from langchain_core.tools import tool

# Umbrales de clasificación MYPE (Ley MYPE / REMYPE, ver
# data/normativa/04_REGISTRO_LABORAL_Y_REMYPE.md): ventas anuales en UIT.
# Se recibe el valor ya en UIT (no en soles) porque el corpus normativo no
# fija un monto de la UIT en soles — convertirlo requeriría un dato que no
# viene del RAG y quedaría desactualizado sin que nadie lo note (mismo
# criterio de no inventar datos normativos que ya sigue calcular_categoria_nrus).
LIMITE_MICROEMPRESA_UIT = 150
LIMITE_PEQUENA_EMPRESA_UIT = 1700


@tool
def clasificar_empresa_mype(ventas_anuales_uit: float) -> str:
    """Clasifica una empresa como microempresa, pequeña empresa o fuera del
    rango MYPE según sus ventas anuales expresadas en UIT, para efectos de
    inscripción en REMYPE.

    Args:
        ventas_anuales_uit: Ventas anuales de la empresa, expresadas en UIT
            (no en soles).
    """
    if ventas_anuales_uit < 0:
        return "Las ventas anuales no pueden ser un valor negativo."

    if ventas_anuales_uit <= LIMITE_MICROEMPRESA_UIT:
        return (
            f"Con ventas anuales de {ventas_anuales_uit:.2f} UIT, la empresa "
            f"clasifica como Microempresa (hasta {LIMITE_MICROEMPRESA_UIT} "
            "UIT), y puede inscribirse en REMYPE con los beneficios "
            "correspondientes a esa categoría."
        )

    if ventas_anuales_uit <= LIMITE_PEQUENA_EMPRESA_UIT:
        return (
            f"Con ventas anuales de {ventas_anuales_uit:.2f} UIT, la empresa "
            f"clasifica como Pequeña Empresa (entre {LIMITE_MICROEMPRESA_UIT} "
            f"y {LIMITE_PEQUENA_EMPRESA_UIT} UIT), y puede inscribirse en "
            "REMYPE con los beneficios correspondientes a esa categoría."
        )

    return (
        f"Con ventas anuales de {ventas_anuales_uit:.2f} UIT superas el "
        f"límite de Pequeña Empresa ({LIMITE_PEQUENA_EMPRESA_UIT} UIT), por "
        "lo que la empresa no califica para inscribirse en REMYPE bajo la "
        "Ley MYPE."
    )
