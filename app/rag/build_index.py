from pathlib import Path

from app.rag.loader import load_documents
from app.rag.splitter import split_documents
from app.rag.vectorstore import build_vectorstore


def main():
    """Reconstruye el vectorstore completo desde los documentos fuente.

    Punto de entrada manual para re-indexar el corpus normativo. Se debe
    ejecutar cada vez que se agreguen, modifiquen o eliminen documentos
    en `data/normativa/` o `data/normativa_web/`.
    """
    print("=== Cargando documentos (data/normativa) ===")
    documentos = load_documents("data/normativa")

    if Path("data/normativa_web").exists():
        print("\n=== Cargando documentos (data/normativa_web) ===")
        documentos += load_documents("data/normativa_web", recursive=True)

    print("\n=== Dividiendo en chunks ===")
    chunks = split_documents(documentos)

    print("\n=== Construyendo vectorstore ===")
    build_vectorstore(chunks)

    print("\nIndexación completa.")


if __name__ == "__main__":
    main()
