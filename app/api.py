"""API HTTP para que servicios externos (ej. un bot de WhatsApp sobre
Baileys) conversen con el Chatbot sin acoplarse a Gradio.

Pensada para redes internas/confianza entre servicios: no implementa
autenticación. Si el servicio de WhatsApp corre en otra máquina o el
endpoint queda accesible desde fuera de la red local, hay que agregar
un mecanismo de autenticación (API key, mTLS, etc.) antes de exponerlo.

Las requests entrantes se encolan y se procesan de a una (QUEUE_WORKERS=1):
el tier gratuito de Groq limita a 6000 tokens/minuto, y `resolver_tool_call`
+ la cadena RAG ya asumen ese límite en `app/eval/regression.py`
(`max_concurrency=1`). Si varios mensajes de WhatsApp llegan a la vez, se
procesan en orden de llegada en vez de dispararse en paralelo y toparse con
un `RateLimitError`.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.chatbot import Chatbot

QUEUE_MAXSIZE = 50
QUEUE_WORKERS = 1

chatbot = Chatbot()


class _Trabajo:
    __slots__ = ("mensaje", "session_id", "future")

    def __init__(self, mensaje: str, session_id: str, future: asyncio.Future):
        self.mensaje = mensaje
        self.session_id = session_id
        self.future = future


async def _worker(cola: asyncio.Queue):
    loop = asyncio.get_running_loop()
    while True:
        trabajo = await cola.get()
        try:
            resultado = await loop.run_in_executor(
                None, chatbot.invoke, trabajo.mensaje, trabajo.session_id
            )
            if not trabajo.future.done():
                trabajo.future.set_result(resultado)
        except Exception as exc:  # noqa: BLE001 - se reenvía al caller vía el future
            if not trabajo.future.done():
                trabajo.future.set_exception(exc)
        finally:
            cola.task_done()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.cola = asyncio.Queue(maxsize=QUEUE_MAXSIZE)
    workers = [
        asyncio.create_task(_worker(app.state.cola)) for _ in range(QUEUE_WORKERS)
    ]
    yield
    for worker in workers:
        worker.cancel()


app = FastAPI(title="FormalizaBot MYPE API", lifespan=lifespan)


class PreguntaRequest(BaseModel):
    mensaje: str
    session_id: str = "default"


class Fuente(BaseModel):
    archivo: str
    pagina: int | None = None
    chunk: int | None = None


class RespuestaResponse(BaseModel):
    respuesta: str
    fuera_de_dominio: bool
    fuentes: list[Fuente]


@app.get("/health")
def health():
    return {"status": "ok", "en_cola": app.state.cola.qsize()}


@app.post("/chat", response_model=RespuestaResponse)
async def chat(payload: PreguntaRequest):
    """Encola el mensaje y espera su turno de procesamiento (RF ad-hoc de
    integración externa).

    `session_id` mantiene memoria de conversación por número/chat: cada JID
    de WhatsApp debe mapearse a un `session_id` estable para que el bot
    resuelva referencias a turnos anteriores ("¿y para ese régimen?").
    """
    future = asyncio.get_running_loop().create_future()
    trabajo = _Trabajo(payload.mensaje, payload.session_id, future)
    try:
        app.state.cola.put_nowait(trabajo)
    except asyncio.QueueFull:
        raise HTTPException(
            status_code=503, detail="Cola llena, reintentar en unos segundos"
        )

    try:
        resultado = await future
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return RespuestaResponse(
        respuesta=resultado["respuesta"],
        fuera_de_dominio=resultado["fuera_de_dominio"],
        fuentes=resultado["fuentes"],
    )
