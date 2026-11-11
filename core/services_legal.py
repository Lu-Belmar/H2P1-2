# core/services_legal.py
from datetime import date, datetime
import numpy as np
import openpyxl

MESES_NOMBRES_LEGAL = [
    "01 Enero", "02 Febrero", "03 Marzo", "04 Abril",
    "05 Mayo", "06 Junio", "07 Julio", "08 Agosto",
    "09 Septiembre", "10 Octubre", "11 Noviembre", "12 Diciembre"
]

SENTENCIAS_CATALOGO_LEGAL = [
    "A FAVOR",
    "A FAVOR/INCOMPETENCIA",
    "A FAVOR/ABANDONO",
    "A FAVOR/EXCEPCION DILATORIA",
    "SENTENCIA CONDENATORIA",
    "ACUERDO",
    "INCOMPETENCIA/ACUERDO",
    "AR",
    "SCP",
    "DNP",
    "Sobreseimiento definitivo",
    "EN CONTRA",
]

DELITOS_PENALES_CONOCIDOS = {
    "FRAUDE AL SEGURO",
    "APROPIACIÓN INDEBIDA",
    "APROPIACION INDEBIDA",
    "ROBO",
    "RECEPTACIÓN",
    "RECEPTACION",
    "ESTAFA",
    "CLONACIÓN",
    "CLONACION",
    "OBSTRUCCIÓN A LA JUSTICIA",
    "OBSTRUCCION A LA JUSTICIA",
}

COLUMNAS_BIMESTRES_REPORTES = [
    (6, "rep_anteriores", "Reportes anteriores (hasta sep-2026)"),
    (7, "oct_2026", "Octubre 2026"),
    (8, "dic_2026", "Diciembre 2026"),
    (9, "feb_2027", "Febrero 2027"),
    (10, "abr_2027", "Abril 2027"),
    (11, "jun_2027", "Junio 2027"),
    (12, "ago_2027", "Agosto 2027"),
    (13, "oct_2027", "Octubre 2027"),
    (14, "dic_2027", "Diciembre 2027"),
]


def _limpiar_str(val):
    if val is None:
        return ""
    return str(val).strip()


def _parsear_fecha(val):
    if not val:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    texto = str(val).strip()[:10]
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    return None


def _formatear_fecha_iso(d):
    return d.strftime("%Y-%m-%d") if d else ""


def _formatear_fecha_vista(d):
    return d.strftime("%d-%m-%Y") if d else "-"


def clasificar_bloque_legal(competencia):
    comp_up = _limpiar_str(competencia).upper()
    if comp_up == "PENAL":
        return "PENAL"
    return "CIVIL"


def clasificar_motivo_o_delito(competencia, motivo_delito):
    comp_up = _limpiar_str(competencia).upper()
    mot_up = _limpiar_str(motivo_delito).upper()
    if comp_up == "PENAL" or mot_up in DELITOS_PENALES_CONOCIDOS:
        return "DELITO"
    return "MOTIVO"


def clasificar_sentencia_winrate(sentencia):
    s = _limpiar_str(sentencia).upper()
    if not s or s == "-":
        return "SIN_SENTENCIA"
    if any(k in s for k in ("DNP", "SOBRESEIMIENTO", "EN CONTRA")):
        return "EN_CONTRA"
    return "A_FAVOR"


def _dias_habiles_excel(fecha_ini, fecha_fin, feriados_np):
    if not fecha_ini or not fecha_fin:
        return None
    d1 = np.datetime64(fecha_ini.strftime("%Y-%m-%d"))
    d2 = np.datetime64(fecha_fin.strftime("%Y-%m-%d"))
    return int(np.busday_count(d1, d2, holidays=feriados_np))


def cargar_catalogos_hojas_auxiliares(wb):
    estudios = []
    if "Estudios Juridicos" in wb.sheetnames:
        ws_est = wb["Estudios Juridicos"]
        for r in range(2, ws_est.max_row + 1):
            val = _limpiar_str(ws_est.cell(r, 2).value)
            if val and val not in estudios:
                estudios.append(val)

    # 1. Inicializar primero todas las listas vacías
    calificaciones, motivos, partes, competencias, estados = [], [], [], [], []

    # 2. Poblar desde la hoja 'Estados Nuevos'
    if "Estados Nuevos" in wb.sheetnames:
        ws_en = wb["Estados Nuevos"]
        for r in range(2, ws_en.max_row + 1):
            for col_idx, destino in [
                (19, calificaciones),
                (20, motivos),
                (21, partes),
                (22, competencias),
                (23, estados),
            ]:
                v = _limpiar_str(ws_en.cell(r, col_idx).value)
                if v and v not in destino:
                    destino.append(v)

    # 3. Filtrar 'Archivada' DESPUÉS de haber creado y llenado la lista 'estados'
    estados = [e for e in estados if e.strip().lower() not in ("archivada", "archivado")]

    tribunales = []
    if "Tribunales" in wb.sheetnames:
        ws_tr = wb["Tribunales"]
        for r in range(2, ws_tr.max_row + 1):
            v = _limpiar_str(ws_tr.cell(r, 3).value)
            if v:
                tribunales.append(v)

    feriados_fechas = []
    if "Feriados" in wb.sheetnames:
        ws_fer = wb["Feriados"]
        for r in range(2, ws_fer.max_row + 1):
            f_dt = _parsear_fecha(ws_fer.cell(r, 1).value)
            if f_dt:
                feriados_fechas.append(f_dt.strftime("%Y-%m-%d"))

    return {
        "estudios_catalogo": estudios or [
            "Estudio Carvallo Abogados SpA",
            "Fiscalia Privada",
            "Pumpin, Dorfman, Nasser, Díaz y Compañia limitada",
            "Inzunza y Mohor Ltda.",
            "Ramdohr Asesorías Legales Ltda",
            "SILVA & PARMAR ABOGADOS SpA",
            "Servicios y Asesorias Birkner y Cía. Ltda.",
            "Ríos Abogados Limitada.",
            "Sociedad de Profesionales Quezada, Bórquez y Cía. Limitada",
            "Juan Pablo Cucurella",
            "Legalchile S.A.",
        ],
        "calificaciones_legal": calificaciones or ["Dinamica", "Robo", "Ramos Varios", "Apropiación Indebida", "No"],
        "motivos_legal": motivos or ["Fraude al seguro", "Incumplimiento de contrato", "Infracción Ley del Consumidor", "Apropiación Indebida", "Arbitraje", "Robo"],
        "partes_legal": partes or ["Querellante", "Demandado", "Recupero", "RC No Aplica", "Querellado"],
        "competencias_legal": competencias or ["Penal", "Civil", "JPL", "Recupero", "Arbitraje"],
        "estados_legal": estados or ["En Proceso", "Terminada"],
        "tribunales_catalogo": tribunales,
        "feriados_np": np.array(feriados_fechas, dtype="datetime64[D]") if feriados_fechas else np.array([], dtype="datetime64[D]"),
    }

