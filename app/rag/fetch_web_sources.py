import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml

from app.rag.web_loader import fetch_pagina

FUENTES_YAML = Path("data/fuentes_web.yaml")
OUTPUT_DIR = Path("data/normativa_web")


def _slug(url: str) -> str:
    """Deriva un nombre de archivo estable a partir del path de la URL.

    p. ej. https://www.gob.pe/269-registrar-o-constituir-una-empresa
    -> "269-registrar-o-constituir-una-empresa".
    """
    path = urlparse(url).path.strip("/")
    ultimo_segmento = path.rsplit("/", 1)[-1] if path else url
    slug = re.sub(r"[^a-zA-Z0-9\-]+", "-", ultimo_segmento).strip("-").lower()
    return slug or "pagina"


def _guardar_snapshot(url: str, institucion: str, categoria: str, descripcion: str) -> Path:
    """Descarga una URL y guarda su snapshot en Markdown con front-matter.

    El front-matter (bloque YAML entre `---`) es lo que `load_documents()`
    (`app/rag/loader.py`) parsea para poblar `url`/`institucion`/
    `fecha_captura`/`tipo_fuente` en la metadata del documento, igual que
    `fuentes.yaml` hace para los PDFs binarios (ver SPEC_MEJORAS_RAG.md
    secciones 1.1/1.2/1.4).
    """
    pagina = fetch_pagina(url)

    front_matter = {
        "url": url,
        "institucion": institucion,
        "categoria": categoria,
        "descripcion": descripcion.strip() if descripcion else "",
        "fecha_captura": date.today().isoformat(),
        "tipo_fuente": "web_oficial",
    }

    contenido = "---\n"
    contenido += yaml.safe_dump(front_matter, allow_unicode=True, sort_keys=False)
    contenido += "---\n\n"
    contenido += f"# {pagina.titulo}\n\n{pagina.contenido}\n"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    destino = OUTPUT_DIR / f"{_slug(url)}.md"
    destino.write_text(contenido, encoding="utf-8")
    return destino


def main():
    """Descarga las fuentes web de `data/fuentes_web.yaml` como snapshots locales.

    No se llama desde `build_index.py` (evita dependencia de red en cada
    reindex). Correr manualmente cuando se quiera actualizar/agregar fuentes
    web, y luego `python -m app.rag.build_index` para reindexar los
    snapshots resultantes.
    """
    grupos = yaml.safe_load(FUENTES_YAML.read_text(encoding="utf-8"))

    total = 0
    fallidas = 0

    for grupo in grupos:
        categoria = grupo["categoria"]
        for fuente in grupo["fuentes"]:
            url = fuente["url"]
            print(f"Descargando: {url}")
            try:
                destino = _guardar_snapshot(
                    url=url,
                    institucion=fuente.get("institucion", ""),
                    categoria=categoria,
                    descripcion=fuente.get("descripcion", ""),
                )
            except requests.RequestException as e:
                print(f"  ERROR al descargar: {e}")
                fallidas += 1
                continue

            print(f"  Guardado: {destino}")
            total += 1

    print(f"\nSnapshots guardados: {total}. Fallidos: {fallidas}.")
    if total:
        print("Recuerda correr 'python -m app.rag.build_index' para reindexar.")


if __name__ == "__main__":
    main()
