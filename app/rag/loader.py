from pathlib import Path

import yaml
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}
MANIFEST_FILENAME = "fuentes.yaml"
EXCLUDED_DIR_PREFIX = "_"


def _cargar_manifiesto(carpeta: Path) -> dict[str, dict]:
    """Lee `fuentes.yaml` de una carpeta (si existe) → {nombre_archivo: metadata}.

    Manifiesto lateral para archivos binarios (PDFs descargados directo)
    donde no es posible embeber front-matter en el propio archivo. Ver
    SPEC_MEJORAS_RAG.md sección 1.4.
    """
    manifiesto_path = carpeta / MANIFEST_FILENAME
    if not manifiesto_path.exists():
        return {}

    with open(manifiesto_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return data.get("archivos", {})


def _extraer_front_matter(texto: str) -> tuple[dict, str]:
    """Separa el bloque YAML de front-matter (si existe) del resto del texto.

    Formato esperado (el que escribe `app/rag/fetch_web_sources.py`):
    ```
    ---
    url: ...
    institucion: ...
    ---
    contenido...
    ```
    Los `.md` normativos existentes (`data/normativa/`) no tienen
    front-matter, así que para ellos esto simplemente devuelve ({}, texto
    sin cambios).
    """
    if not texto.startswith("---"):
        return {}, texto

    partes = texto.split("---", 2)
    if len(partes) < 3:
        return {}, texto

    _, bloque_yaml, resto = partes
    metadata = yaml.safe_load(bloque_yaml) or {}
    return metadata, resto.lstrip("\n")


def load_documents(data_dir: str = "data/normativa", recursive: bool = False) -> list[Document]:
    """Carga documentos normativos soportados desde un directorio.

    Recorre `data_dir` buscando archivos con extensión soportada (.pdf, .txt,
    .md) y los carga usando el loader de LangChain correspondiente a cada
    tipo. A cada documento cargado se le agregan metadatos base (nombre_archivo,
    tipo) que luego viajan hacia los chunks generados por `split_documents`,
    permitiendo trazabilidad de la fuente en las respuestas del agente.

    Si `recursive=True`, también desciende a subcarpetas (necesario para
    `data/normativa_web/<fuente>/`, ver SPEC_MEJORAS_RAG.md sección 1.4).
    Las subcarpetas cuyo nombre empieza con "_" (p. ej. `_pendiente_ocr`) se
    excluyen explícitamente — contienen PDFs sin texto extraíble a propósito
    no indexados. Si una carpeta tiene un `fuentes.yaml` (ver
    `_cargar_manifiesto`), sus entradas enriquecen la metadata de cada
    archivo (`url`, `institucion`, `fecha_captura`, `tipo_fuente`); los
    archivos sin manifiesto conservan el comportamiento actual
    (`tipo_fuente="normativa_pdf"`, sin url/institución/fecha).

    Args:
        data_dir (str): Ruta al directorio que contiene los documentos fuente.
            Por defecto "data/normativa".
        recursive (bool): Si True, recorre subcarpetas (excepto las que
            empiezan con "_"). Por defecto False.

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

    if recursive:
        carpetas = [
            p
            for p in data_path.rglob("*")
            if p.is_dir() and not any(part.startswith(EXCLUDED_DIR_PREFIX) for part in p.relative_to(data_path).parts)
        ]
        carpetas.append(data_path)
    else:
        carpetas = [data_path]

    archivos = [
        f
        for carpeta in carpetas
        for f in carpeta.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not archivos:
        raise ValueError(f"No se encontraron documentos en '{data_dir}'.")

    manifiestos_por_carpeta: dict[Path, dict[str, dict]] = {}
    documentos: list[Document] = []

    for archivo in archivos:
        print(f"  Cargando: {archivo.name}")

        if archivo.suffix.lower() == ".pdf":
            loader = PyPDFLoader(str(archivo))
        else:
            loader = TextLoader(str(archivo), encoding="utf-8")

        docs = loader.load()

        carpeta = archivo.parent
        if carpeta not in manifiestos_por_carpeta:
            manifiestos_por_carpeta[carpeta] = _cargar_manifiesto(carpeta)
        entrada_manifiesto = manifiestos_por_carpeta[carpeta].get(archivo.name)

        front_matter: dict = {}
        if archivo.suffix.lower() == ".md":
            for doc in docs:
                front_matter, doc.page_content = _extraer_front_matter(doc.page_content)

        for doc in docs:
            doc.metadata["nombre_archivo"] = archivo.name
            doc.metadata["tipo"] = archivo.suffix.lower().replace(".", "")
            if "page" in doc.metadata:
                doc.metadata["pagina"] = doc.metadata["page"] + 1

            if entrada_manifiesto:
                doc.metadata["tipo_fuente"] = "web_oficial"
                for campo in ("url", "institucion", "fecha_captura", "categoria", "descripcion"):
                    if entrada_manifiesto.get(campo):
                        doc.metadata[campo] = entrada_manifiesto[campo]
            elif front_matter:
                doc.metadata["tipo_fuente"] = front_matter.get("tipo_fuente", "web_oficial")
                for campo in ("url", "institucion", "fecha_captura", "categoria", "descripcion"):
                    if front_matter.get(campo):
                        doc.metadata[campo] = front_matter[campo]
            else:
                doc.metadata["tipo_fuente"] = "normativa_pdf"

        documentos.extend(docs)

    print(f"  Total documentos cargados: {len(documentos)} páginas/secciones")
    return documentos