def leer_hoja_causas_legales(ruta_archivo, nombre_hoja):
    wb = openpyxl.load_workbook(ruta_archivo, data_only=True)
    try:
        catalogos = cargar_catalogos_hojas_auxiliares(wb)
        feriados_np = catalogos["feriados_np"]
        ws = wb[nombre_hoja]

        # 1. Leer hoja 'Reportes estudios'
        reportes_por_id = {}
        lista_reportes_estudios = []
        if "Reportes estudios" in wb.sheetnames:
            ws_rep = wb["Reportes estudios"]
            for r_idx in range(3, ws_rep.max_row + 1):
                cid = _limpiar_str(ws_rep.cell(r_idx, 1).value)
                if not cid:
                    continue
                item_rep = {
                    "fila_reporte": r_idx,
                    "id_causa": cid,
                    "siniestro": _limpiar_str(ws_rep.cell(r_idx, 2).value),
                    "competencia": _limpiar_str(ws_rep.cell(r_idx, 3).value),
                    "estudio": _limpiar_str(ws_rep.cell(r_idx, 4).value),
                    "estado": _limpiar_str(ws_rep.cell(r_idx, 5).value),
                }
                ultimo_txt = ""
                ultimo_periodo = ""
                for col_num, key_name, label_col in COLUMNAS_BIMESTRES_REPORTES:
                    val_txt = _limpiar_str(ws_rep.cell(r_idx, col_num).value)
                    item_rep[key_name] = val_txt
                    if val_txt:
                        ultimo_txt = val_txt
                        ultimo_periodo = label_col
                item_rep["ultimo_texto"] = ultimo_txt
                item_rep["ultimo_periodo"] = ultimo_periodo
                reportes_por_id[cid] = item_rep
                lista_reportes_estudios.append(item_rep)

        # 2. Leer hoja 'Informes recibidos'
        informes_por_estudio = {}
        lista_informes_recibidos = []
        if "Informes recibidos" in wb.sheetnames:
            ws_inf = wb["Informes recibidos"]
            for r_idx in range(4, ws_inf.max_row + 1):
                f_rec = _parsear_fecha(ws_inf.cell(r_idx, 1).value)
                est_nom = _limpiar_str(ws_inf.cell(r_idx, 2).value)
                if not f_rec and not est_nom:
                    continue
                area_inf = _limpiar_str(ws_inf.cell(r_idx, 3).value)
                periodo_inf = _limpiar_str(ws_inf.cell(r_idx, 4).value)
                f_lim = _parsear_fecha(ws_inf.cell(r_idx, 5).value)
                atraso_raw = ws_inf.cell(r_idx, 6).value
                if isinstance(atraso_raw, (int, float)):
                    atraso_dias = int(atraso_raw)
                elif f_rec and f_lim:
                    atraso_dias = max(0, _dias_habiles_excel(f_lim, f_rec, feriados_np) or 0)
                else:
                    atraso_dias = 0

                recibido_de = _limpiar_str(ws_inf.cell(r_idx, 7).value)
                obs_inf = _limpiar_str(ws_inf.cell(r_idx, 8).value)

                info_obj = {
                    "fila_informe": r_idx,
                    "fecha_recepcion": _formatear_fecha_vista(f_rec),
                    "fecha_recepcion_iso": _formatear_fecha_iso(f_rec),
                    "estudio": est_nom,
                    "area": area_inf,
                    "periodo": periodo_inf,
                    "fecha_limite": _formatear_fecha_vista(f_lim),
                    "atraso_dias": atraso_dias,
                    "recibido_de": recibido_de,
                    "observaciones": obs_inf,
                }
                lista_informes_recibidos.append(info_obj)
                if est_nom:
                    informes_por_estudio[est_nom] = info_obj

        catalogos["informes_por_estudio"] = informes_por_estudio
        catalogos["lista_informes_recibidos"] = list(reversed(lista_informes_recibidos))
        catalogos["lista_reportes_estudios"] = lista_reportes_estudios

        # 3. Leer hoja principal 'CONSOLIDADO CAUSAS FID'
        registros = []
        conteo_siniestros = {}
        hoy = date.today()

        for fila_idx in range(2, ws.max_row + 1):
            siniestro_raw = _limpiar_str(ws.cell(fila_idx, 2).value)
            rotulado_raw = _limpiar_str(ws.cell(fila_idx, 14).value)
            estudio_raw = _limpiar_str(ws.cell(fila_idx, 23).value)

            if not any([siniestro_raw, rotulado_raw, estudio_raw]):
                continue

            key_sin = "SIN SINIESTRO" if siniestro_raw.upper() == "NO" else siniestro_raw
            conteo_siniestros[key_sin] = conteo_siniestros.get(key_sin, 0) + 1
            id_calculado = f"{key_sin}-{conteo_siniestros[key_sin]}" if key_sin else f"FILA-{fila_idx}"
            id_celda = _limpiar_str(ws.cell(fila_idx, 1).value) or id_calculado

            f_creacion = _parsear_fecha(ws.cell(fila_idx, 3).value)
            f_pjud = _parsear_fecha(ws.cell(fila_idx, 5).value)
            f_notif = _parsear_fecha(ws.cell(fila_idx, 6).value)
            f_asig = _parsear_fecha(ws.cell(fila_idx, 7).value)
            f_term = _parsear_fecha(ws.cell(fila_idx, 8).value)

            moneda = _limpiar_str(ws.cell(fila_idx, 11).value).upper()
            prov_raw = ws.cell(fila_idx, 12).value
            try:
                provision = float(prov_raw) if prov_raw is not None and str(prov_raw).strip() != "" else 0.0
            except (ValueError, TypeError):
                provision = 0.0

            competencia = _limpiar_str(ws.cell(fila_idx, 16).value) or "Civil"
            bloque_legal = clasificar_bloque_legal(competencia)
            motivo_delito = _limpiar_str(ws.cell(fila_idx, 9).value)
            estudio = estudio_raw or "Sin Estudio Asignado"
            estado = _limpiar_str(ws.cell(fila_idx, 24).value) or "En Proceso"
            sentencia = _limpiar_str(ws.cell(fila_idx, 25).value)
            resultado_win = clasificar_sentencia_winrate(sentencia)
            observacion = _limpiar_str(ws.cell(fila_idx, 30).value)

            dias_aa = ws.cell(fila_idx, 27).value
            if not isinstance(dias_aa, (int, float)) and f_asig:
                dias_aa = _dias_habiles_excel(f_asig, f_term or hoy, feriados_np)

            dias_ab = ws.cell(fila_idx, 28).value
            if not isinstance(dias_ab, (int, float)) and f_pjud and f_notif:
                dias_ab = _dias_habiles_excel(f_pjud, f_notif, feriados_np)

            dias_ac = ws.cell(fila_idx, 29).value
            if not isinstance(dias_ac, (int, float)) and f_notif and f_asig:
                dias_ac = _dias_habiles_excel(f_notif, f_asig, feriados_np)

            anio_creacion = str(f_creacion.year) if f_creacion else (_limpiar_str(ws.cell(fila_idx, 33).value) or "Sin fecha")
            mes_creacion = MESES_NOMBRES_LEGAL[f_creacion.month - 1] if f_creacion else "Sin fecha"
            rep_info = reportes_por_id.get(id_celda, {})

            registros.append({
                "fila_excel": fila_idx,
                "id_causa": id_celda,
                "siniestro": siniestro_raw,
                "fecha_creacion": _formatear_fecha_vista(f_creacion),
                "fecha_creacion_iso": _formatear_fecha_iso(f_creacion),
                "calificacion": _limpiar_str(ws.cell(fila_idx, 4).value),
                "fecha_pjud": _formatear_fecha_vista(f_pjud),
                "fecha_pjud_iso": _formatear_fecha_iso(f_pjud),
                "fecha_notif": _formatear_fecha_vista(f_notif),
                "fecha_notif_iso": _formatear_fecha_iso(f_notif),
                "fecha_asig": _formatear_fecha_vista(f_asig),
                "fecha_asig_iso": _formatear_fecha_iso(f_asig),
                "fecha_termino": _formatear_fecha_vista(f_term),
                "fecha_termino_iso": _formatear_fecha_iso(f_term),
                "motivo_delito": motivo_delito,
                "tipo_motivo_delito": clasificar_motivo_o_delito(competencia, motivo_delito),
                "parte": _limpiar_str(ws.cell(fila_idx, 10).value),
                "moneda": moneda,
                "provision": provision,
                "provision_fmt": f"${provision:,.0f}".replace(",", ".") if moneda == "CLP" else (f"{provision:,.1f} UF" if moneda == "UF" else "-"),
                "estado_siniestro": _limpiar_str(ws.cell(fila_idx, 13).value),
                "rotulado": rotulado_raw,
                "asegurado": _limpiar_str(ws.cell(fila_idx, 15).value),
                "competencia": competencia,
                "bloque_legal": bloque_legal,
                "ruc": _limpiar_str(ws.cell(fila_idx, 17).value),
                "rit": _limpiar_str(ws.cell(fila_idx, 18).value),
                "tribunal": _limpiar_str(ws.cell(fila_idx, 19).value),
                "analista": _limpiar_str(ws.cell(fila_idx, 20).value),
                "liquidador": _limpiar_str(ws.cell(fila_idx, 21).value),
                "corredor": _limpiar_str(ws.cell(fila_idx, 22).value),
                "estudio": estudio,
                "estado": estado,
                "sentencia": sentencia or "-",
                "resultado_win": resultado_win,
                "etapa_procesal": _limpiar_str(ws.cell(fila_idx, 26).value),
                "dias_gestion": int(round(dias_aa)) if isinstance(dias_aa, (int, float)) else None,
                "dias_pjud_notif": int(round(dias_ab)) if isinstance(dias_ab, (int, float)) else None,
                "dias_notif_asig": int(round(dias_ac)) if isinstance(dias_ac, (int, float)) else None,
                "observacion": observacion,
                "marca_fidsin": _limpiar_str(ws.cell(fila_idx, 31).value) or "No",
                "etapa_fidsin": _limpiar_str(ws.cell(fila_idx, 32).value) or "Sin Marca en FIDSIN",
                "anio_creacion": anio_creacion,
                "mes_creacion": mes_creacion,
                "ultimo_reporte_estudio": rep_info.get("ultimo_texto", ""),
                "ultimo_periodo_estudio": rep_info.get("ultimo_periodo", ""),
            })
        # 4. Leer hoja 'Próximas Audiencias'
        lista_audiencias = []
        if "Próximas Audiencias" in wb.sheetnames:
            ws_aud = wb["Próximas Audiencias"]
            for r_idx in range(2, ws_aud.max_row + 1):
                f_aud = _parsear_fecha(ws_aud.cell(r_idx, 5).value)
                if not f_aud:
                    continue
                lista_audiencias.append({
                    "siniestro": _limpiar_str(ws_aud.cell(r_idx, 1).value),
                    "id_causa": _limpiar_str(ws_aud.cell(r_idx, 2).value),
                    "ruc": _limpiar_str(ws_aud.cell(r_idx, 3).value),
                    "rit": _limpiar_str(ws_aud.cell(r_idx, 4).value),
                    "fecha_audiencia": _formatear_fecha_vista(f_aud),
                    "fecha_audiencia_iso": _formatear_fecha_iso(f_aud),
                    "estudio": _limpiar_str(ws_aud.cell(r_idx, 6).value),
                    "motivo_audiencia": _limpiar_str(ws_aud.cell(r_idx, 7).value),
                })
        catalogos["lista_audiencias"] = lista_audiencias
        # Rellenar Siniestro, Competencia, Estudio y Estado en 'lista_reportes_estudios'
        # para no depender del valor en caché de las fórmulas INDEX/MATCH de Excel
        mapa_causas_por_id = {r["id_causa"]: r for r in registros}
        for item_rep in lista_reportes_estudios:
            datos_base = mapa_causas_por_id.get(item_rep["id_causa"])
            if datos_base:
                item_rep["siniestro"] = item_rep["siniestro"] or datos_base["siniestro"]
                item_rep["competencia"] = item_rep["competencia"] or datos_base["competencia"]
                item_rep["estudio"] = item_rep["estudio"] or datos_base["estudio"]
                item_rep["estado"] = item_rep["estado"] or datos_base["estado"]

        return registros, catalogos
    finally:
        wb.close()

