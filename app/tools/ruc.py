import re

import requests
from langchain_core.tools import tool

from app.config import RUC_API_KEY

# api.decolecta.com (SUNAT vía Decolecta) — consulta en tiempo real, no un
# dato del corpus normativo (ver SPEC_MEJORAS_RAG.md, punto 10 de la
# sección 4): el estado/condición de un RUC es información transaccional
# del contribuyente, no una norma, así que ningún RAG lo resuelve. El
# endpoint devuelve el dato real; esta tool nunca lo infiere ni lo asume.
RUC_API_URL = "https://api.decolecta.com/v1/sunat/ruc"
RUC_API_TIMEOUT_SEGUNDOS = 8


@tool
def consultar_estado_ruc(ruc: str) -> str:
    """Consulta en tiempo real el estado (activo/inactivo) y la condición
    (habido/no habido) de un número de RUC ante SUNAT, junto con la razón
    social y dirección registradas.

    Args:
        ruc: Número de RUC a consultar, de 11 dígitos.
    """
    ruc_normalizado = re.sub(r"\D", "", ruc)
    if len(ruc_normalizado) != 11:
        return (
            f"'{ruc}' no es un número de RUC válido: debe tener 11 dígitos. "
            "Verifica el número e inténtalo de nuevo."
        )

    if not RUC_API_KEY:
        return (
            "La consulta de RUC en tiempo real no está configurada en este "
            "momento (falta RUC_API_KEY). No puedo verificar el estado de "
            "ese RUC ahora mismo."
        )

    try:
        respuesta = requests.get(
            RUC_API_URL,
            params={"numero": ruc_normalizado},
            headers={
                "Authorization": f"Bearer {RUC_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=RUC_API_TIMEOUT_SEGUNDOS,
        )
    except requests.RequestException:
        # Falla de red/timeout: nunca debe leerse como "el RUC no existe".
        return (
            "No se pudo conectar al servicio de consulta de RUC en este "
            "momento. Intenta de nuevo en unos minutos, o verifica el RUC "
            "directamente en https://e-consultaruc.sunat.gob.pe."
        )

    if respuesta.status_code in (404, 422):
        # 422 es lo que devuelve la API cuando el RUC tiene 11 dígitos pero
        # no pasa la validación del dígito verificador de SUNAT (RUC
        # inexistente/mal formado); 404 cubre el caso de "no encontrado".
        return f"El RUC {ruc_normalizado} no existe o no es válido según SUNAT."

    if respuesta.status_code == 401:
        return (
            "La consulta de RUC en tiempo real no está disponible ahora "
            "mismo (credencial inválida). No puedo verificar ese RUC."
        )

    if not respuesta.ok:
        return (
            f"El servicio de consulta de RUC respondió con un error "
            f"({respuesta.status_code}). Intenta de nuevo más tarde."
        )

    datos = respuesta.json()
    razon_social = datos.get("razon_social", "(sin razón social registrada)")
    estado = datos.get("estado", "desconocido")
    condicion = datos.get("condicion", "desconocida")
    direccion = datos.get("direccion")

    resultado = (
        f"RUC {ruc_normalizado} — {razon_social}. "
        f"Estado: {estado}. Condición: {condicion}."
    )
    if direccion:
        resultado += f" Domicilio fiscal: {direccion}."

    return resultado
