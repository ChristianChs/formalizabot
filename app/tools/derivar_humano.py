from langchain_core.tools import tool


@tool
def derivar_a_humano(motivo: str) -> str:
    """Deriva la conversación a un asesor humano cuando la consulta excede
    lo que el bot puede resolver o el usuario pide explícitamente hablar
    con una persona. No resuelve la consulta: solo registra la derivación.

    Args:
        motivo: Razón breve de la derivación (ej. "usuario pidió hablar
            con un asesor", "caso legal complejo fuera del alcance del bot").
    """
    return (
        "Tu consulta fue derivada a un asesor humano del equipo de "
        f"formalización. Motivo: {motivo}. En breve te contactarán."
    )