def registrar_nueva_audiencia(ruta_archivo, post_data):
    """Agrega una nueva audiencia en la hoja 'Próximas Audiencias' en vivo."""
    wb = openpyxl.load_workbook(ruta_archivo)
    try:
        if "Próximas Audiencias" not in wb.sheetnames:
            raise ValueError("El archivo Excel no contiene la hoja 'Próximas Audiencias'.")

        ws = wb["Próximas Audiencias"]
        fila_libre = 2
        while ws.cell(fila_libre, 1).value is not None or ws.cell(fila_libre, 2).value is not None:
            fila_libre += 1

        f_audiencia_str = _limpiar_str(post_data.get("fecha_audiencia"))
        f_audiencia_dt = datetime.strptime(f_audiencia_str, "%Y-%m-%d") if f_audiencia_str else datetime.today()

        ws.cell(fila_libre, 1, _limpiar_str(post_data.get("siniestro")) or None)
        ws.cell(fila_libre, 2, _limpiar_str(post_data.get("id_causa")) or None)
        ws.cell(fila_libre, 3, _limpiar_str(post_data.get("ruc")) or None)
        ws.cell(fila_libre, 4, _limpiar_str(post_data.get("rit")) or None)
        ws.cell(fila_libre, 5, f_audiencia_dt)
        ws.cell(fila_libre, 6, _limpiar_str(post_data.get("estudio")) or None)
        ws.cell(fila_libre, 7, _limpiar_str(post_data.get("motivo_audiencia")) or None)

        wb.save(ruta_archivo)
        return fila_libre
    finally:
        wb.close()

