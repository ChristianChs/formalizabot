from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.llm import get_llm
from app.rag.vectorstore import load_vectorstore
from app.prompts.system_prompt import SYSTEM_PROMPT


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
        bloques.append(f"[Fuente: {fuente}]\n{doc.page_content}")
    return "\n\n---\n\n".join(bloques)


def build_rag_chain():
    """Ensambla la cadena RAG: retriever + prompt + LLM.

    Conecta el vectorstore persistido con el LLM configurado, usando el
    SYSTEM_PROMPT como instrucciones de dominio y guardrail. El contexto
    recuperado se inyecta explícitamente, indicándole al modelo que debe
    fundamentar su respuesta en él y admitir cuando no encuentra la
    información en lugar de inventarla.

    Returns:
        Runnable: Cadena LangChain lista para invocarse con `.invoke(pregunta)`.
    """
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                """Usa el siguiente CONTEXTO extraído de normativa oficial \
        para responder la pregunta. Si el contexto no contiene información \
        suficiente para responder con certeza, dilo explícitamente en vez de \
        inventar datos.

        CONTEXTO:
        {contexto}

        PREGUNTA:
        {pregunta}""",
            ),
        ]
    )

    chain = (
        {"contexto": retriever | format_docs, "pregunta": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain
