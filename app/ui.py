import uuid

import gradio as gr

from app.chatbot import Chatbot

chatbot = Chatbot()


def _formatear_fuentes(fuentes: list[dict]) -> str:
    lineas = []
    for f in fuentes:
        detalle = f["archivo"]
        if f.get("articulo") is not None:
            detalle += f" (Artículo {f['articulo']})"
        elif f.get("pagina") is not None:
            detalle += f" (pág. {f['pagina']})"
        lineas.append(f"- {detalle}")
    return "\n".join(lineas)


def responder(mensaje: str, historial_ui, session_id: str):
    parcial = {}
    for parcial in chatbot.stream(mensaje, session_id=session_id):
        yield parcial["respuesta"]

    if not parcial["fuera_de_dominio"] and parcial["fuentes"]:
        yield f"{parcial['respuesta']}\n\n📎 Fuentes:\n{_formatear_fuentes(parcial['fuentes'])}"


with gr.Blocks(title="FormalizaBot MYPE") as demo:
    gr.Markdown(
        "# FormalizaBot MYPE\n"
        "Orientación sobre formalización de micro y pequeñas empresas en Tacna, Perú."
    )
    session_id = gr.State(lambda: str(uuid.uuid4()))
    gr.ChatInterface(
        fn=responder,
        additional_inputs=[session_id],
    )


if __name__ == "__main__":
    demo.launch()