def construir_contexto_causas_legales(registros, catalogos):
    registros_ordenados = list(reversed(registros))

    total_causas = len(registros)
    en_proceso = sum(1 for r in registros if r["estado"].lower() == "en proceso")
    terminadas = sum(1 for r in registros if r["estado"].lower() == "terminada")
    total_clp = sum(r["provision"] for r in registros if r["moneda"] == "CLP")
    total_uf = sum(r["provision"] for r in registros if r["moneda"] == "UF")

    mapa_estudios = {}
    for r in registros:
        est = r["estudio"]
        if est not in mapa_estudios:
            mapa_estudios[est] = {
                "nombre": est,
                "total": 0,
                "en_proceso": 0,
                "terminadas": 0,
                "civil": 0,
                "penal": 0,
                "ganadas": 0,
                "perdidas": 0,
                "con_sentencia": 0,
                "winrate": 0.0,
                "provision_clp": 0.0,
                "provision_uf": 0.0,
                "suma_dias": 0,
                "n_dias": 0,
                "causas": [],
            }
        st = mapa_estudios[est]
        st["total"] += 1
        if r["estado"].lower() == "en proceso":
            st["en_proceso"] += 1
        elif r["estado"].lower() == "terminada":
            st["terminadas"] += 1

        if r["bloque_legal"] == "PENAL":
            st["penal"] += 1
        else:
            st["civil"] += 1

        if r["resultado_win"] == "A_FAVOR":
            st["ganadas"] += 1
            st["con_sentencia"] += 1
        elif r["resultado_win"] == "EN_CONTRA":
            st["perdidas"] += 1
            st["con_sentencia"] += 1

        if r["moneda"] == "CLP":
            st["provision_clp"] += r["provision"]
        elif r["moneda"] == "UF":
            st["provision_uf"] += r["provision"]

        if r["dias_gestion"] is not None:
            st["suma_dias"] += r["dias_gestion"]
            st["n_dias"] += 1

        st["causas"].append({
            "fila_excel": r["fila_excel"],
            "id_causa": r["id_causa"],
            "siniestro": r["siniestro"],
            "rotulado": r["rotulado"],
            "competencia": r["competencia"],
            "bloque_legal": r["bloque_legal"],
            "tribunal": r["tribunal"],
            "estado": r["estado"],
            "sentencia": r["sentencia"],
            "resultado_win": r["resultado_win"],
            "etapa_procesal": r["etapa_procesal"],
            "moneda": r["moneda"],
            "provision": r["provision"],
            "provision_fmt": r["provision_fmt"],
            "dias_gestion": r["dias_gestion"],
            "analista": r["analista"],
            "ultimo_reporte": r["ultimo_reporte_estudio"],
        })

    informes_map = catalogos.get("informes_por_estudio", {})
    estudios_stats = []
    for st in mapa_estudios.values():
        st["winrate"] = round((st["ganadas"] / st["con_sentencia"]) * 100, 1) if st["con_sentencia"] > 0 else 0.0
        st["promedio_dias"] = round(st["suma_dias"] / st["n_dias"], 1) if st["n_dias"] > 0 else 0
        st["provision_clp_fmt"] = f"${st['provision_clp']:,.0f}".replace(",", ".")
        st["provision_uf_fmt"] = f"{st['provision_uf']:,.1f} UF"
        st["informe"] = informes_map.get(st["nombre"])
        estudios_stats.append(st)

    estudios_stats.sort(key=lambda x: x["total"], reverse=True)
    anios_disponibles = sorted({r["anio_creacion"] for r in registros if r["anio_creacion"] != "Sin fecha"})

    return {
        "datos_cargados": True,
        "es_hoja_causas_legales": True,
        "registros_legales": registros_ordenados,
        "estudios_stats": estudios_stats,
        "estudios_stats_json": estudios_stats,
        "legales_analytics_json": registros,
        "informes_recibidos_list": catalogos.get("lista_informes_recibidos", []),
        "reportes_estudios_list": catalogos.get("lista_reportes_estudios", []),
        "kpi_legal_total": total_causas,
        "kpi_legal_proceso": en_proceso,
        "kpi_legal_terminadas": terminadas,
        "kpi_legal_clp_fmt": f"${total_clp:,.0f}".replace(",", "."),
        "kpi_legal_uf_fmt": f"{total_uf:,.1f} UF",
        "anios_legales": anios_disponibles,
        "estudios_catalogo": catalogos["estudios_catalogo"],
        "calificaciones_legal": catalogos["calificaciones_legal"],
        "motivos_legal": catalogos["motivos_legal"],
        "partes_legal": catalogos["partes_legal"],
        "competencias_legal": catalogos["competencias_legal"],
        "estados_legal": catalogos["estados_legal"],
        "sentencias_legal": SENTENCIAS_CATALOGO_LEGAL,
        "tribunales_catalogo": catalogos["tribunales_catalogo"],
        "audiencias_list": catalogos.get("lista_audiencias", []),
    }


