# core/excel_cache.py
import os
import threading

_CACHE_LOCK = threading.Lock()
# Estructura: { (ruta_norm, hoja_norm): {"mtime": float, "size": int, "data": dict} }
_MEMORIA_EXCELS = {}
# Estructura: { ruta_norm: {"mtime": float, "sheets": list} }
_MEMORIA_HOJAS = {}


def _firma_archivo(ruta_archivo):
    """Obtiene la marca de tiempo de modificación y tamaño en menos de 0.1 milisegundos."""
    stat = os.stat(ruta_archivo)
    return (stat.st_mtime, stat.st_size)


def obtener_hojas_cacheadas(ruta_archivo, funcion_lectora_hojas):
    """Devuelve la lista de pestañas desde RAM si el archivo no ha cambiado en disco."""
    ruta_key = os.path.normcase(os.path.abspath(ruta_archivo))
    firma_actual = _firma_archivo(ruta_archivo)

    with _CACHE_LOCK:
        entrada = _MEMORIA_HOJAS.get(ruta_key)
        if entrada and entrada["firma"] == firma_actual:
            return entrada["sheets"]

    sheets = funcion_lectora_hojas(ruta_archivo)
    with _CACHE_LOCK:
        _MEMORIA_HOJAS[ruta_key] = {"firma": firma_actual, "sheets": sheets}
    return sheets


def obtener_contexto_cacheado(ruta_archivo, nombre_hoja, funcion_constructora):
    """
    Si el archivo y hoja ya están en RAM y el archivo en disco no fue modificado,
    devuelve el contexto instantáneamente sin ejecutar openpyxl.
    """
    ruta_key = os.path.normcase(os.path.abspath(ruta_archivo))
    hoja_key = nombre_hoja.strip().lower()
    clave = (ruta_key, hoja_key)
    firma_actual = _firma_archivo(ruta_archivo)

    with _CACHE_LOCK:
        entrada = _MEMORIA_EXCELS.get(clave)
        if entrada and entrada["firma"] == firma_actual:
            # Retornamos copia superficial para no mutar la caché
            return dict(entrada["data"])

    # Si no está en caché o el Excel cambió en disco/SharePoint, lo procesamos
    contexto_hoja = funcion_constructora()

    with _CACHE_LOCK:
        _MEMORIA_EXCELS[clave] = {
            "firma": firma_actual,
            "data": dict(contexto_hoja),
        }
    return contexto_hoja


def invalidar_cache_archivo(ruta_archivo=None):
    """Limpia la caché de un archivo específico (o de todos) al forzar recarga o guardar."""
    with _CACHE_LOCK:
        if not ruta_archivo:
            _MEMORIA_EXCELS.clear()
            _MEMORIA_HOJAS.clear()
            return

        ruta_key = os.path.normcase(os.path.abspath(ruta_archivo))
        _MEMORIA_HOJAS.pop(ruta_key, None)
        claves_borrar = [k for k in _MEMORIA_EXCELS if k[0] == ruta_key]
        for k in claves_borrar:
            _MEMORIA_EXCELS.pop(k, None)