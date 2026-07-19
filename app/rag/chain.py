from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from app.llm import get_llm
from app.rag.vectorstore import load_vectorstore
from app.prompts.system_prompt import SYSTEM_PROMPT
from app.schemas import RespuestaMYPE

# k y temperature estándar de la cadena de producción: k=4 da suficiente
# cobertura de contexto sin diluir la ventana del prompt, y temperature=0
# prioriza determinismo sobre contenido normativo (ver SPEC.md, Bloque 1).
RETRIEVAL_K = 6
LLM_TEMPERATURE = 0


def format_docs(docs) -> str:
    """Formatea los chunks recuperados como texto de contexto para el LLM.

    Cada chunk se antecede de su fuente y número de artículo/chunk, para
    que el modelo pueda citar de dónde proviene la información si lo
    considera relevante en su respuesta.

    Args:
        docs (list[Document]): Chunks recuperados por el retriever.

    Returns:
        str: Texto consolidado, listo para inyectarse en el prompt.
    """
    bloques = []
    for doc in docs:
        fuente = doc.metadata.get("nombre_archivo", "fuente desconocida")
        pagina = doc.metadata.get("pagina")
        chunk_index = doc.metadata.get("chunk_index")

        encabezado = f"[Fuente: {fuente}"
        if pagina is not None:
            encabezado += f" | pág. {pagina}"
        if chunk_index is not None:
            encabezado += f" | chunk {chunk_index}"
        encabezado += "]"

        bloques.append(f"{encabezado}\n{doc.page_content}")
    return "\n\n---\n\n".join(bloques)


def _build_output_parser() -> JsonOutputParser:
    return JsonOutputParser(pydantic_object=RespuestaMYPE)


def _build_prompt(parser: JsonOutputParser) -> ChatPromptTemplate:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("historial", optional=True),
            (
                "human",
                """Usa el siguiente CONTEXTO extraído de normativa oficial \
sobre formalización de empresas en Perú.

ANTES de responder, evalúa internamente:
1. ¿La PREGUNTA pertenece al dominio de formalización MYPE? Si no, marca \
fuera_de_dominio=true y responde con la redirección amable indicada en tus reglas.
2. Si sí pertenece al dominio: ¿el CONTEXTO contiene información directamente \
relevante a la PREGUNTA?
3. Si el CONTEXTO es relevante: fundamenta tu respuesta ÚNICAMENTE en ese contexto \
y marca fundamentado_en_contexto=true.
4. Si el CONTEXTO no es relevante o es parcial: indícalo explícitamente en tu \
respuesta. Di qué parte sí puedes responder con el contexto disponible y qué \
parte excede lo que tienes documentado actualmente. NO rellenes los huecos con \
conocimiento general no verificado. Marca fundamentado_en_contexto=false.
5. Si tu respuesta es solo una interacción social (saludo, agradecimiento, \
presentarte) sin contenido normativo, marca fundamentado_en_contexto=false \
aunque fuera_de_dominio sea false.

CONTEXTO:
{contexto}

PREGUNTA:
{pregunta}

Responde ÚNICAMENTE con un objeto JSON válido, sin texto antes ni después, \
sin encabezados ni bloques de markdown (nada de ```). Nada fuera de las llaves \
del JSON.

{format_instructions}""",
            ),
        ]
    )
    return prompt.partial(format_instructions=parser.get_format_instructions())


def _build_retriever():
    return load_vectorstore().as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": RETRIEVAL_K,
            "fetch_k": 20,
            "lambda_mult": 0.5,
        },
    )


def build_condensador():
    """Reescribe una pregunta de seguimiento en una pregunta autocontenida.

    El retriever busca solo con el texto literal de la pregunta actual — no
    ve el `historial`. Sin este paso, un turno de seguimiento como
    "explícame más sobre eso" no trae ningún chunk relevante (el texto no
    tiene palabras clave del tema real), y la cadena de grounding termina
    respondiendo "no tengo información" aunque el corpus sí la tenga (como
    se vio en pruebas reales de conversación). Se usa solo para armar la
    consulta al vectorstore; la pregunta original (sin condensar) sigue
    siendo la que ve el usuario y la que recibe la cadena de respuesta.
    """
    llm = get_llm(LLM_TEMPERATURE)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Reformula la ÚLTIMA pregunta del usuario como una pregunta "
                "autocontenida y completa, resolviendo cualquier referencia al "
                'HISTORIAL de la conversación (pronombres, "eso", "ese '
                'régimen", etc.). No respondas la pregunta ni agregues '
                "información nueva, solo reformúlala. Si ya es autocontenida, "
                "devuélvela igual. Responde ÚNICAMENTE con la pregunta "
                "reformulada, sin comillas ni texto adicional.",
            ),
            MessagesPlaceholder("historial"),
            ("human", "{pregunta}"),
        ]
    )
    return prompt | llm | StrOutputParser()


