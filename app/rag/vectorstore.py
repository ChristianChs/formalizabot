import shutil
from functools import lru_cache
from pathlib import Path
from langchain_chroma import Chroma
from langchain_core.documents import Document
from app.rag.embeddings import get_embeddings

PERSIST_DIR = "data/chroma_db"


def build_vectorstore(chunks: list[Document]) -> Chroma:
    """Construye y persiste el vectorstore a partir de los chunks dados.

    Crea el índice desde cero en `PERSIST_DIR`. Si ya existía un índice
    previo en esa ruta, se borra por completo antes de reconstruirlo —
    `Chroma.from_documents()` sobre un `persist_directory` existente
    AGREGA a la colección en vez de reemplazarla, lo que hacía que cada
    re-indexación fuera acumulativa (se detectaron ~11,500 chunks
    persistidos para un corpus que solo genera ~2,800: cada re-indexación
    duplicaba los documentos ya existentes, degradando la calidad del
    retriever porque los duplicados competían con los chunks relevantes
    en la búsqueda de similitud). Este método sí sobreescribe, tal como
    indica esta descripción — es la operación a usar cuando se re-indexa
    todo el corpus completo.

    Args:
        chunks (list[Document]): Chunks generados por `split_documents`,
            ya con sus metadatos (nombre_archivo, tipo, chunk_index).

    Returns:
        Chroma: Vectorstore listo para hacer búsquedas de similitud.
    """
    if Path(PERSIST_DIR).exists():
        shutil.rmtree(PERSIST_DIR)

    embeddings = get_embeddings()

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
    )

    print(f"  Vectorstore creado/actualizado en: {PERSIST_DIR}")
    print(f"  Total chunks indexados: {len(chunks)}")
    return vectorstore


@lru_cache(maxsize=1)
def load_vectorstore() -> Chroma:
    """Carga un vectorstore previamente persistido en disco.

    Usar esta función (en vez de `build_vectorstore`) cuando el índice ya
    fue construido antes y solo se necesita consultarlo — por ejemplo,
    al ejecutar el agente en producción, sin re-indexar el corpus en
    cada arranque.

    Cacheada con `lru_cache`: sin esto, cada pregunta al agente reabriría
    la conexión a Chroma y recargaría el modelo de embeddings desde cero.

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
