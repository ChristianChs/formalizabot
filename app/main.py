from app.rag.chain import answer_question


def main():
    pregunta = "¿Cuales son los pasos a seguir para constituir mi empresa?"
    resultado = answer_question(pregunta)

    print(f"=== Pregunta ===\n{pregunta}\n")
    print(f"=== Respuesta ===\n{resultado['respuesta']}\n")
    print(f"=== Fuera de dominio: {resultado['fuera_de_dominio']} ===\n")

    if resultado["fuentes"]:
        print("=== Fuentes recuperadas ===")
        for fuente in resultado["fuentes"]:
            pagina = f"pág. {fuente['pagina']}" if fuente["pagina"] else "sin pág."
            chunk = f"chunk {fuente['chunk']}" if fuente["chunk"] else "sin chunk"
            print(f"- {fuente['archivo']} | {pagina} | {chunk}")


if __name__ == "__main__":
    main()