def extract_sources(docs) -> list[dict]:
    return [
        {
            "archivo": doc.metadata.get("nombre_archivo", "fuente desconocida"),
            "pagina": doc.metadata.get("pagina"),
            "chunk": doc.metadata.get("chunk_index"),
        }
        for doc in docs
    ]


def _finalize(data: dict) -> dict:
    """Combina la salida estructurada del LLM con las fuentes derivadas del retriever.

    Las fuentes no se le piden al LLM (evitaría que "recuerde mal" o invente
    una cita): se derivan de los metadatos de los chunks efectivamente
    recuperados. Si la pregunta está fuera de dominio, no se exponen fuentes
    normativas, ya que no aplican a la respuesta.
    """
    structured = data["structured"]
    fuera_de_dominio = structured.get("fuera_de_dominio", False)
    fundamentado = structured.get("fundamentado_en_contexto", False)

    return {
        "pregunta": data["pregunta"],
        "respuesta": structured.get("respuesta", ""),
        "fuera_de_dominio": fuera_de_dominio,
        "fuentes": (
            extract_sources(data["docs"])
            if (not fuera_de_dominio and fundamentado)
            else []
        ),
    }


def build_respuesta_components():
    """Construye el retriever y la cadena prompt|LLM|parser ya ensamblados.

    Es el bloque reusable tanto por `build_rag_chain` (una pregunta aislada,
    sin memoria) como por `Chatbot` (Bloque 7: memoria de sesión vía
    `MessagesPlaceholder("historial")`) — ambos consumen el mismo prompt con
    guardrail e instrucciones de grounding, sin duplicar su construcción.

    La cadena de respuesta espera como entrada un dict con "docs" (chunks
    recuperados), "pregunta" (str) y opcionalmente "historial" (lista de
    mensajes previos de la sesión).
    """
    retriever = _build_retriever()
    llm = get_llm(LLM_TEMPERATURE)
    parser = _build_output_parser()
    prompt = _build_prompt(parser)

    respuesta_chain = (
        {
            "contexto": lambda data: format_docs(data["docs"]),
            "pregunta": lambda data: data["pregunta"],
            "historial": lambda data: data.get("historial", []),
        }
        | prompt
        | llm
        | parser
    )

    return retriever, respuesta_chain


def build_rag_chain():
    """Ensambla la cadena RAG completa: retriever + prompt + LLM + fuentes.

    Conecta el vectorstore persistido con el LLM configurado, usando el
    SYSTEM_PROMPT como instrucciones de dominio y guardrail. El contexto
    recuperado se inyecta explícitamente, indicándole al modelo que debe
    fundamentar su respuesta en él y admitir cuando no encuentra la
    información en lugar de inventarla.

    La cadena es la única fuente de verdad para responder preguntas: recibe
    la pregunta como string y devuelve directamente el dict final
    (pregunta, respuesta, fuera_de_dominio, fuentes) — no hay una
    construcción manual paralela del mismo resultado en otra función.
    Es una cadena sin memoria (sin "historial"); para conversación con
    memoria de sesión usar `app.chatbot.Chatbot`.

    Returns:
        Runnable: Cadena LangChain lista para invocarse con `.invoke(pregunta)`.
    """
    retriever, respuesta_chain = build_respuesta_components()

    chain = (
        {"pregunta": RunnablePassthrough(), "docs": retriever}
        | RunnablePassthrough.assign(structured=respuesta_chain)
        | RunnableLambda(_finalize)
    )

    return chain


def answer_question(question: str) -> dict:
    """Responde una pregunta usando la cadena RAG completa (`build_rag_chain`)."""
    return build_rag_chain().invoke(question)
