from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(documentos: list[Document]) -> list[Document]:
    """Divide documentos normativos en chunks aptos para retrieval semántico.

    Utiliza RecursiveCharacterTextSplitter, que prioriza cortar por párrafos
    y oraciones antes de cortar a la fuerza por caracteres — esto preserva
    mejor la estructura de artículos e incisos típica de textos legales.

    Cada chunk resultante conserva los metadatos del documento de origen
    (nombre_archivo, tipo) y recibe un nuevo metadato `chunk_index` que
    indica su posición secuencial dentro de ese documento.

    Args:
        documentos (list[Document]): Documentos crudos cargados por
            `load_documents`, ya con sus metadatos base (nombre_archivo, tipo).

    Returns:
        list[Document]: Lista de chunks, cada uno con metadata extendida
            (nombre_archivo, tipo, chunk_index) lista para ser indexada
            en el vectorstore.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documentos)

    # Propagar metadatos + agregar índice del chunk dentro de su documento fuente
    fuente_conteo: dict[str, int] = {}

    for chunk in chunks:
        nombre = chunk.metadata.get("nombre_archivo", "desconocido")
        fuente_conteo[nombre] = fuente_conteo.get(nombre, 0) + 1
        chunk.metadata["chunk_index"] = fuente_conteo[nombre]

    print(f"  Total chunks generados: {len(chunks)}")
    return chunks
