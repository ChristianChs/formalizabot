from langchain_core.messages import SystemMessage, HumanMessage
from app.llm import get_llm
from app.prompts.system_prompt import SYSTEM_PROMPT


def main():
    llm = get_llm()

    mensajes = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content="Hola"),
    ]
    respuesta = llm.invoke(mensajes)
    print(respuesta.content)


if __name__ == "__main__":
    main()
