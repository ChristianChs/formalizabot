from app.rag.loader import load_documents
from app.rag.splitter import split_documents
from app.rag.vectorstore import build_vectorstore


def main():
    """Reconstruye el vectorstore completo desde los documentos fuente.

    Punto de entrada manual para re-indexar el corpus normativo. Se debe
    ejecutar cada vez que se agreguen, modifiquen o eliminen documentos
    en `data/normativa/`.
    """
    print("=== Cargando documentos ===")
    documentos = load_documents("data/normativa")

    print("\n=== Dividiendo en chunks ===")
    chunks = split_documents(documentos)

    print("\n=== Construyendo vectorstore ===")
    build_vectorstore(chunks)

    print("\nIndexación completa.")


if __name__ == "__main__":
    main()
