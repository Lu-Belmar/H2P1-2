# core/services.py
import pandas as pd
import openpyxl
from .constants import MESES_ES
from .utils import (
    contiene_anomalia,
    normalizar_ramo,
    normalizar_estado,
    parsear_fecha,
    calcular_rango_demora,
)

from collections import Counter
from .constants import MESES_ES, MOTIVOS_CATALOGO

VALORES_IGNORADOS_RANKING = {"", "-", "N/A", "NO APLICA", "SIN DATO", "NONE", "NO", "S/I", "SIN INFORMACION", "SIN INFORMACIÓN"}


def _obtener_top_frecuencia(registros, claves_posibles):
    """
    Busca el valor más repetido en una lista de diccionarios probando las claves indicadas.
    Devuelve (nombre_top, cantidad_menciones).
    """
    contador = Counter()
    for r in registros:
        valor_hallado = ""
        for k in claves_posibles:
            if k in r and r[k]:
                val_limpio = str(r[k]).strip()
                if val_limpio.upper() not in VALORES_IGNORADOS_RANKING:
                    valor_hallado = val_limpio
                    break
        if valor_hallado:
            contador[valor_hallado] += 1

    if not contador:
        return "Sin registros", 0
    return contador.most_common(1)[0]

def guardar_fila_consolidado(ruta_archivo, nombre_hoja, fila_excel, datos_form, es_nuevo=False):
    """Inserta o edita un registro en el XLSX preservando fórmulas y normalizando categorías."""
    wb = openpyxl.load_workbook(ruta_archivo)
    ws = wb[nombre_hoja]

    if es_nuevo:
        fila_excel = ws.max_row + 1

    f_siniestro = parsear_fecha(datos_form.get("fecha_siniestro"))
    f_cmf = parsear_fecha(datos_form.get("fecha_cmf"))
    f_limite = parsear_fecha(datos_form.get("fecha_limite"))
    f_fid = parsear_fecha(datos_form.get("fecha_fid"))

    oficio_raw = datos_form.get("n_oficio", "").strip()
    n_oficio = int(oficio_raw) if oficio_raw.isdigit() else oficio_raw

    ws.cell(fila_excel, 1, datos_form.get("nombre", "").strip())
    ws.cell(fila_excel, 2, n_oficio)
    ws.cell(fila_excel, 3, datos_form.get("n_siniestro", "").strip())
    ws.cell(fila_excel, 4, f_siniestro)
    ws.cell(fila_excel, 5, f_cmf)

    ws.cell(fila_excel, 6, f'=TEXT(E{fila_excel},"mmm")' if f_cmf else None)
    ws.cell(fila_excel, 7, f'=YEAR(E{fila_excel})' if f_cmf else None)

    ws.cell(fila_excel, 8, f_limite if f_limite else "-")
    ws.cell(fila_excel, 9, f_fid if f_fid else "-")

    ws.cell(fila_excel, 10, f'=TEXT(I{fila_excel},"mmm")' if f_fid else "-")
    ws.cell(fila_excel, 11, f'=YEAR(I{fila_excel})' if f_fid else None)

    ws.cell(fila_excel, 12, f"=I{fila_excel}-E{fila_excel}" if (f_fid and f_cmf) else None)

    if f_fid and f_limite:
        ws.cell(fila_excel, 13, f"=I{fila_excel}-H{fila_excel}")
        formula_n = (
            f'=IF(M{fila_excel}=0,"Sin retraso",'
            f'IF(AND(M{fila_excel}>0,M{fila_excel}<=3),"De 1 a 3 días de retraso",'
            f'IF(AND(M{fila_excel}>3,M{fila_excel}<=7),"De 4 a 7 días de retraso",'
            f'IF(AND(M{fila_excel}>7,M{fila_excel}<=10),"De 7 a 10 días de retraso",'
            f'IF(M{fila_excel}>10,"Más de 10 días de retraso",'
            f'"Respuesta enviada antes de la fecha límite")))))'
        )
        ws.cell(fila_excel, 14, formula_n)
    else:
        ws.cell(fila_excel, 13, None)
        ws.cell(fila_excel, 14, "-")

    ws.cell(fila_excel, 15, datos_form.get("motivo", "").strip())
    ws.cell(fila_excel, 16, datos_form.get("respuesta", "").strip())
    ws.cell(fila_excel, 17, normalizar_estado(datos_form.get("estado", "")))
    ws.cell(fila_excel, 18, normalizar_ramo(datos_form.get("ramo", "")))
    ws.cell(fila_excel, 19, datos_form.get("dda", "").strip() or None)
    ws.cell(fila_excel, 20, datos_form.get("zendesk", "").strip() or None)

    obs_texto = datos_form.get("observaciones", "").strip()
    if datos_form.get("marcar_anomalia") and not contiene_anomalia(obs_texto):
        obs_texto = f"{obs_texto} / Anomalía" if obs_texto else "Anomalía"
    ws.cell(fila_excel, 21, obs_texto or None)
    ws.cell(fila_excel, 25, datos_form.get("legal", "").strip() or None)

    for col_idx, fecha_val in [(4, f_siniestro), (5, f_cmf), (8, f_limite), (9, f_fid)]:
        if fecha_val:
            ws.cell(fila_excel, col_idx).number_format = "dd-mm-yyyy"

    if es_nuevo and "TABLACMF" in ws.tables:
        ws.tables["TABLACMF"].ref = f"A1:Y{ws.max_row}"

    wb.save(ruta_archivo)
    return fila_excel


