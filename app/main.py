from app.rag.loader import load_documents
from app.rag.splitter import split_documents


def main():
    print("=== Cargando documentos ===")
    documentos = load_documents("data/normativa")

    print("\n=== Dividiendo en chunks ===")
    chunks = split_documents(documentos)

    print("\n=== Muestra de los primeros 3 chunks ===")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n--- Chunk {i + 1} ---")
        print(f"Fuente   : {chunk.metadata.get('nombre_archivo')}")
        print(f"Tipo     : {chunk.metadata.get('tipo')}")
        print(f"Chunk #  : {chunk.metadata.get('chunk_index')}")
        print(f"Caracteres: {len(chunk.page_content)}")
        print(f"Contenido: {chunk.page_content[:300]}...")


if __name__ == "__main__":
    main()
