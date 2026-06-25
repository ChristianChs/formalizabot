from app.rag.vectorstore import load_vectorstore


def main():
    vectorstore = load_vectorstore()

    pregunta = "¿Qué se entiende por formalizar una empresa?"
    resultados = vectorstore.similarity_search(pregunta, k=2)

    print(f"\n=== Resultados para: '{pregunta}' ===")
    for i, doc in enumerate(resultados):
        print(f"\n--- Resultado {i + 1} ---")
        print(f"Fuente: {doc.metadata.get('nombre_archivo')}")
        print(f"Chunk #: {doc.metadata.get('chunk_index')}")
        print(f"Contenido: {doc.page_content[:300]}...")


if __name__ == "__main__":
    main()
