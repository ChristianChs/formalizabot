FROM python:3.11-slim AS base

WORKDIR /srv/app

# onnxruntime/sentence-transformers/chromadb necesitan estas libs en runtime,
# no solo en build, así que quedan en la imagen final (no en un stage aparte).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# torch CPU-only: el wheel con CUDA agrega ~2GB de más y este servicio
# nunca corre en GPU.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY data/normativa/ data/normativa/

# Hornea el índice de Chroma en la imagen: build_index.py solo usa embeddings
# locales (HuggingFace), no requiere GROQ_API_KEY. Así cada contenedor nuevo
# arranca con el índice ya listo, sin depender de un volumen inicializado
# a mano. Si cambias algo en data/normativa/, hay que reconstruir la imagen
# (mismo gotcha que en local: el índice no se regenera solo).
RUN python -m app.rag.build_index

ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/srv/app/.cache/huggingface

RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /srv/app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