# core/services.py (reemplazar leer_hoja_consolidado y construir_contexto_consolidado)

def leer_hoja_consolidado(ruta_archivo, nombre_hoja):
    """Lee 'Tabla consolidado' y normaliza automáticamente Ramo, Estado y Anomalía."""
    wb = openpyxl.load_workbook(ruta_archivo, data_only=True)
    try:
        ws = wb[nombre_hoja]

        # Detectar columnas opcionales en la fila 1 (Liquidador, Taller, Reclamante)
        mapa_headers = {}
        for col_idx in range(1, ws.max_column + 1):
            val_h = str(ws.cell(1, col_idx).value or "").strip().lower()
            if val_h:
                mapa_headers[val_h] = col_idx

        col_liq = next(
            (idx for nombre_col, idx in mapa_headers.items() if "liquidador" in nombre_col or "taller" in nombre_col),
            22,  # Columna V por defecto si existe
        )

        registros = []
        for r in range(2, ws.max_row + 1):
            nombre = ws.cell(r, 1).value
            n_oficio = ws.cell(r, 2).value
            n_siniestro = ws.cell(r, 3).value

            if nombre is None and n_oficio is None and n_siniestro is None:
                continue

            f_siniestro = parsear_fecha(ws.cell(r, 4).value)
            f_cmf = parsear_fecha(ws.cell(r, 5).value)
            f_limite = parsear_fecha(ws.cell(r, 8).value)
            f_fid = parsear_fecha(ws.cell(r, 9).value)

            mes_cmf = MESES_ES.get(f_cmf.month, "") if f_cmf else (ws.cell(r, 6).value or "")
            anio_cmf = f_cmf.year if f_cmf else (ws.cell(r, 7).value or "")
            mes_fid = MESES_ES.get(f_fid.month, "-") if f_fid else "-"
            anio_fid = f_fid.year if f_fid else ""

            dias_cmf_vs_fid = (f_fid - f_cmf).days if (f_fid and f_cmf) else None
            dias_demora = (f_fid - f_limite).days if (f_fid and f_limite) else None

            observaciones_str = str(ws.cell(r, 21).value or "").strip()
            nombre_str = str(nombre or "").strip()
            liq_str = str(ws.cell(r, col_liq).value or "").strip() if col_liq <= ws.max_column else ""
            legal_str = str(ws.cell(r, 25).value or "").strip() if ws.max_column >= 25 else ""

            registros.append({
                "fila_excel": r,
                "nombre": nombre_str,
                "reclamante": nombre_str,
                "asegurado": nombre_str,
                "liquidador": liq_str,
                "liquidador_taller": liq_str,
                "n_oficio": "" if n_oficio is None else str(n_oficio).replace(".0", ""),
                "n_siniestro": "" if n_siniestro is None else str(n_siniestro).replace(".0", ""),
                "fecha_siniestro": f_siniestro.strftime("%d-%m-%Y") if f_siniestro else "-",
                "fecha_siniestro_iso": f_siniestro.strftime("%Y-%m-%d") if f_siniestro else "",
                "fecha_cmf": f_cmf.strftime("%d-%m-%Y") if f_cmf else "-",
                "fecha_cmf_iso": f_cmf.strftime("%Y-%m-%d") if f_cmf else "",
                "mes_cmf": mes_cmf,
                "anio_cmf": anio_cmf,
                "fecha_limite": f_limite.strftime("%d-%m-%Y") if f_limite else "-",
                "fecha_limite_iso": f_limite.strftime("%Y-%m-%d") if f_limite else "",
                "fecha_fid": f_fid.strftime("%d-%m-%Y") if f_fid else "-",
                "fecha_fid_iso": f_fid.strftime("%Y-%m-%d") if f_fid else "",
                "mes_fid": mes_fid,
                "anio_fid": anio_fid,
                "dias_cmf_vs_fid": "-" if dias_cmf_vs_fid is None else dias_cmf_vs_fid,
                "dias_demora": "-" if dias_demora is None else dias_demora,
                "dias_demora_num": dias_demora or 0,
                "rango_demora": calcular_rango_demora(dias_demora),
                "motivo": str(ws.cell(r, 15).value or "").strip(),
                "respuesta": str(ws.cell(r, 16).value or "").strip(),
                "estado": normalizar_estado(ws.cell(r, 17).value),
                "ramo": normalizar_ramo(ws.cell(r, 18).value),
                "dda": str(ws.cell(r, 19).value or "").strip(),
                "zendesk": str(ws.cell(r, 20).value or "").strip(),
                "observaciones": observaciones_str,
                "tiene_anomalia": "SI" if contiene_anomalia(observaciones_str) else "NO",
                "legal": legal_str,
            })
        return registros
    finally:
        wb.close()


