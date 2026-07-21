from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

# Módulo separado de loader.py a propósito: ese solo lee disco, este agrega
# una dependencia de red (ver SPEC_MEJORAS_RAG.md sección 1.1). No se usa
# directo desde build_index.py — solo desde fetch_web_sources.py, que
# guarda un snapshot local versionado (sección 1.2); el bot nunca depende
# de que la web de origen esté arriba en el momento de responder.

REQUEST_TIMEOUT_SEGUNDOS = 15
USER_AGENT = (
    "FormalizaBot-MYPE/1.0 (fetch de fuentes oficiales para RAG academico)"
)

# Etiquetas y palabras clave de navegación/footers/banners de cookies que
# ensucian el chunking si quedan en el texto indexado.
TAGS_A_ELIMINAR = ["script", "style", "nav", "footer", "header", "aside", "noscript"]
PALABRAS_CLAVE_RUIDO = (
    "cookie",
    "menu",
    "nav",
    "footer",
    "header",
    "banner",
    "breadcrumb",
    "compartir",
    "share",
    "sidebar",
    "skip-link",
    "sr-only",
)


@dataclass
class PaginaWeb:
    url: str
    titulo: str
    contenido: str


def _es_ruido(tag) -> bool:
    if tag.attrs is None:
        # Ya fue eliminado como hijo de un tag de ruido anterior en este
        # mismo recorrido (decompose() marca a los hijos como decompuestos).
        return False
    atributos = " ".join(tag.get("class", []) + [tag.get("id") or ""]).lower()
    return any(palabra in atributos for palabra in PALABRAS_CLAVE_RUIDO)


def fetch_pagina(url: str) -> PaginaWeb:
    """Descarga una página web y extrae su contenido útil.

    Elimina scripts/estilos y navegación/footers/banners de cookies antes de
    extraer el texto, para no ensuciar el chunking con boilerplate que no
    aporta al contenido normativo real (ver SPEC_MEJORAS_RAG.md sección 1.1).

    Args:
        url (str): URL de la página a descargar.

    Raises:
        requests.RequestException: Si la descarga falla (red, timeout, HTTP).

    Returns:
        PaginaWeb: título y contenido de texto limpio de la página.
    """
    respuesta = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT_SEGUNDOS,
    )
    respuesta.raise_for_status()

    soup = BeautifulSoup(respuesta.text, "html.parser")

    titulo = soup.title.get_text(strip=True) if soup.title else url

    # Se localiza el contenedor principal ANTES de limpiar: si se limpia
    # sobre todo `soup`, decompose() sobre un ancestro de <main> (p. ej. un
    # wrapper con clase "js-sharect" que matchea la palabra clave "share")
    # se lleva puesto el contenido real, aunque <main> en sí nunca se haya
    # tocado directamente (queda huérfano, desconectado del árbol).
    contenedor = soup.find("main") or soup.find(attrs={"role": "main"}) or soup.body or soup

    for tag_name in TAGS_A_ELIMINAR:
        for tag in contenedor.find_all(tag_name):
            tag.decompose()

    for tag in contenedor.find_all(True):
        if _es_ruido(tag):
            tag.decompose()

    texto = contenedor.get_text(separator="\n")
    lineas = [linea.strip() for linea in texto.splitlines() if linea.strip()]
    contenido = "\n".join(lineas)

    return PaginaWeb(url=url, titulo=titulo, contenido=contenido)