def guardar_fila_causas_legales(ruta_archivo, nombre_hoja, fila_destino, post_data, es_nuevo=False):
    wb = openpyxl.load_workbook(ruta_archivo)
    try:
        ws = wb[nombre_hoja]

        if es_nuevo:
            fila_destino = ws.max_row + 1
            while fila_destino > 2 and not any(ws.cell(fila_destino - 1, c).value for c in (2, 14, 23)):
                fila_destino -= 1

        def _parse_input_date(key):
            val = _limpiar_str(post_data.get(key, ""))
            if not val:
                return None
            try:
                return datetime.strptime(val, "%Y-%m-%d")
            except ValueError:
                return None

        siniestro = _limpiar_str(post_data.get("siniestro")) or "NO"
        moneda = _limpiar_str(post_data.get("moneda")).upper()
        prov_str = _limpiar_str(post_data.get("provision"))
        try:
            provision_val = float(prov_str) if prov_str != "" else None
        except ValueError:
            provision_val = None

        ws.cell(fila_destino, 2, siniestro)
        ws.cell(fila_destino, 3, _parse_input_date("fecha_creacion"))
        ws.cell(fila_destino, 4, _limpiar_str(post_data.get("calificacion")) or None)
        ws.cell(fila_destino, 5, _parse_input_date("fecha_pjud"))
        ws.cell(fila_destino, 6, _parse_input_date("fecha_notif"))
        ws.cell(fila_destino, 7, _parse_input_date("fecha_asig"))
        ws.cell(fila_destino, 8, _parse_input_date("fecha_termino"))
        ws.cell(fila_destino, 9, _limpiar_str(post_data.get("motivo_delito")) or None)
        ws.cell(fila_destino, 10, _limpiar_str(post_data.get("parte")) or None)
        ws.cell(fila_destino, 11, moneda if moneda in ("CLP", "UF") else None)
        ws.cell(fila_destino, 12, provision_val)
        ws.cell(fila_destino, 13, _limpiar_str(post_data.get("estado_siniestro")) or None)
        ws.cell(fila_destino, 14, _limpiar_str(post_data.get("rotulado")) or None)
        ws.cell(fila_destino, 15, _limpiar_str(post_data.get("asegurado")) or None)
        ws.cell(fila_destino, 16, _limpiar_str(post_data.get("competencia")) or "Civil")
        ws.cell(fila_destino, 17, _limpiar_str(post_data.get("ruc")) or None)
        ws.cell(fila_destino, 18, _limpiar_str(post_data.get("rit")) or None)
        ws.cell(fila_destino, 19, _limpiar_str(post_data.get("tribunal")) or None)
        ws.cell(fila_destino, 20, _limpiar_str(post_data.get("analista")) or None)
        ws.cell(fila_destino, 21, _limpiar_str(post_data.get("liquidador")) or None)
        ws.cell(fila_destino, 22, _limpiar_str(post_data.get("corredor")) or None)
        ws.cell(fila_destino, 23, _limpiar_str(post_data.get("estudio")) or None)
        ws.cell(fila_destino, 24, _limpiar_str(post_data.get("estado")) or "En Proceso")
        ws.cell(fila_destino, 25, _limpiar_str(post_data.get("sentencia")) or None)
        ws.cell(fila_destino, 26, _limpiar_str(post_data.get("etapa_procesal")) or None)
        ws.cell(fila_destino, 30, _limpiar_str(post_data.get("observacion")) or None)
        ws.cell(fila_destino, 31, _limpiar_str(post_data.get("marca_fidsin")) or "No")
        ws.cell(fila_destino, 32, _limpiar_str(post_data.get("etapa_fidsin")) or "Sin Marca en FIDSIN")

        # Fórmulas nativas de la tabla Controvertidos
        ws.cell(
            fila_destino, 1,
            '=IF(Controvertidos[[#This Row],[Siniestro]]="","",IF(TRIM(Controvertidos[[#This Row],[Siniestro]])="NO","SIN SINIESTRO",Controvertidos[[#This Row],[Siniestro]])&"-"&COUNTIF(INDEX(Controvertidos[Siniestro],1):Controvertidos[[#This Row],[Siniestro]],Controvertidos[[#This Row],[Siniestro]]))'
        )
        ws.cell(
            fila_destino, 27,
            '=IF(Controvertidos[[#This Row],[FECHA ASIGNACIÓN]]="","",IF(IF(Controvertidos[[#This Row],[FECHA TERMINO]]="",TODAY(),Controvertidos[[#This Row],[FECHA TERMINO]])>=Controvertidos[[#This Row],[FECHA ASIGNACIÓN]],NETWORKDAYS(Controvertidos[[#This Row],[FECHA ASIGNACIÓN]],IF(Controvertidos[[#This Row],[FECHA TERMINO]]="",TODAY(),Controvertidos[[#This Row],[FECHA TERMINO]]),Lista_Feriados)-1,NETWORKDAYS(Controvertidos[[#This Row],[FECHA ASIGNACIÓN]],IF(Controvertidos[[#This Row],[FECHA TERMINO]]="",TODAY(),Controvertidos[[#This Row],[FECHA TERMINO]]),Lista_Feriados)+1))'
        )
        ws.cell(
            fila_destino, 28,
            '=IF(OR(Controvertidos[[#This Row],[Fecha ingreso a PJUD]]="",Controvertidos[[#This Row],[Fecha Notificación]]=""),"",IF(Controvertidos[[#This Row],[Fecha Notificación]]>=Controvertidos[[#This Row],[Fecha ingreso a PJUD]],NETWORKDAYS(Controvertidos[[#This Row],[Fecha ingreso a PJUD]],Controvertidos[[#This Row],[Fecha Notificación]],Lista_Feriados)-1,NETWORKDAYS(Controvertidos[[#This Row],[Fecha ingreso a PJUD]],Controvertidos[[#This Row],[Fecha Notificación]],Lista_Feriados)+1))'
        )
        ws.cell(
            fila_destino, 29,
            '=IF(OR(Controvertidos[[#This Row],[Fecha Notificación]]="",Controvertidos[[#This Row],[FECHA ASIGNACIÓN]]=""),"",IF(Controvertidos[[#This Row],[FECHA ASIGNACIÓN]]>=Controvertidos[[#This Row],[Fecha Notificación]],NETWORKDAYS(Controvertidos[[#This Row],[Fecha Notificación]],Controvertidos[[#This Row],[FECHA ASIGNACIÓN]],Lista_Feriados)-1,NETWORKDAYS(Controvertidos[[#This Row],[Fecha Notificación]],Controvertidos[[#This Row],[FECHA ASIGNACIÓN]],Lista_Feriados)+1))'
        )
        ws.cell(
            fila_destino, 33,
            '=IF(ISNUMBER(Controvertidos[[#This Row],[Fecha Creación]]),IF(Controvertidos[[#This Row],[Fecha Creación]]<3000,Controvertidos[[#This Row],[Fecha Creación]],YEAR(Controvertidos[[#This Row],[Fecha Creación]])),"Sin fecha")'
        )
        ws.cell(
            fila_destino, 34,
            '=IF(AND(ISNUMBER(Controvertidos[[#This Row],[Fecha Creación]]),Controvertidos[[#This Row],[Fecha Creación]]>=3000),CHOOSE(MONTH(Controvertidos[[#This Row],[Fecha Creación]]),"01 Enero","02 Febrero","03 Marzo","04 Abril","05 Mayo","06 Junio","07 Julio","08 Agosto","09 Septiembre","10 Octubre","11 Noviembre","12 Diciembre"),"Sin fecha")'
        )
        ws.cell(
            fila_destino, 35,
            '=IF(TRIM(Controvertidos[[#This Row],[Siniestro]])="NO","Sin siniestro (NO)","Con siniestro")'
        )

        if "Controvertidos" in ws.tables:
            max_fila_tabla = max(ws.max_row, fila_destino)
            ws.tables["Controvertidos"].ref = f"A1:AI{max_fila_tabla}"

        # Sincronizar nueva fila en la hoja 'Reportes estudios'
        if es_nuevo and "Reportes estudios" in wb.sheetnames:
            ws_rep = wb["Reportes estudios"]
            nueva_r = ws_rep.max_row + 1
            while nueva_r > 3 and not ws_rep.cell(nueva_r - 1, 1).value:
                nueva_r -= 1
            conteo_sin = sum(
                1 for r in range(2, fila_destino + 1)
                if _limpiar_str(ws.cell(r, 2).value).upper() == siniestro.upper()
            )
            prefijo_id = "SIN SINIESTRO" if siniestro.upper() == "NO" else siniestro
            nuevo_id = f"{prefijo_id}-{conteo_sin}"
            ws_rep.cell(nueva_r, 1, nuevo_id)
            ws_rep.cell(nueva_r, 2, f'=IFERROR(INDEX(cl_Sin,MATCH($A{nueva_r},cl_ID,0)),"")')
            ws_rep.cell(nueva_r, 3, f'=IFERROR(INDEX(cl_Comp,MATCH($A{nueva_r},cl_ID,0)),"")')
            ws_rep.cell(nueva_r, 4, f'=IFERROR(INDEX(cl_Estudio,MATCH($A{nueva_r},cl_ID,0)),"")')
            ws_rep.cell(nueva_r, 5, f'=IFERROR(INDEX(cl_Estado,MATCH($A{nueva_r},cl_ID,0)),"")')

        wb.save(ruta_archivo)
        return fila_destino
    finally:
        wb.close()


