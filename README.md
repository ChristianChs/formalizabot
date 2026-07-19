# FormalizaBot MYPE

Agente conversacional especializado en orientación para la formalización de
micro y pequeñas empresas (MYPE) en Tacna, Perú. Proyecto desarrollado para
el curso de Inteligencia Artificial.

Toda respuesta con contenido normativo se fundamenta en documentos oficiales
recuperados por RAG, citando la fuente. Ver [`SPEC.md`](SPEC.md) para el
detalle de arquitectura y requisitos.

## Stack
- Python + LangChain (LCEL)
- LLM vía Groq (GPT-OSS 20B)
- Embeddings locales (HuggingFace) + Chroma como vectorstore
- Gradio como interfaz de prueba/demo

## 1. Instalación

Crear el entorno virtual e instalar dependencias:
```
python -m venv .venv
source .venv/Scripts/activate      # Windows (Git Bash)
# .venv\Scripts\Activate.ps1       # Windows (PowerShell)
pip install -r requirements.txt
```

Configurar variables de entorno: copiar `.env.example` a `.env` y completar
`GROQ_API_KEY` con una clave de [console.groq.com](https://console.groq.com).
```
GROQ_API_KEY=tu_clave_aqui
LLM_MODEL=openai/gpt-oss-20b
LLM_BASE_URL=https://api.groq.com/openai/v1
```

## 2. Construir el índice del RAG

El corpus normativo vive en `data/normativa/` (`.md` y `.pdf`). Antes de usar
el bot por primera vez, hay que construir el vectorstore:
```
python -m app.rag.build_index
```

**Importante**: hay que volver a correr este comando cada vez que se agregue,
edite o elimine un documento en `data/normativa/` — el índice no se actualiza
solo, y si queda desactualizado el bot va a responder "no tengo esa
información" aunque el documento ya la tenga.

## 3. Probar el bot

**Por consola** (una pregunta suelta, sin memoria):
```
python -m app.main
```

**Interfaz de chat** (con memoria de sesión, recomendado para probar
conversaciones reales de varios turnos):
```
python -m app.ui
```
Abre la URL local que imprime Gradio (por defecto `http://127.0.0.1:7860`).

**Set de regresión** (guardrail de dominio + resistencia a prompt injection):
```
python -m app.eval.regression
```
Corre con `max_concurrency=1` porque el tier gratuito de Groq tiene un
límite de 6000 tokens/minuto; si lo bajás de golpe con muchas pruebas
seguidas podés toparte con un `RateLimitError` — esperar un minuto y
reintentar.

## 4. Estructura del proyecto

```
app/
  main.py              # punto de entrada CLI (una pregunta, sin memoria)
  ui.py                # interfaz Gradio con memoria de sesión
  chatbot.py           # clase Chatbot: memoria por sesión + tools + RAG
  llm.py               # cliente LLM (Groq vía ChatOpenAI)
  schemas.py           # RespuestaMYPE (salida estructurada)
  prompts/
    system_prompt.py   # persona, guardrail de dominio, anti-injection
  rag/
    loader.py           # carga de .md/.pdf desde data/normativa/
    splitter.py          # chunking
    embeddings.py         # embeddings HuggingFace
    vectorstore.py          # build/load de Chroma (cacheado)
    chain.py                 # cadena RAG completa (LCEL)
    build_index.py            # script de (re)indexación
  tools/
    nrus.py              # tool: cálculo determinista de categoría NRUS
    derivar_humano.py    # tool: derivación a asesor humano
    router.py            # decide si una tool aplica, valida y ejecuta
  eval/
    regression.py        # set de regresión (chain.batch)
data/
  normativa/             # corpus fuente (.md/.pdf) — no versionado
  chroma_db/             # índice vectorial persistido — no versionado
```

## 5. Estado del proyecto

El roadmap funcional está completo (ver [`SPEC.md`](SPEC.md), sección 5):
guardrail de dominio, grounding con citas, memoria de sesión, salida
estructurada, resistencia a prompt injection, set de regresión y tool
calling determinista. Lo que queda pendiente es optimización (paralelizar
el guardrail de dominio) y, sobre todo, seguir ampliando y curando el
corpus en `data/normativa/`.
