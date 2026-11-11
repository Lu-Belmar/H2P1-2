# core/views.py
import logging
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from openpyxl import load_workbook

from django.contrib import messages
from django.http import FileResponse
from django.shortcuts import redirect, render
from django.views import View

from .excel_cache import (
    invalidar_cache_archivo,
    obtener_contexto_cacheado,
    obtener_hojas_cacheadas,
)
from .constants import (
    ESTADOS_CATALOGO,
    LEGAL_CATALOGO,
    MOTIVOS_CATALOGO,
    RAMOS_CATALOGO,
)
from .forms import CargaExcelForm, EditarFilaForm
from .services import (
    construir_contexto_consolidado,
    guardar_fila_consolidado,
    leer_hoja_consolidado,
    leer_hoja_generica,
)
from .services_legal import (
    construir_contexto_causas_legales,
    construir_contexto_querellas_sisgen,
    guardar_fila_causas_legales,
    guardar_fila_querellas_sisgen,
    guardar_reporte_bimestral_estudio,
    leer_hoja_causas_legales,
    leer_hoja_querellas_sisgen,
    registrar_informe_recibido,
    registrar_nueva_audiencia,
)

logger = logging.getLogger(__name__)

HOJAS_CONSOLIDADO = {"tabla consolidado", "consolidados", "consolidado"}
HOJAS_CAUSAS_LEGALES = {"consolidado causas fid", "controvertidos"}
HOJAS_QUERELLAS_SISGEN = {"querellas vs sisgen", "controvertidos5"}
HOJA_POR_DEFECTO = "Tabla consolidado"

CATALOGOS_CONTEXTO = {
    "motivos_catalogo": MOTIVOS_CATALOGO,
    "estados_catalogo": ESTADOS_CATALOGO,
    "ramos_catalogo": RAMOS_CATALOGO,
    "legal_catalogo": LEGAL_CATALOGO,
}