def registrar_informe_recibido(ruta_archivo, post_data):
    """Agrega un nuevo registro en la hoja 'Informes recibidos' preservando las fórmulas de plazo y atraso."""
    wb = openpyxl.load_workbook(ruta_archivo)
    try:
        if "Informes recibidos" not in wb.sheetnames:
            raise ValueError("El archivo Excel no contiene la hoja 'Informes recibidos'.")

        ws = wb["Informes recibidos"]
        fila_libre = 4
        while ws.cell(fila_libre, 1).value is not None or ws.cell(fila_libre, 2).value is not None:
            fila_libre += 1

        f_rec_str = _limpiar_str(post_data.get("fecha_recepcion"))
        f_rec_dt = datetime.strptime(f_rec_str, "%Y-%m-%d") if f_rec_str else datetime.today()

        ws.cell(fila_libre, 1, f_rec_dt)
        ws.cell(fila_libre, 2, _limpiar_str(post_data.get("estudio")))
        ws.cell(fila_libre, 3, _limpiar_str(post_data.get("area_informada")) or "Todas")
        ws.cell(fila_libre, 4, _limpiar_str(post_data.get("periodo_informa")) or "Octubre 2026")
        ws.cell(
            fila_libre, 5,
            f'=IF(D{fila_libre}="","",IFERROR(WORKDAY(DATE(VALUE(RIGHT(D{fila_libre},4)),MATCH(LEFT(D{fila_libre},FIND(" ",D{fila_libre})-1),{{"Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"}},0),1)-1,10,Lista_Feriados),""))'
        )
        ws.cell(
            fila_libre, 6,
            f'=IF(OR(A{fila_libre}="",E{fila_libre}=""),"",IF(A{fila_libre}<=E{fila_libre},0,NETWORKDAYS(E{fila_libre},A{fila_libre},Feriados)-1))'
        )
        ws.cell(fila_libre, 7, _limpiar_str(post_data.get("recibido_de")) or None)
        ws.cell(fila_libre, 8, _limpiar_str(post_data.get("observaciones_informe")) or None)

        wb.save(ruta_archivo)
        return fila_libre
    finally:
        wb.close()


