import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
# Sin este límite explícito, Groq puede cortar la generación a mitad de una
# respuesta larga (JSON estructurado + explicación completa de un trámite);
# el JsonOutputParser tolera JSON incompleto y devuelve el texto truncado
# sin error, así que el corte pasa desapercibido. 1024 da margen para una
# respuesta detallada sin dejar la generación sin techo.
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY no está configurada. Revisa tu archivo .env")

# Token de api.decolecta.com (consulta RUC/SUNAT en tiempo real, ver
# app/tools/ruc.py). A diferencia de GROQ_API_KEY, no es obligatoria para
# que el bot arranque: si falta, la tool lo reporta explícitamente en su
# propia respuesta en vez de tumbar toda la aplicación.
RUC_API_KEY = os.getenv("RUC_API_KEY")
