from pydantic import BaseModel, Field


class RespuestaMYPE(BaseModel):
    """Esquema de salida estructurada de la cadena RAG.

    Separa lo que el LLM debe decidir (texto de la respuesta, si la
    pregunta cae fuera de dominio) de lo que se calcula de forma
    determinista fuera del LLM (las fuentes citadas, que vienen de los
    metadatos de los chunks recuperados, no de lo que el modelo "recuerde"
    haber leído).
    """

    respuesta: str = Field(
        description=(
            "Respuesta breve y directa para el usuario, siguiendo el tono y "
            "las reglas del system prompt (sin markdown complejo, apta para chat)."
        )
    )
    fuera_de_dominio: bool = Field(
        description=(
            "True si la pregunta del usuario no pertenece al dominio de "
            "formalización de MYPE (por ejemplo: clima, deportes, programación, "
            "temas personales u otros países). False en caso contrario."
        )
    )
    fundamentado_en_contexto: bool = Field(
        description=(
            "True SOLO si la respuesta efectivamente contiene o resume "
            "información normativa proveniente del CONTEXTO recuperado. "
            "False si la respuesta es una interacción social (saludo, "
            "agradecimiento, presentación) o si el CONTEXTO no tenía "
            "información relevante para la PREGUNTA."
        )
    )