def guardar_reporte_bimestral_estudio(ruta_archivo, post_data):
    """Actualiza los reportes bimestrales de una causa en la hoja 'Reportes estudios'."""
    wb = openpyxl.load_workbook(ruta_archivo)
    try:
        if "Reportes estudios" not in wb.sheetnames:
            raise ValueError("El archivo Excel no contiene la hoja 'Reportes estudios'.")

        ws = wb["Reportes estudios"]
        fila_rep = int(post_data.get("fila_reporte"))

        for col_num, key_name, _ in COLUMNAS_BIMESTRES_REPORTES:
            if key_name in post_data:
                val = _limpiar_str(post_data.get(key_name))
                ws.cell(fila_rep, col_num, val if val else None)

        wb.save(ruta_archivo)
        return fila_rep
    finally:
        wb.close()

# Añadir al final de core/services_legal.py

def leer_hoja_querellas_sisgen(ruta_archivo, nombre_hoja):
    """
    Lee la hoja 'QUERELLAS VS SISGEN' extrayendo las 9 columnas con encabezado en texto amarillo:
    Siniestro (B), Motivo - Delito (C), ROTULADO (E), Nombre Asegurado (F),
    RUT (G), Ultimo siniestro SISGEN (H), Fecha siniestro SISGEN (I), Cía (J) y Observaciones (K).
    """
    wb = openpyxl.load_workbook(ruta_archivo, data_only=True)
    try:
        catalogos = cargar_catalogos_hojas_auxiliares(wb)
        ws = wb[nombre_hoja]

        registros = []
        conteo_siniestros = {}
        motivos_set = set(catalogos.get("motivos_legal", []))
        cias_set = set()

        for fila_idx in range(2, ws.max_row + 1):
            siniestro_raw = _limpiar_str(ws.cell(fila_idx, 2).value).replace(".0", "")
            motivo_delito = _limpiar_str(ws.cell(fila_idx, 3).value)
            rotulado = _limpiar_str(ws.cell(fila_idx, 5).value)
            asegurado = _limpiar_str(ws.cell(fila_idx, 6).value)

            if not any([siniestro_raw, motivo_delito, rotulado, asegurado]):
                continue

            key_sin = "SIN SINIESTRO" if siniestro_raw.upper() == "NO" else siniestro_raw
            conteo_siniestros[key_sin] = conteo_siniestros.get(key_sin, 0) + 1
            id_calculado = f"{key_sin}-{conteo_siniestros[key_sin]}" if key_sin else f"FILA-{fila_idx}"
            id_celda = _limpiar_str(ws.cell(fila_idx, 1).value) or id_calculado

            parte = _limpiar_str(ws.cell(fila_idx, 4).value)
            rut = _limpiar_str(ws.cell(fila_idx, 7).value)
            ultimo_sin_sisgen = _limpiar_str(ws.cell(fila_idx, 8).value).replace(".0", "")
            f_sisgen = _parsear_fecha(ws.cell(fila_idx, 9).value)
            cia = _limpiar_str(ws.cell(fila_idx, 10).value)
            observaciones = _limpiar_str(ws.cell(fila_idx, 11).value)

            tiene_cruce_sisgen = "SI" if any([rut, ultimo_sin_sisgen, f_sisgen, cia]) else "NO"

            if motivo_delito:
                motivos_set.add(motivo_delito)
            if cia:
                cias_set.add(cia)

            registros.append({
                "fila_excel": fila_idx,
                "id_causa": id_celda,
                "siniestro": siniestro_raw,
                "motivo_delito": motivo_delito,
                "parte": parte,
                "rotulado": rotulado,
                "asegurado": asegurado,
                "rut": rut,
                "ultimo_siniestro_sisgen": ultimo_sin_sisgen,
                "fecha_siniestro_sisgen": _formatear_fecha_vista(f_sisgen),
                "fecha_siniestro_sisgen_iso": _formatear_fecha_iso(f_sisgen),
                "cia": cia,
                "observaciones": observaciones,
                "tiene_cruce_sisgen": tiene_cruce_sisgen,
            })

        catalogos["motivos_sisgen"] = sorted(motivos_set)
        catalogos["cias_sisgen"] = sorted(cias_set)
        return registros, catalogos
    finally:
        wb.close()


