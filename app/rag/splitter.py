import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Encabezado típico de unidad normativa: "Artículo 5°.-", "Artículo 12.-",
# "Art. 3°-". El lookahead conserva el separador como inicio del siguiente
# fragmento (re.split normal lo descartaría).
ARTICULO_REGEX = re.compile(r"(?=Art[íi]culo\s+\d+°?[\.\-])", re.IGNORECASE)
ARTICULO_NUMERO_REGEX = re.compile(r"Art[íi]culo\s+(\d+)", re.IGNORECASE)

# Config de chunking por defecto (PDFs normativos, prosa densa) vs. páginas
# web fetched por app/rag/fetch_web_sources.py (contenido más fragmentado:
# listas, pasos, tablas de requisitos) — ver SPEC_MEJORAS_RAG.md sección 2.2.
# Se distingue por (tipo == "md" y tipo_fuente == "web_oficial") en vez de
# solo tipo_fuente, porque los PDFs de legislación descargados directo de
# la Muni Tacna también llevan tipo_fuente="web_oficial" (vienen de
# fuentes.yaml) pero son prosa legal densa igual que la normativa PDF
# existente, no contenido fragmentado de página web.
CHUNK_CONFIG_DEFAULT = {"chunk_size": 1200, "chunk_overlap": 250}
CHUNK_CONFIG_WEB_HTML = {"chunk_size": 600, "chunk_overlap": 100}


def _es_pagina_web_fetched(doc: Document) -> bool:
    return doc.metadata.get("tipo") == "md" and doc.metadata.get("tipo_fuente") == "web_oficial"


def _dividir_por_articulos(doc: Document) -> list[Document]:
    """Pre-divide un documento por encabezados de artículo, antes del splitter
    de caracteres (SPEC_MEJORAS_RAG.md sección 2.1).

    Si el texto no tiene encabezados de artículo detectables (la mayoría de
    PDFs de trámites/formularios, y todo el contenido web), devuelve el
    documento sin tocar — de modo que solo afecta a texto legal real, y el
    `RecursiveCharacterTextSplitter` posterior sigue siendo quien sub-divide
    cualquier artículo más largo que `chunk_size`.
    """
    texto = doc.page_content
    limites = [m.start() for m in ARTICULO_REGEX.finditer(texto)]

    if not limites:
        return [doc]

    fragmentos = []
    if limites[0] > 0:
        preambulo = texto[: limites[0]].strip()
        if preambulo:
            fragmentos.append(Document(page_content=preambulo, metadata=dict(doc.metadata)))

    limites.append(len(texto))
    for inicio, fin in zip(limites[:-1], limites[1:]):
        fragmento = texto[inicio:fin].strip()
        if not fragmento:
            continue
        metadata = dict(doc.metadata)
        match_numero = ARTICULO_NUMERO_REGEX.match(fragmento)
        if match_numero:
            metadata["articulo_numero"] = match_numero.group(1)
        fragmentos.append(Document(page_content=fragmento, metadata=metadata))

    return fragmentos


def split_documents(documentos: list[Document]) -> list[Document]:
    """Divide documentos normativos en chunks aptos para retrieval semántico.

    Dos pasos antes de indexar:
    1. `_dividir_por_articulos`: en texto legal con encabezados "Artículo N°",
       separa cada artículo como unidad propia (metadata `articulo_numero`)
       para que el `RecursiveCharacterTextSplitter` nunca mezcle dos
       artículos distintos en un mismo chunk. Sin encabezados detectables,
       el documento pasa intacto a este splitter.
    2. `RecursiveCharacterTextSplitter`, con `chunk_size`/`chunk_overlap`
       distintos según el origen del contenido (`CHUNK_CONFIG_DEFAULT` para
       PDFs/prosa densa, `CHUNK_CONFIG_WEB_HTML` para páginas web fetched,
       más fragmentadas) — prioriza cortar por párrafos/oraciones antes de
       cortar a la fuerza por caracteres.

    Cada chunk resultante conserva los metadatos del documento de origen
    (nombre_archivo, tipo, tipo_fuente, articulo_numero si aplica) y recibe
    un nuevo metadato `chunk_index` que indica su posición secuencial dentro
    de ese documento.

    Args:
        documentos (list[Document]): Documentos crudos cargados por
            `load_documents`, ya con sus metadatos base (nombre_archivo, tipo).

    Returns:
        list[Document]: Lista de chunks, cada uno con metadata extendida
            lista para ser indexada en el vectorstore.
    """
    unidades: list[Document] = []
    for doc in documentos:
        unidades.extend(_dividir_por_articulos(doc))

    grupos: dict[tuple[int, int], list[Document]] = {}
    for doc in unidades:
        config = CHUNK_CONFIG_WEB_HTML if _es_pagina_web_fetched(doc) else CHUNK_CONFIG_DEFAULT
        clave = (config["chunk_size"], config["chunk_overlap"])
        grupos.setdefault(clave, []).append(doc)

    chunks: list[Document] = []
    for (chunk_size, chunk_overlap), docs_grupo in grupos.items():
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks.extend(splitter.split_documents(docs_grupo))

    # Propagar metadatos + agregar índice del chunk dentro de su documento fuente
    fuente_conteo: dict[str, int] = {}

    for chunk in chunks:
        nombre = chunk.metadata.get("nombre_archivo", "desconocido")
        fuente_conteo[nombre] = fuente_conteo.get(nombre, 0) + 1
        chunk.metadata["chunk_index"] = fuente_conteo[nombre]

    print(f"  Total chunks generados: {len(chunks)}")
    return chunks