def seleccionar_archivos_nativos(ruta_inicial=None):
    """Abre el explorador nativo de Windows permitiendo elegir UNO o VARIOS archivos Excel."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    rutas = filedialog.askopenfilenames(
        initialdir=ruta_inicial or os.path.expanduser("~"),
        title="Seleccionar uno o varios archivos Excel (Local o SharePoint)",
        filetypes=[("Archivos Excel", "*.xlsx *.xlsm *.xls *.xlsb")],
    )
    root.destroy()
    return [str(Path(r).resolve()) for r in rutas] if rutas else []


class DashboardView(View):
    template_name = "core/dashboard.html"

    def _notificar(self, request, exito=None, error=None):
        if exito:
            messages.success(request, exito)
            request.session["_flash_exito"] = exito
        if error:
            messages.error(request, error)
            request.session["_flash_error"] = error

    def _obtener_hojas_excel(self, ruta_archivo):
        def _leer_hojas(ruta):
            wb = load_workbook(filename=ruta, read_only=True)
            try:
                return wb.sheetnames
            finally:
                wb.close()

        return obtener_hojas_cacheadas(ruta_archivo, _leer_hojas)

    def _detectar_hoja_y_tipo(self, sheet_names):
        """Determina la hoja principal por defecto y el tipo de icono para la tarjeta."""
        hojas_lower = {s.strip().lower(): s for s in sheet_names}
        for h_leg in HOJAS_CAUSAS_LEGALES:
            if h_leg in hojas_lower:
                return hojas_lower[h_leg], "LEGAL"
        for h_sis in HOJAS_QUERELLAS_SISGEN:
            if h_sis in hojas_lower:
                return hojas_lower[h_sis], "LEGAL"
        for h_cmf in HOJAS_CONSOLIDADO:
            if h_cmf in hojas_lower:
                return hojas_lower[h_cmf], "CMF"
        hoja_def = sheet_names[0] if sheet_names else ""
        return hoja_def, "EXCEL"

    def _activar_item_galeria(self, request, item):
        request.session.update({
            "ruta_archivo": item["ruta"],
            "nombre_archivo": item["nombre"],
            "sheet_names": item["sheet_names"],
            "hoja_seleccionada": item["hoja_seleccionada"],
        })

    def _registrar_en_galeria(self, request, rutas_nuevas):
        """Agrega uno o varios archivos a la galería en sesión y activa el último seleccionado."""
        galeria = request.session.get("archivos_vinculados", [])
        mapa_galeria = {item["ruta"]: item for item in galeria if Path(item["ruta"]).is_file()}

        ultimo_valido = None
        errores = []

        for r_str in rutas_nuevas:
            p = Path(r_str)
            if not p.is_file():
                errores.append(f"No existe: {r_str}")
                continue
            try:
                sheets = self._obtener_hojas_excel(str(p))
                hoja_def, tipo_mod = self._detectar_hoja_y_tipo(sheets)
                item_previo = mapa_galeria.get(str(p), {})
                hoja_activa = item_previo.get("hoja_seleccionada")
                if not hoja_activa or hoja_activa not in sheets:
                    hoja_activa = hoja_def

                item = {
                    "ruta": str(p),
                    "nombre": p.name,
                    "tipo": tipo_mod,  # 'CMF', 'LEGAL' o 'EXCEL'
                    "sheet_names": sheets,
                    "hoja_seleccionada": hoja_activa,
                }
                mapa_galeria[str(p)] = item
                ultimo_valido = item
            except Exception as e:
                logger.exception("Error leyendo archivo %s", r_str)
                errores.append(f"{p.name}: {e}")

        nueva_galeria = list(mapa_galeria.values())
        request.session["archivos_vinculados"] = nueva_galeria

        if ultimo_valido:
            self._activar_item_galeria(request, ultimo_valido)
            self._notificar(
                request,
                exito=f"Se cargaron {len(rutas_nuevas)} archivo(s). Activo: {ultimo_valido['nombre']}",
            )
        if errores:
            self._notificar(request, error=" | ".join(errores))

    def _handle_vincular_archivo(self, request, explorar=False):
        ruta_actual = request.session.get("ruta_archivo")
        if explorar:
            carpeta_inicial = str(Path(ruta_actual).parent) if ruta_actual else None
            rutas = seleccionar_archivos_nativos(carpeta_inicial)
            if not rutas:
                return
        else:
            raw = request.POST.get("ruta_directa", "").strip().strip('"')
            rutas = [raw] if raw else []

        if not rutas:
            self._notificar(request, error="Debes seleccionar al menos un archivo válido.")
            return

        self._registrar_en_galeria(request, rutas)

    def _handle_seleccionar_archivo_galeria(self, request):
        """Cambia instantáneamente entre los archivos subidos usando la RAM."""
        ruta_elegida = request.POST.get("ruta_elegida", "")
        galeria = request.session.get("archivos_vinculados", [])

        for item in galeria:
            if item["ruta"] == ruta_elegida:
                if Path(ruta_elegida).is_file():
                    sheets = self._obtener_hojas_excel(ruta_elegida)
                    item["sheet_names"] = sheets
                    if item["hoja_seleccionada"] not in sheets:
                        item["hoja_seleccionada"], item["tipo"] = self._detectar_hoja_y_tipo(sheets)
                    request.session["archivos_vinculados"] = galeria
                    self._activar_item_galeria(request, item)
                else:
                    self._notificar(request, error=f"El archivo ya no se encuentra en: {ruta_elegida}")
                break

    def _handle_quitar_archivo_galeria(self, request):
        ruta_quitar = request.POST.get("ruta_quitar", "")
        galeria = [
            item for item in request.session.get("archivos_vinculados", [])
            if item["ruta"] != ruta_quitar
        ]
        request.session["archivos_vinculados"] = galeria

        if request.session.get("ruta_archivo") == ruta_quitar:
            if galeria:
                self._activar_item_galeria(request, galeria[-1])
            else:
                for k in ("ruta_archivo", "nombre_archivo", "sheet_names", "hoja_seleccionada"):
                    request.session.pop(k, None)

    def _handle_recargar_en_vivo(self, request, ruta_archivo):
        """El botón 'Recargar datos' fuerza una lectura limpia desde el disco."""
        if ruta_archivo and Path(ruta_archivo).is_file():
            try:
                invalidar_cache_archivo(ruta_archivo)
                sheets = self._obtener_hojas_excel(ruta_archivo)
                request.session["sheet_names"] = sheets
                self._notificar(request, exito="Datos recargados en vivo desde el archivo original.")
            except Exception as e:
                self._notificar(request, error=f"No se pudo recargar el archivo: {e}")

    def _handle_cambiar_hoja(self, request):
        nueva_hoja = request.POST.get("hoja_seleccionada", "")
        request.session["hoja_seleccionada"] = nueva_hoja
        ruta_actual = request.session.get("ruta_archivo")
        galeria = request.session.get("archivos_vinculados", [])
        for item in galeria:
            if item["ruta"] == ruta_actual:
                item["hoja_seleccionada"] = nueva_hoja
                break
        request.session["archivos_vinculados"] = galeria

    def _handle_crear_registro(self, request, ruta_archivo, hoja_seleccionada):
        try:
            nueva = guardar_fila_consolidado(
                ruta_archivo, hoja_seleccionada, None, request.POST, es_nuevo=True
            )
            invalidar_cache_archivo(ruta_archivo)
            self._notificar(
                request,
                exito=f"Nuevo registro creado y guardado en vivo en la fila #{nueva} de '{hoja_seleccionada}'.",
            )
        except PermissionError:
            nombre = Path(ruta_archivo).name
            self._notificar(request, error=f"No se pudo guardar porque '{nombre}' está abierto en Excel.")
        except Exception as e:
            logger.exception("Error creando registro en Excel")
            self._notificar(request, error=f"Error al crear el registro: {e}")

    def _handle_editar_registro(self, request, ruta_archivo, hoja_seleccionada):
        form_fila = EditarFilaForm(request.POST)
        if not form_fila.is_valid():
            primer_error = next(iter(form_fila.errors.values()))[0]
            self._notificar(request, error=f"Error al modificar el registro: {primer_error}")
            return

        fila_num = form_fila.cleaned_data["fila_excel"]
        try:
            guardar_fila_consolidado(
                ruta_archivo, hoja_seleccionada, fila_num, request.POST, es_nuevo=False
            )
            invalidar_cache_archivo(ruta_archivo)
            self._notificar(request, exito=f"Registro de la fila #{fila_num} actualizado y guardado en vivo.")
        except PermissionError:
            nombre = Path(ruta_archivo).name
            self._notificar(request, error=f"No se pudo guardar porque '{nombre}' está abierto en Excel.")
        except Exception as e:
            logger.exception("Error editando fila %s en Excel", fila_num)
            self._notificar(request, error=f"Error al modificar el registro: {e}")

    def _handle_guardar_causa_legal(self, request, ruta_archivo, hoja_seleccionada, es_nuevo=False):
        fila_num = None if es_nuevo else int(request.POST.get("fila_excel"))
        try:
            fila_res = guardar_fila_causas_legales(
                ruta_archivo, hoja_seleccionada, fila_num, request.POST, es_nuevo=es_nuevo
            )
            invalidar_cache_archivo(ruta_archivo)
            accion_txt = "creada" if es_nuevo else "actualizada"
            self._notificar(request, exito=f"Causa legal {accion_txt} y guardada en vivo en la fila #{fila_res}.")
        except PermissionError:
            nombre = Path(ruta_archivo).name
            self._notificar(request, error=f"No se pudo guardar porque '{nombre}' está abierto en Excel.")
        except Exception as e:
            logger.exception("Error guardando causa legal")
            self._notificar(request, error=f"Error al guardar la causa legal: {e}")

    def _handle_guardar_querella_sisgen(self, request, ruta_archivo, hoja_seleccionada, es_nuevo=False):
        fila_num = None if es_nuevo else int(request.POST.get("fila_excel"))
        try:
            fila_res = guardar_fila_querellas_sisgen(
                ruta_archivo, hoja_seleccionada, fila_num, request.POST, es_nuevo=es_nuevo
            )
            invalidar_cache_archivo(ruta_archivo)
            accion_txt = "creado" if es_nuevo else "actualizado"
            self._notificar(request, exito=f"Registro SISGEN {accion_txt} y guardado en vivo en la fila #{fila_res}.")
        except PermissionError:
            nombre = Path(ruta_archivo).name
            self._notificar(request, error=f"No se pudo guardar porque '{nombre}' está abierto en Excel.")
        except Exception as e:
            logger.exception("Error guardando en QUERELLAS VS SISGEN")
            self._notificar(request, error=f"Error al guardar registro SISGEN: {e}")

    def post(self, request):
        """Procesa cualquier acción de escritura en vivo y redirige con PRG (Post/Redirect/Get)."""
        accion = request.POST.get("accion", "")
        ruta_archivo = request.session.get("ruta_archivo")
        hoja_seleccionada = request.session.get("hoja_seleccionada", "")

        if accion == "explorar_archivo":
            self._handle_vincular_archivo(request, explorar=True)
        elif accion == "vincular_ruta":
            self._handle_vincular_archivo(request, explorar=False)
        elif accion == "seleccionar_archivo_galeria":
            self._handle_seleccionar_archivo_galeria(request)
        elif accion == "quitar_archivo_galeria":
            self._handle_quitar_archivo_galeria(request)
        elif accion == "recargar_en_vivo":
            self._handle_recargar_en_vivo(request, ruta_archivo)
        elif accion == "cambiar_hoja":
            self._handle_cambiar_hoja(request)
        elif ruta_archivo and hoja_seleccionada:
            if accion == "crear_registro":
                self._handle_crear_registro(request, ruta_archivo, hoja_seleccionada)
            elif accion == "editar_registro":
                self._handle_editar_registro(request, ruta_archivo, hoja_seleccionada)
            elif accion == "crear_causa_legal":
                self._handle_guardar_causa_legal(request, ruta_archivo, hoja_seleccionada, es_nuevo=True)
            elif accion == "editar_causa_legal":
                self._handle_guardar_causa_legal(request, ruta_archivo, hoja_seleccionada, es_nuevo=False)
            elif accion == "crear_querella_sisgen":
                self._handle_guardar_querella_sisgen(request, ruta_archivo, hoja_seleccionada, es_nuevo=True)
            elif accion == "editar_querella_sisgen":
                self._handle_guardar_querella_sisgen(request, ruta_archivo, hoja_seleccionada, es_nuevo=False)
            elif accion == "registrar_informe_estudio":
                try:
                    f_inf = registrar_informe_recibido(ruta_archivo, request.POST)
                    invalidar_cache_archivo(ruta_archivo)
                    self._notificar(request, exito=f"Recepción registrada en vivo (Fila #{f_inf} de 'Informes recibidos').")
                except PermissionError:
                    self._notificar(request, error="No se pudo guardar porque el archivo está abierto en Excel.")
                except Exception as e:
                    self._notificar(request, error=f"Error al registrar informe: {e}")
            elif accion == "guardar_reporte_bimestral":
                try:
                    f_rep = guardar_reporte_bimestral_estudio(ruta_archivo, request.POST)
                    invalidar_cache_archivo(ruta_archivo)
                    self._notificar(request, exito=f"Reporte bimestral actualizado en vivo (Fila #{f_rep} de 'Reportes estudios').")
                except PermissionError:
                    self._notificar(request, error="No se pudo guardar porque el archivo está abierto en Excel.")
                except Exception as e:
                    self._notificar(request, error=f"Error al guardar reporte bimestral: {e}")
            elif accion == "registrar_audiencia_agenda":
                try:
                    f_aud = registrar_nueva_audiencia(ruta_archivo, request.POST)
                    invalidar_cache_archivo(ruta_archivo)
                    self._notificar(request, exito=f"Audiencia agendada correctamente en la hoja 'Próximas Audiencias' (Fila #{f_aud}).")
                except PermissionError:
                    self._notificar(request, error="No se pudo guardar porque el archivo está abierto en Excel.")
                except Exception as e:
                    self._notificar(request, error=f"Error al agendar audiencia: {e}")

        return redirect(request.path)

    def get(self, request):
        ruta_archivo = request.session.get("ruta_archivo")
        nombre_archivo = request.session.get("nombre_archivo")
        sheet_names = request.session.get("sheet_names", [])
        hoja_seleccionada = request.session.get("hoja_seleccionada", "")
        archivos_vinculados = request.session.get("archivos_vinculados", [])

        mensaje_exito = request.session.pop("_flash_exito", None)
        error = request.session.pop("_flash_error", None)

        archivo_cargado = bool(ruta_archivo and Path(ruta_archivo).is_file())
        hoja_norm = hoja_seleccionada.strip().lower()
        es_hoja_consolidado = hoja_norm in HOJAS_CONSOLIDADO
        es_hoja_causas_legales = hoja_norm in HOJAS_CAUSAS_LEGALES
        es_hoja_querellas_sisgen = hoja_norm in HOJAS_QUERELLAS_SISGEN

        contexto = {
            "form": CargaExcelForm(),
            "archivos_vinculados": archivos_vinculados,
            "archivo_cargado": archivo_cargado,
            "ruta_archivo": ruta_archivo or "",
            "nombre_archivo": nombre_archivo,
            "sheet_names": sheet_names,
            "hoja_seleccionada": hoja_seleccionada,
            "dropdown_disabled": len(sheet_names) == 1,
            "es_hoja_consolidado": es_hoja_consolidado,
            "es_hoja_causas_legales": es_hoja_causas_legales,
            "es_hoja_querellas_sisgen": es_hoja_querellas_sisgen,
            **CATALOGOS_CONTEXTO,
            "mensaje_exito": mensaje_exito,
            "error": error,
            "datos_cargados": False,
            "hoja_vacia": False,
        }

        if archivo_cargado and hoja_seleccionada:
            try:
                def _cargar_datos_hoja():
                    if es_hoja_consolidado:
                        if registros := leer_hoja_consolidado(ruta_archivo, hoja_seleccionada):
                            return construir_contexto_consolidado(registros)
                        return {"hoja_vacia": True}
                    elif es_hoja_causas_legales:
                        registros_leg, catalogos_leg = leer_hoja_causas_legales(ruta_archivo, hoja_seleccionada)
                        if registros_leg:
                            return construir_contexto_causas_legales(registros_leg, catalogos_leg)
                        return {"hoja_vacia": True}
                    elif es_hoja_querellas_sisgen:
                        registros_sis, catalogos_sis = leer_hoja_querellas_sisgen(ruta_archivo, hoja_seleccionada)
                        if registros_sis:
                            return construir_contexto_querellas_sisgen(registros_sis, catalogos_sis)
                        return {"hoja_vacia": True}
                    else:
                        return leer_hoja_generica(ruta_archivo, hoja_seleccionada)

                contexto_hoja = obtener_contexto_cacheado(
                    ruta_archivo, hoja_seleccionada, _cargar_datos_hoja
                )
                contexto.update(contexto_hoja)
            except Exception as e:
                logger.exception("Error procesando la hoja %s", hoja_seleccionada)
                contexto["error"] = f"Error al procesar la hoja '{hoja_seleccionada}': {e}"

        return render(request, self.template_name, contexto)


dashboard = DashboardView.as_view()


def descargar_excel(request):
    ruta_archivo = request.session.get("ruta_archivo")
    nombre_archivo = request.session.get("nombre_archivo", "Archivo_actualizado.xlsx")

    if ruta_archivo and Path(ruta_archivo).is_file():
        return FileResponse(
            open(ruta_archivo, "rb"), as_attachment=True, filename=nombre_archivo
        )

    request.session["_flash_error"] = "No hay un archivo cargado para descargar."
    messages.error(request, "No hay un archivo cargado para descargar.")
    return redirect("dashboard")