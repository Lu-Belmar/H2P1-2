# core/utils.py
import unicodedata
from datetime import datetime, date


def quitar_tildes(texto):
    """Elimina tildes para comparaciones insensibles a acentos."""
    return "".join(
        c for c in unicodedata.normalize("NFD", str(texto).lower().strip())
        if unicodedata.category(c) != "Mn"
    )


def contiene_anomalia(texto_observacion):
    """Detecta si el texto contiene 'anomalía' o 'anomalias'."""
    if not texto_observacion:
        return False
    return "anomal" in quitar_tildes(texto_observacion)


def normalizar_ramo(valor):
    """Unifica 'RR.VV', 'RRVV', 'rv' y 'RV' bajo la categoría única 'RV'."""
    if not valor:
        return ""
    limpio = str(valor).strip().upper()
    if limpio in ("RR.VV", "RRVV", "RR.VV.", "RV"):
        return "RV"
    return limpio


def normalizar_estado(valor):
    """Unifica variantes sin tilde o abreviadas de Estado/Calidad de la respuesta."""
    if not valor or not str(valor).strip():
        return ""
    base = quitar_tildes(valor)
    if "completa" in base:
        return "Con solución completa"
    if "parcial" in base:
        return "Con solución parcial"
    if "contencion" in base:
        return "Con respuesta de contención"
    if "sin respuesta" in base:
        return "Sin respuesta"
    return str(valor).strip()


def parsear_fecha(valor):
    """Convierte celdas de Excel o strings de formularios en datetime.date."""
    if not valor or valor == "-":
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        valor = valor.strip()
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(valor[:10], fmt).date()
            except ValueError:
                continue
    return None


def calcular_rango_demora(dias_demora):
    """Replica la fórmula condicional de la Columna N del Excel."""
    if dias_demora is None:
        return "-"
    if dias_demora == 0:
        return "Sin retraso"
    elif 1 <= dias_demora <= 3:
        return "De 1 a 3 días de retraso"
    elif 4 <= dias_demora <= 7:
        return "De 4 a 7 días de retraso"
    elif 8 <= dias_demora <= 10:
        return "De 7 a 10 días de retraso"
    elif dias_demora > 10:
        return "Más de 10 días de retraso"
    elif dias_demora < 0:
        return "Respuesta enviada antes de la fecha límite"
    return "-"