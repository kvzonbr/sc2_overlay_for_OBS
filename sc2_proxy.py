import urllib.request
import json
import time
import os
import traceback

SC2_API = "http://localhost:6119/game"
OUTPUT_FILE = "status.json"
POLL_INTERVAL = 10

def fetch_and_save():
    try:
        with urllib.request.urlopen(SC2_API, timeout=2) as resp:
            data = resp.read()
        json.loads(data)
    except Exception as e:
        data = json.dumps({"error": str(e), "players": []}).encode("utf-8")

    try:
        tmp_file = OUTPUT_FILE + ".tmp"
        with open(tmp_file, "wb") as f:
            f.write(data)
        os.replace(tmp_file, OUTPUT_FILE)
    except Exception as e:
        print("Error escribiendo el archivo:", e)

if __name__ == "__main__":
    print("Escribiendo estado en status.json cada 10 segundos...")
    print("Deja esta ventana abierta. Ctrl+C para detener.")
    while True:
        try:
            fetch_and_save()
        except Exception:
            traceback.print_exc()
        time.sleep(POLL_INTERVAL)