from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


def load_documents(data_dir: str = "data/normativa") -> list[Document]:
    """Carga documentos normativos soportados desde un directorio.

    Recorre `data_dir` buscando archivos con extensión soportada (.pdf, .txt,
    .md) y los carga usando el loader de LangChain correspondiente a cada
    tipo. A cada documento cargado se le agregan metadatos base (nombre_archivo,
    tipo) que luego viajan hacia los chunks generados por `split_documents`,
    permitiendo trazabilidad de la fuente en las respuestas del agente.

    Args:
        data_dir (str): Ruta al directorio que contiene los documentos fuente.
            Por defecto "data/normativa".

    Raises:
        FileNotFoundError: Si `data_dir` no existe.
        ValueError: Si `data_dir` existe pero no contiene archivos con una
            extensión soportada.

    Returns:
        list[Document]: Documentos cargados, cada uno con metadata base
            (nombre_archivo, tipo) lista para ser enriquecida en el splitting.
    """
    data_path = Path(data_dir)

    if not data_path.exists():
        raise FileNotFoundError(f"El directorio '{data_dir}' no existe.")

    archivos = [
        f
        for f in data_path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not archivos:
        raise ValueError(f"No se encontraron documentos en '{data_dir}'.")

    documentos: list[Document] = []

    for archivo in archivos:
        print(f"  Cargando: {archivo.name}")

        if archivo.suffix.lower() == ".pdf":
            loader = PyPDFLoader(str(archivo))
        else:
            loader = TextLoader(str(archivo), encoding="utf-8")

        docs = loader.load()

        for doc in docs:
            doc.metadata["nombre_archivo"] = archivo.name
            doc.metadata["tipo"] = archivo.suffix.lower().replace(".", "")
            if "page" in doc.metadata:
                doc.metadata["pagina"] = doc.metadata["page"] + 1

        documentos.extend(docs)

    print(f"  Total documentos cargados: {len(documentos)} páginas/secciones")
    return documentos
