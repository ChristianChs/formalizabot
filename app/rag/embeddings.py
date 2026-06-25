from langchain_huggingface import HuggingFaceEmbeddings


def get_embeddings() -> HuggingFaceEmbeddings:
    """Crea el modelo de embeddings usado para indexar y buscar en el RAG.

    Usa un modelo local de HuggingFace (sentence-transformers), evitando
    depender de una API externa de pago solo para esta pieza. El modelo
    elegido soporta múltiples idiomas, incluyendo español, lo cual es
    relevante dado que el corpus normativo está en español.

    Returns:
        HuggingFaceEmbeddings: Instancia lista para generar vectores,
            tanto en la fase de indexación como en la de retrieval.
    """
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
