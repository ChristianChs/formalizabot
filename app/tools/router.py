import re

from openai import BadRequestError

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm import get_llm
from app.rag.chain import LLM_TEMPERATURE
from app.tools.derivar_humano import derivar_a_humano
from app.tools.nrus import calcular_categoria_nrus

TOOLS = [calcular_categoria_nrus, derivar_a_humano]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}

SISTEMA_ROUTER = (
    "Decides si el mensaje del usuario requiere invocar una tool "
    "determinista. Llama una tool ÚNICAMENTE si el mensaje contiene, de "
    "forma EXPLÍCITA, todos los datos que esa tool necesita (por ejemplo, "
    "un monto de ingresos en soles ya mencionado por el usuario para "
    "calcular_categoria_nrus, o un pedido explícito de hablar con una "
    "persona para derivar_a_humano). Si falta un dato requerido, o el "
    "usuario no lo pidió explícitamente, NO llames ninguna tool — nunca "
    "inventes ni asumas un valor de argumento."
)


def _build_router_llm():
    # LLM separado del de la cadena RAG de grounding (Bloque 1-3): ese debe
    # seguir siendo determinista solo para responder con fundamento en el
    # CONTEXTO recuperado. Este es el LLM de la "cadena de chat" (Bloque 9),
    # cuya única decisión es SI corresponde invocar una tool y con qué
    # argumentos — el resultado en sí lo calcula la tool, no el LLM (RF8).
    return get_llm(LLM_TEMPERATURE).bind_tools(TOOLS)


def _numero_mencionado(pregunta: str, valor: float) -> bool:
    """Verifica que un número que el LLM pasó como argumento aparezca
    realmente en el texto del usuario (tolerando separadores de miles/decimales).
    """
    for match in re.findall(r"\d+(?:[.,]\d+)*", pregunta):
        normalizado = match.replace(",", "").replace(".", "")
        try:
            if float(normalizado) == valor:
                return True
        except ValueError:
            continue
    return False


def _llamada_valida(pregunta: str, nombre: str, args: dict) -> bool:
    """Descarta tool calls con argumentos que el LLM pudo haber inventado.

    Se detectó en pruebas reales que el modelo 8B, ante una pregunta sin
    montos (ej. "quiero crear una empresa de software"), igual llamaba a
    `calcular_categoria_nrus` inventando un ingreso (ej. 100000) para poder
    completar la llamada. Esta validación es la defensa determinista: si el
    argumento numérico no aparece en el texto original del usuario, la
    llamada se descarta y el flujo cae de vuelta al RAG normal.
    """
    if nombre == "calcular_categoria_nrus":
        ingresos = args.get("ingresos_mensuales")
        if ingresos is None:
            return False
        try:
            return _numero_mencionado(pregunta, float(ingresos))
        except (TypeError, ValueError):
            return False
    return True


def resolver_tool_call(pregunta: str) -> str | None:
    """Ejecuta una tool determinista si la pregunta la activa; si no, None.

    Cuando el LLM decide llamar una o más tools, esta función valida cada
    llamada contra el texto original (ver `_llamada_valida`) y ejecuta
    manualmente las que pasan esa validación — nunca deja que el LLM
    "invente" el resultado. Si ninguna tool call es válida, el flujo normal
    de RAG (retriever + grounding) continúa sin cambios.
    """
    llm = _build_router_llm()
    try:
        respuesta = llm.invoke(
            [SystemMessage(content=SISTEMA_ROUTER), HumanMessage(content=pregunta)]
        )
    except BadRequestError:
        # El modelo (8B) a veces intenta llamar una tool y genera un
        # payload de argumentos mal formado incluso cuando ninguna tool
        # aplica. Ante eso, se trata como "no hay tool call" en vez de
        # tumbar la conversación: el flujo normal de RAG sigue intacto.
        return None

    if not respuesta.tool_calls:
        return None

    resultados = []
    for llamada in respuesta.tool_calls:
        tool_fn = TOOLS_BY_NAME.get(llamada["name"])
        if tool_fn is None:
            continue
        if not _llamada_valida(pregunta, llamada["name"], llamada["args"]):
            continue
        resultados.append(tool_fn.invoke(llamada["args"]))

    return "\n".join(resultados) if resultados else None
