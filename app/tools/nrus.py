from langchain_core.tools import tool

# Tabla de categorías NRUS vigente (SUNAT): límite mensual de ingresos/compras
# -> (categoría, cuota mensual en soles). Cálculo determinista (RF8): el
# LLM decide SI invocar la tool, pero el monto sale de esta tabla fija,
# nunca de lo que el modelo "calcule" o "recuerde".
CATEGORIAS_NRUS = [
    (5000, 1, 20),
    (8000, 2, 50),
]


@tool
def calcular_categoria_nrus(ingresos_mensuales: float) -> str:
    """Determina la categoría NRUS y la cuota mensual a pagar (en soles)
    según los ingresos mensuales declarados por el negocio.

    Args:
        ingresos_mensuales: Ingresos mensuales estimados del negocio, en soles.
    """
    if ingresos_mensuales < 0:
        return "Los ingresos mensuales no pueden ser un valor negativo."

    for limite, categoria, cuota in CATEGORIAS_NRUS:
        if ingresos_mensuales <= limite:
            return (
                f"Con ingresos mensuales de S/ {ingresos_mensuales:.2f}, "
                f"corresponde la Categoría {categoria} del NRUS, con una "
                f"cuota mensual de S/ {cuota}."
            )

    return (
        f"Con ingresos mensuales de S/ {ingresos_mensuales:.2f} superas el "
        "límite del NRUS (hasta S/ 8,000 mensuales). Debes evaluar el "
        "Régimen Especial (RER) o el Régimen MYPE Tributario; te recomiendo "
        "verificarlo con SUNAT o tu contador."
    )
