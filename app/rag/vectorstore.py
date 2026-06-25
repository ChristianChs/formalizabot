from pathlib import Path
from langchain_chroma import Chroma
from langchain_core.documents import Document
from app.rag.embeddings import get_embeddings

PERSIST_DIR = "data/chroma_db"


def build_vectorstore(chunks: list[Document]) -> Chroma:
    """Construye y persiste el vectorstore a partir de los chunks dados.

    Crea el índice desde cero en `PERSIST_DIR`. Si ya existía un índice
    previo en esa ruta, este método lo sobreescribe — es la operación
    a usar cuando se re-indexa todo el corpus completo.

    Args:
        chunks (list[Document]): Chunks generados por `split_documents`,
            ya con sus metadatos (nombre_archivo, tipo, chunk_index).

    Returns:
        Chroma: Vectorstore listo para hacer búsquedas de similitud.
    """
    embeddings = get_embeddings()

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
    )

    print(f"  Vectorstore creado/actualizado en: {PERSIST_DIR}")
    print(f"  Total chunks indexados: {len(chunks)}")
    return vectorstore


def load_vectorstore() -> Chroma:
    """Carga un vectorstore previamente persistido en disco.

    Usar esta función (en vez de `build_vectorstore`) cuando el índice ya
    fue construido antes y solo se necesita consultarlo — por ejemplo,
    al ejecutar el agente en producción, sin re-indexar el corpus en
    cada arranque.

    Raises:
        FileNotFoundError: Si `PERSIST_DIR` no existe, lo cual indica que
            el índice nunca fue construido.

    Returns:
        Chroma: Vectorstore listo para hacer búsquedas de similitud.
    """
    if not Path(PERSIST_DIR).exists():
        raise FileNotFoundError(
            f"No existe un índice en '{PERSIST_DIR}'. "
            "Ejecuta primero el script de indexación (build_index.py)."
        )

    embeddings = get_embeddings()

    return Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings,
    )
