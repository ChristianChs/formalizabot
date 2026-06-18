from langchain_openai import ChatOpenAI
from app.config import GROQ_API_KEY, LLM_MODEL, LLM_BASE_URL


def get_llm(temperature: float = 0.3) -> ChatOpenAI:
    """
    Crea y retorna una instancia configurada del LLM via Groq.

    Temperature 0.3 por defecto.
    """
    return ChatOpenAI(
        model=LLM_MODEL,
        api_key=GROQ_API_KEY,
        base_url=LLM_BASE_URL,
        temperature=temperature,
    )