def construir_contexto_querellas_sisgen(registros, catalogos):
    """Construye los KPIs y listas desplegables para la interfaz de QUERELLAS VS SISGEN."""
    total_registros = len(registros)
    con_sisgen = sum(1 for r in registros if r["tiene_cruce_sisgen"] == "SI")
    sin_sisgen = total_registros - con_sisgen

    conteo_cias = {}
    for r in registros:
        if r["cia"]:
            conteo_cias[r["cia"]] = conteo_cias.get(r["cia"], 0) + 1
    top_cia = max(conteo_cias.items(), key=lambda x: x[1])[0] if conteo_cias else "Sin registros"

    return {
        "datos_cargados": True,
        "es_hoja_querellas_sisgen": True,
        "registros_sisgen": list(reversed(registros)),
        "kpi_sisgen_total": total_registros,
        "kpi_sisgen_con_cruce": con_sisgen,
        "kpi_sisgen_sin_cruce": sin_sisgen,
        "kpi_sisgen_top_cia": top_cia,
        "motivos_sisgen": catalogos.get("motivos_sisgen", []),
        "cias_sisgen": catalogos.get("cias_sisgen", []),
        "partes_legal": catalogos.get("partes_legal", ["Querellante", "Demandado", "Recupero", "RC No Aplica", "Querellado"]),
    }


def guardar_fila_querellas_sisgen(ruta_archivo, nombre_hoja, fila_destino, post_data, es_nuevo=False):
    """Crea o edita en vivo un registro en la hoja 'QUERELLAS VS SISGEN' preservando la tabla Controvertidos5."""
    wb = openpyxl.load_workbook(ruta_archivo)
    try:
        ws = wb[nombre_hoja]
        if es_nuevo:
            fila_destino = ws.max_row + 1
            while fila_destino > 2 and not any(ws.cell(fila_destino - 1, c).value for c in (2, 3, 5, 6)):
                fila_destino -= 1

        siniestro = _limpiar_str(post_data.get("siniestro")) or "NO"
        f_sisgen_str = _limpiar_str(post_data.get("fecha_siniestro_sisgen"))
        try:
            f_sisgen_dt = datetime.strptime(f_sisgen_str, "%Y-%m-%d") if f_sisgen_str else None
        except ValueError:
            f_sisgen_dt = None

        ult_sin_raw = _limpiar_str(post_data.get("ultimo_siniestro_sisgen"))
        ult_sin_val = int(ult_sin_raw) if ult_sin_raw.isdigit() else (ult_sin_raw or None)

        # Fórmula nativa para Columna A (ID)
        nombre_tabla = next(iter(ws.tables.keys()), "Controvertidos5")
        ws.cell(
            fila_destino, 1,
            f'=IF({nombre_tabla}[[#This Row],[Siniestro]]="","",IF(TRIM({nombre_tabla}[[#This Row],[Siniestro]])="NO","SIN SINIESTRO",{nombre_tabla}[[#This Row],[Siniestro]])&"-"&COUNTIF(INDEX({nombre_tabla}[Siniestro],1):{nombre_tabla}[[#This Row],[Siniestro]],{nombre_tabla}[[#This Row],[Siniestro]]))'
        )

        # Columnas en texto amarillo (B, C, E, F, G, H, I, J, K) + Parte (D)
        ws.cell(fila_destino, 2, siniestro)
        ws.cell(fila_destino, 3, _limpiar_str(post_data.get("motivo_delito")) or None)
        ws.cell(fila_destino, 4, _limpiar_str(post_data.get("parte")) or ws.cell(fila_destino, 4).value or "Querellante")
        ws.cell(fila_destino, 5, _limpiar_str(post_data.get("rotulado")) or None)
        ws.cell(fila_destino, 6, _limpiar_str(post_data.get("asegurado")) or None)
        ws.cell(fila_destino, 7, _limpiar_str(post_data.get("rut")) or None)
        ws.cell(fila_destino, 8, ult_sin_val)
        ws.cell(fila_destino, 9, f_sisgen_dt)
        if f_sisgen_dt:
            ws.cell(fila_destino, 9).number_format = "dd-mm-yyyy"
        ws.cell(fila_destino, 10, _limpiar_str(post_data.get("cia")) or None)
        ws.cell(fila_destino, 11, _limpiar_str(post_data.get("observaciones")) or None)

        if nombre_tabla in ws.tables:
            max_fila_tabla = max(ws.max_row, fila_destino)
            ws.tables[nombre_tabla].ref = f"A1:K{max_fila_tabla}"

        wb.save(ruta_archivo)
        return fila_destino
    finally:
        wb.close()