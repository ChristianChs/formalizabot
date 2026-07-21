# PDFs escaneados — pendientes de OCR

Estos 8 archivos vienen de la sección "Legislación" de la Licencia de
Funcionamiento de la Municipalidad Provincial de Tacna
(https://www.munitacna.gob.pe/pagina/sf/servicios/licencia-funcionamiento#info).

Se movieron aquí, fuera de `data/normativa_web/licencia_funcionamiento_tacna/`,
porque son PDFs escaneados como imagen: `pypdf` extrae **0 caracteres de
texto en todas sus páginas**. `PyPDFLoader` (el loader que usa
`app/rag/loader.py`/`build_index.py`) no hace OCR, así que si estos
archivos quedaran en la carpeta indexable, `build_index.py` los cargaría
como documentos vacíos — chunks sin contenido que no aportan nada a la
búsqueda por similitud y solo ensucian el índice.

Verificado el 2026-07-21 con:

```python
import pypdf
r = pypdf.PdfReader("archivo.pdf")
sum(len((p.extract_text() or "")) for p in r.pages)  # == 0 para los 8 de aquí
```

No se borraron para no perder la referencia de que la norma existe y de
dónde se obtuvo — quedan como snapshot local por si en algún momento se
agrega un paso de OCR (p. ej. `pytesseract` u otro) al pipeline de
indexación (ver `SPEC_MEJORAS_RAG.md`).

## Archivos

| Archivo | Norma |
|---|---|
| `legislacion_01_om_001_2025_modifica_derecho_tramite_itse.pdf` | Ordenanza Municipal 001-2025 — modifica derecho de trámite de procedimientos ITSE (se eliminó `legislacion_03`, duplicado byte-a-byte de este mismo archivo — confirmado por el usuario) |
| `legislacion_06_om_049_2010_modifica_om_0043_08.pdf` | Ordenanza Municipal N° 049-2010 |
| `legislacion_07_om_032_2022_rof.pdf` | Ordenanza Municipal N° 032-2022 — Reglamento de Organización y Funciones (41.6 MB) |
| `legislacion_08_decreto_alcaldia_010_2019.pdf` | Decreto de Alcaldía N° 010-2019 (11.2 MB) |
| `legislacion_11_dl_776_ley_tributacion_municipal.pdf` | Decreto Legislativo N° 776 — Ley de Tributación Municipal |
| `legislacion_15_om_0014_2008_adecuacion_ley_marco.pdf` | Ordenanza Municipal N° 0014-08 — adecuación a la Ley Marco de Licencia de Funcionamiento |
| `legislacion_16_om_0016_2014_tupa.pdf` | Ordenanza Municipal N° 0016-14 — TUPA |
| `legislacion_18_om_0030_2009_reglamento_ruidos.pdf` | Ordenanza Municipal N° 0030-09 — Reglamento de Control y Regulación de Ruidos |

## Cómo re-verificar si algún día se re-descargan o cambian

```python
import pypdf, glob, os
for f in sorted(glob.glob("*.pdf")):
    r = pypdf.PdfReader(f)
    chars = sum(len((p.extract_text() or "")) for p in r.pages)
    print(f"{os.path.basename(f):55s} pages={len(r.pages):4d} chars={chars}")
```

Si `chars > 0`, el archivo ya tiene texto extraíble y puede moverse de
vuelta a la carpeta padre para indexarse normalmente.