def construir_contexto_consolidado(registros):
    """Prepara KPIs, series de gráficos y dataset analítico para la plantilla."""
    tiempos = [r["dias_cmf_vs_fid"] for r in registros if isinstance(r["dias_cmf_vs_fid"], int)]
    promedio_dias = round(sum(tiempos) / len(tiempos), 1) if tiempos else 0
    total_anomalias = sum(1 for r in registros if r["tiene_anomalia"] == "SI")

    conteo_estados = {}
    for r in registros:
        est = r["estado"] or "Sin especificar"
        conteo_estados[est] = conteo_estados.get(est, 0) + 1

    anios_disponibles = sorted(
        {str(r["anio_cmf"]) for r in registros if str(r["anio_cmf"]).isdigit()}
    )

    registros_analytics = [
        {
            "oficio": r["n_oficio"],
            "anio": str(r["anio_cmf"]),
            "mes": str(r["mes_cmf"]).lower().strip(),
            "ramo": r["ramo"] or "SIN_RAMO",
            "anomalia": r["tiene_anomalia"],
            "motivo": r["motivo"] or "Sin clasificar",
            "estado": r["estado"] or "Sin especificar",
            "rango_demora": r["rango_demora"],
            "dias_cmf_fid": r["dias_cmf_vs_fid"] if isinstance(r["dias_cmf_vs_fid"], int) else None,
        }
        for r in registros
    ]

    top_liq_taller_nombre, top_liq_taller_cant = _obtener_top_frecuencia(
        registros,
        ["liquidador_taller", "liquidador", "taller", "dda"],
    )

    top_reclamante_nombre, top_reclamante_cant = _obtener_top_frecuencia(
        registros,
        ["reclamante", "asegurado", "nombre"],
    )
    motivos_en_excel = [r["motivo"] for r in registros if r.get("motivo")]
    motivos_dinamicos = list(dict.fromkeys(MOTIVOS_CATALOGO + motivos_en_excel))
    return {
        "datos_cargados": True,
        "motivos_catalogo": motivos_dinamicos,
        "datos_cargados": True,
        "registros": list(reversed(registros)),
        "total_filas": len(registros),
        "kpi_total_oficios": len(registros),
        "kpi_anomalias": total_anomalias,
        "promedio_dias": promedio_dias,
        "nombre_col_num": "Reclamos por Estado/Calidad de Respuesta",
        "chart_labels": list(conteo_estados.keys()),
        "chart_data": list(conteo_estados.values()),
        "anios_disponibles": anios_disponibles,
        "registros_analytics": registros_analytics,
        "top_liq_taller_nombre": top_liq_taller_nombre,
        "top_liq_taller_cant": top_liq_taller_cant,
        "top_reclamante_nombre": top_reclamante_nombre,
        "top_reclamante_cant": top_reclamante_cant,
    }


def leer_hoja_generica(ruta_archivo, nombre_hoja):
    """Procesa cualquier otra pestaña del libro Excel como vista previa estándar."""
    df = pd.read_excel(ruta_archivo, sheet_name=nombre_hoja).fillna("")
    if len(df) == 0:
        return {"hoja_vacia": True}

    columnas = df.columns.tolist()
    cols_num = df.select_dtypes(include=["number"]).columns.tolist()
    chart_labels, chart_data = [], []
    nombre_col_num = "Vista general"

    if cols_num:
        col_n = cols_num[0]
        nombre_col_num = str(col_n)
        chart_labels = [f"Fila {i+1}" for i in range(min(10, len(df)))]
        chart_data = [float(x) for x in df[col_n].head(10).tolist()]

    return {
        "datos_cargados": True,
        "columnas": columnas,
        "filas": df.values.tolist()[:100],
        "total_filas": len(df),
        "promedio_dias": "-",
        "nombre_col_num": nombre_col_num,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
    }