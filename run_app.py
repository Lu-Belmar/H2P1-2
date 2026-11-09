# run_app.py
import os
import sys
import threading
import time
import webbrowser
from waitress import serve

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

def iniciar_servidor():
    try:
        serve(application, host='127.0.0.1', port=8080, threads=4)
    except Exception as e:
        print(f"Error en el servidor Waitress: {e}")

if __name__ == '__main__':
    # 1. Iniciar servidor Django en segundo plano (hilo daemon)
    servidor = threading.Thread(target=iniciar_servidor, daemon=True)
    servidor.start()

    # 2. Intentar abrir la ventana nativa de pywebview
    ventana_abierta = False
    try:
        import webview
        # Damos un pequeño respiro de medio segundo para asegurar que Waitress levantó el puerto
        time.sleep(0.5)
        
        webview.create_window(
            title='HenFID CMF - Visualizador y Editor',
            url='http://127.0.0.1:8080',
            width=1380,
            height=860,
            min_size=(1024, 700),
            maximized=True
        )
        webview.start()
        ventana_abierta = True
    except Exception as ex:
        print(f"Aviso: No se pudo abrir la ventana nativa de PyWebView ({ex}). Abriendo en navegador web...")

    # 3. Plan B: Si pywebview falló o dio error de DLL, abrir el navegador web por defecto
    if not ventana_abierta:
        time.sleep(0.8)
        webbrowser.open('http://127.0.0.1:8080')
        
        # Mantener la consola abierta o el script vivo si se compiló sin consola
        try:
            while servidor.is_alive():
                servidor.join(1)
        except KeyboardInterrupt:
            sys.exit(0)