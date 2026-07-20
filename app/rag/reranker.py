from functools import lru_cache

from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

# Cross-encoder multilingüe (entrenado sobre mMARCO, incluye español), en
# vez de uno solo-inglés (ej. ms-marco-MiniLM), dado que el corpus normativo
# está en español.
RERANK_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


@lru_cache(maxsize=1)
def _get_cross_encoder() -> HuggingFaceCrossEncoder:
    """Carga el modelo cross-encoder usado para reordenar candidatos.

    Cacheada: cargar el modelo es costoso y `build_reranker` se invoca en
    cada construcción del retriever.
    """
    return HuggingFaceCrossEncoder(model_name=RERANK_MODEL)


def build_reranker(top_n: int) -> CrossEncoderReranker:
    """Reordena los chunks recuperados por relevancia real a la pregunta.

    La similitud de embeddings (usada por el retriever base) mide cercanía
    semántica general entre pregunta y chunk por separado; un cross-encoder
    evalúa el par (pregunta, chunk) conjuntamente, lo que da una señal de
    relevancia más precisa para elegir los `top_n` mejores de un pool más
    grande de candidatos.
    """
    return CrossEncoderReranker(model=_get_cross_encoder(), top_n=top_n)
