from langchain_core.chat_history import InMemoryChatMessageHistory

from app.rag.chain import build_condensador, build_respuesta_components, extract_sources
from app.tools.router import resolver_tool_call


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
    """

    def __init__(self):
        self._retriever, self._respuesta_chain = build_respuesta_components()
        self._condensador = build_condensador()
        self._sesiones: dict[str, InMemoryChatMessageHistory] = {}

    def _historial(self, session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in self._sesiones:
            self._sesiones[session_id] = InMemoryChatMessageHistory()
        return self._sesiones[session_id]

    def stream(self, pregunta: str, session_id: str = "default"):
        """Emite el resultado progresivamente (RF5) y actualiza la memoria.

        Cada valor emitido es un dict con "respuesta" (creciente conforme
        llegan tokens), "fuera_de_dominio" y "fuentes". Las fuentes solo
        vienen completas en el último valor emitido, una vez que la
        respuesta del LLM terminó de generarse y se sabe si aplican.
        """
        historial = self._historial(session_id)

        resultado_tool = resolver_tool_call(pregunta)
        if resultado_tool is not None:
            historial.add_user_message(pregunta)
            historial.add_ai_message(resultado_tool)
            yield {"respuesta": resultado_tool, "fuera_de_dominio": False, "fuentes": []}
            return

        pregunta_busqueda = pregunta
        if historial.messages:
            pregunta_busqueda = self._condensador.invoke(
                {"pregunta": pregunta, "historial": historial.messages}
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
            "historial": historial.messages,
        }

        estructurado = {}
        for parcial in self._respuesta_chain.stream(entrada):
            estructurado = parcial
            yield {
                "respuesta": estructurado.get("respuesta", ""),
                "fuera_de_dominio": estructurado.get("fuera_de_dominio", False),
                "fuentes": [],
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
        }

    def invoke(self, pregunta: str, session_id: str = "default") -> dict:
        resultado = {}
        for resultado in self.stream(pregunta, session_id):
            pass
        return {"pregunta": pregunta, **resultado}
