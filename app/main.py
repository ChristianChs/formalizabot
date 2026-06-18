from app.llm import get_llm


def main():
    llm = get_llm()
    respuesta = llm.invoke("Hola, ¿en qué consiste formalizar una MYPE en Perú?")
    print(respuesta.content)


if __name__ == "__main__":
    main()
