import time

from langchain_core.chat_history import InMemoryChatMessageHistory

from app.rag.chain import build_condensador, build_respuesta_components, extract_sources
from app.tools.router import resolver_tool_call

SESION_TTL_SEGUNDOS = 24 * 60 * 60
# Turnos (par usuario+bot) más recientes que se inyectan como "historial" en
# el condensador y en la cadena de respuesta. Sin este tope, el historial de
# una sesión de 24h crece sin límite y termina empujando el prompt (ya
# ajustado al límite de 6000 TPM de Groq, ver app/rag/chain.py) por encima
# de la cuota, devolviendo 413 "Request too large".
HISTORIAL_MAX_TURNOS = 3


class Chatbot:
    """Conversación con memoria de sesión sobre la cadena RAG (RF4).

    A diferencia de `answer_question` (una pregunta aislada por llamada),
    esta clase guarda el historial de turnos por `session_id` y lo inyecta
    en el prompt vía `MessagesPlaceholder("historial")`, para que el modelo
    resuelva referencias como "¿y para ese régimen?" sin que el usuario
    repita contexto. El retriever y la cadena prompt|LLM|parser se
    construyen una sola vez (en `__init__`), no por turno.

    Antes de recurrir al RAG, cada turno pasa por `resolver_tool_call`
    (Bloque 9): si la pregunta activa una tool determinista (ej. calcular
    categoría NRUS), se responde directamente con el resultado de la tool,
    sin generación del LLM de grounding.

    El historial por sesión expira a las `SESION_TTL_SEGUNDOS` (24h) de
    inactividad: si el turno siguiente llega después de ese plazo, se
    descarta la memoria vieja y arranca una sesión nueva en vez de crecer
    indefinidamente en RAM.
    """

    def __init__(self):
        self._retriever, self._respuesta_chain = build_respuesta_components()
        self._condensador = build_condensador()
        self._sesiones: dict[str, InMemoryChatMessageHistory] = {}
        self._ultima_actividad: dict[str, float] = {}

    def _historial(self, session_id: str) -> tuple[InMemoryChatMessageHistory, bool]:
        """Devuelve el historial de la sesión y si se acaba de crear (primer
        mensaje o TTL vencido), para que el caller pueda informar al usuario
        que arrancó una sesión nueva sin tener que rastrear el TTL por su
        cuenta.
        """
        ahora = time.monotonic()
        vencida = (
            session_id in self._ultima_actividad
            and ahora - self._ultima_actividad[session_id] > SESION_TTL_SEGUNDOS
        )
        es_nueva = session_id not in self._sesiones or vencida
        if es_nueva:
            self._sesiones[session_id] = InMemoryChatMessageHistory()
        self._ultima_actividad[session_id] = ahora
        return self._sesiones[session_id], es_nueva

    @staticmethod
    def _historial_acotado(historial: InMemoryChatMessageHistory) -> list:
        """Últimos HISTORIAL_MAX_TURNOS turnos (usuario+bot) del historial completo."""
        return historial.messages[-(HISTORIAL_MAX_TURNOS * 2):]

    def stream(self, pregunta: str, session_id: str = "default"):
        """Emite el resultado progresivamente (RF5) y actualiza la memoria.

        Cada valor emitido es un dict con "respuesta" (creciente conforme
        llegan tokens), "fuera_de_dominio", "fuentes" y "sesion_nueva" (True
        si este turno arrancó una sesión desde cero, ya sea porque era el
        primer mensaje de ese `session_id` o porque el TTL de 24h venció).
        Las fuentes solo vienen completas en el último valor emitido, una
        vez que la respuesta del LLM terminó de generarse y se sabe si
        aplican.
        """
        historial, sesion_nueva = self._historial(session_id)

        resultado_tool = resolver_tool_call(pregunta)
        if resultado_tool is not None:
            historial.add_user_message(pregunta)
            historial.add_ai_message(resultado_tool)
            yield {
                "respuesta": resultado_tool,
                "fuera_de_dominio": False,
                "fuentes": [],
                "sesion_nueva": sesion_nueva,
            }
            return

        historial_acotado = self._historial_acotado(historial)

        pregunta_busqueda = pregunta
        if historial_acotado:
            pregunta_busqueda = self._condensador.invoke(
                {"pregunta": pregunta, "historial": historial_acotado}
            )

        docs = self._retriever.invoke(pregunta_busqueda)
        # Se usa la pregunta condensada (autocontenida) también para la
        # generación, no solo para el retriever: si se le pasara la
        # pregunta literal ("explícame más sobre eso"), el paso de
        # evaluación de relevancia CONTEXTO-PREGUNTA del prompt la ve
        # ambigua y descarta un CONTEXTO que en realidad sí aplica.
        entrada = {
            "pregunta": pregunta_busqueda,
            "docs": docs,
            "historial": historial_acotado,
        }

        estructurado = {}
        for parcial in self._respuesta_chain.stream(entrada):
            estructurado = parcial
            yield {
                "respuesta": estructurado.get("respuesta", ""),
                "fuera_de_dominio": estructurado.get("fuera_de_dominio", False),
                "fuentes": [],
                "sesion_nueva": sesion_nueva,
            }

        fuera_de_dominio = estructurado.get("fuera_de_dominio", False)
        fundamentado = estructurado.get("fundamentado_en_contexto", False)
        respuesta = estructurado.get("respuesta", "")

        historial.add_user_message(pregunta)
        historial.add_ai_message(respuesta)

        yield {
            "respuesta": respuesta,
            "fuera_de_dominio": fuera_de_dominio,
            "fuentes": (
                extract_sources(docs) if (not fuera_de_dominio and fundamentado) else []
            ),
            "sesion_nueva": sesion_nueva,
        }

    def invoke(self, pregunta: str, session_id: str = "default") -> dict:
        resultado = {}
        for resultado in self.stream(pregunta, session_id):
            pass
        return {"pregunta": pregunta, **resultado}
