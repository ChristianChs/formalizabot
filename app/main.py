from app.rag.chain import build_rag_chain


def main():
    chain = build_rag_chain()

    pregunta = "Quiero abrir una bodega en Tacna, ¿qué necesito?"
    respuesta = chain.invoke(pregunta)

    print(f"=== Pregunta ===\n{pregunta}\n")
    print(f"=== Respuesta (con RAG) ===\n{respuesta}")


if __name__ == "__main__":
    main()
