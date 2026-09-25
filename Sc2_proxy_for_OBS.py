"""
sc2_obs_proxy.py
Script de OBS que lanza el proxy CORS/JSON de SC2 automáticamente al
abrir OBS y lo detiene automaticamente al cerrar OBS.

INSTALACION:
1. Deja este archivo en la misma carpeta que tus overlays (junto a
   status.json, SC2 Session Stats Overlay.html, etc.)
2. En OBS: Tools -> Scripts -> pestaña "Python Settings" -> selecciona
   la carpeta de tu instalacion de Python (la misma que usas para
   correr el proxy manualmente).
3. En OBS: Tools -> Scripts -> boton "+" -> selecciona este archivo.
4. Listo. Cada vez que abras OBS, el proxy se inicia solo. Al cerrar
   OBS (o al quitar el script de la lista), el proxy se detiene solo.
"""

import obspython as obs
import http.server
import urllib.request
import json
import threading
import os

SC2_API = "http://localhost:6119/game"
PROXY_PORT = 6120
STATUS_FILE_NAME = "status.json"
POLL_INTERVAL = 15.0  # segundos

_server_thread = None
_httpd = None
_writer_thread = None
_stop_event = threading.Event()

# Estado visible en la ventana Tools -> Scripts, para saber si el proxy
# esta corriendo y si logra conectarse al API de SC2 sin revisar la consola.
_status_text = "Sin iniciar"
_props_ref = None


def get_script_dir():
    return os.path.dirname(os.path.realpath(__file__))


def set_status(text):
    """Actualiza el texto de estado y refresca el panel de Scripts si esta abierto."""
    global _status_text
    _status_text = text
    if _props_ref is not None:
        info = obs.obs_properties_get(_props_ref, "status_info")
        if info is not None:
            obs.obs_property_set_description(info, "Estado del proxy:\n" + _status_text)


def write_status_loop():
    import datetime
    status_path = os.path.join(get_script_dir(), STATUS_FILE_NAME)
    tmp_path = status_path + ".tmp"
    while not _stop_event.is_set():
        now = datetime.datetime.now().strftime("%H:%M:%S")
        try:
            with urllib.request.urlopen(SC2_API, timeout=2) as resp:
                data = resp.read()
            set_status(f"Conectado a SC2 ({now})")
        except Exception as e:
            data = json.dumps({"error": str(e)}).encode("utf-8")
            set_status(f"Proxy activo, sin conexion a SC2 ({now}): {e}")

        try:
            # Escritura atomica para evitar lecturas de JSON incompleto
            with open(tmp_path, "wb") as f:
                f.write(data)
            os.replace(tmp_path, status_path)
        except Exception as e:
            set_status(f"Error escribiendo {STATUS_FILE_NAME} ({now}): {e}")

        _stop_event.wait(POLL_INTERVAL)


class CORSProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        status_path = os.path.join(get_script_dir(), STATUS_FILE_NAME)
        try:
            with open(status_path, "rb") as f:
                data = f.read()
        except Exception as e:
            data = json.dumps({"error": str(e)}).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        pass  # silencia el log en consola de OBS


def start_proxy():
    global _server_thread, _httpd, _writer_thread
    if _httpd is not None:
        return  # ya esta corriendo

    _stop_event.clear()

    _httpd = http.server.HTTPServer(("localhost", PROXY_PORT), CORSProxyHandler)
    _server_thread = threading.Thread(target=_httpd.serve_forever, daemon=True)
    _server_thread.start()

    _writer_thread = threading.Thread(target=write_status_loop, daemon=True)
    _writer_thread.start()

    set_status(f"Proxy iniciado en http://localhost:{PROXY_PORT}/game")
    obs.script_log(obs.LOG_INFO, f"SC2 Proxy iniciado en http://localhost:{PROXY_PORT}/game")


def stop_proxy():
    global _server_thread, _httpd, _writer_thread
    _stop_event.set()

    if _httpd is not None:
        _httpd.shutdown()
        _httpd.server_close()
        _httpd = None

    _server_thread = None
    _writer_thread = None
    set_status("Detenido")
    obs.script_log(obs.LOG_INFO, "SC2 Proxy detenido")


def refresh_status_button(props, prop):
    """Callback del boton 'Verificar ahora': hace una consulta inmediata
    al API de SC2 y actualiza el texto de estado sin esperar el proximo ciclo."""
    try:
        with urllib.request.urlopen(SC2_API, timeout=2) as resp:
            resp.read()
        set_status("Verificacion manual: conectado a SC2 correctamente")
    except Exception as e:
        set_status(f"Verificacion manual: sin conexion a SC2 ({e})")
    return True  # true refresca el panel de propiedades


# ---- Hooks de ciclo de vida del script en OBS ----

def script_description():
    return (
        "Proxy automatico para SC2 Tournament Overlay.\n\n"
        "Se conecta a http://localhost:6119/game y escribe status.json "
        f"en la carpeta del script. Se inicia al cargar OBS y se detiene "
        "al cerrar OBS.\n\n"
        "El estado actual del proxy se muestra abajo, en este mismo panel."
    )


def script_properties():
    global _props_ref
    props = obs.obs_properties_create()
    info = obs.obs_properties_add_text(
        props, "status_info", "Estado del proxy:\n" + _status_text,
        obs.OBS_TEXT_INFO
    )
    obs.obs_properties_add_button(
        props, "refresh_btn", "Verificar conexion ahora", refresh_status_button
    )
    _props_ref = props
    return props


def script_load(settings):
    start_proxy()


def script_unload():
    stop_proxy()