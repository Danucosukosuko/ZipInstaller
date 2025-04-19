import tkinter as tk
from tkinter import filedialog
import zipfile
import tempfile
import os
import shutil
import subprocess
import shlex
import sys
from datetime import datetime

log_path = os.path.join(os.getcwd(), "instalador.log")

def log(msg):
    print(msg)
    with open(log_path, "a", encoding='utf-8') as logf:
        logf.write(f"[{datetime.now().isoformat()}] {msg}\n")

def instalar_zip(silent=False):
    if not silent:
        root = tk.Tk()
        root.withdraw()
        zip_path = filedialog.askopenfilename(
            title="Selecciona el archivo ZIP",
            filetypes=[("Archivo ZIP", "*.zip")]
        )
        if not zip_path:
            log("[ERROR] No se seleccionó ningún archivo.")
            return
    else:
        if len(sys.argv) < 2:
            log("[ERROR] Ruta ZIP no proporcionada en modo silencioso.")
            return
        zip_path = sys.argv[2]

    try:
        with tempfile.TemporaryDirectory() as tempdir:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tempdir)

            # Buscar MANIFEST.MAN
            manifest_path = None
            for root_dir, _, files in os.walk(tempdir):
                if "MANIFEST.MAN" in files:
                    manifest_path = os.path.join(root_dir, "MANIFEST.MAN")
                    manifest_base = root_dir
                    break

            if not manifest_path:
                raise FileNotFoundError("MANIFEST.MAN no encontrado en el ZIP.")

            # Leer y limpiar líneas
            with open(manifest_path, 'r', encoding='utf-8') as f:
                lines_raw = [line.rstrip('\n') for line in f]
            lines = [line.strip() for line in lines_raw if line.strip()]

            # Mostrar TÍTULO
            if "TITLE=:" not in lines:
                raise ValueError("MANIFEST.MAN inválido: falta TITLE=:")
            title_index = lines.index("TITLE=:")

            log("== TÍTULO DEL PROGRAMA ==")
            for titulo in lines[title_index + 1:]:
                if titulo.startswith("INSTALL=:"):
                    break
                log(titulo)
            log("=" * 27)

            # Inicializar estructuras
            instrucciones = []
            open_command = None
            run_before = []
            run_after = []
            ask_letter = None

            # Procesar instrucciones tras INSTALL=:
            if "INSTALL=:" in lines:
                install_index = lines.index("INSTALL=:")
                for raw in lines[install_index + 1:]:
                    if raw.startswith("ECHO "):
                        log("[ECHO] " + raw[5:].strip())
                        continue
                    elif raw.startswith("OPEN="):
                        open_command = raw[len("OPEN="):].strip()
                        continue
                    elif raw.startswith("RUNBEFORE="):
                        run_before.append(raw[len("RUNBEFORE="):].strip())
                        continue
                    elif raw.startswith("RUNAFTER="):
                        run_after.append(raw[len("RUNAFTER="):].strip())
                        continue
                    elif raw.startswith("ASKLETTER="):
                        ask_letter = raw[len("ASKLETTER="):].strip()
                        continue
                    elif "|" in raw:
                        izq, der = [x.strip().strip('"') for x in raw.split("|", 1)]
                        if izq.upper().startswith("IFEXISTS="):
                            izq = izq.split("=",1)[1].strip()
                            instrucciones.append(("IFEXISTS", izq, der))
                        else:
                            instrucciones.append(("INSTALL", izq, der))
                    else:
                        log(f"[WARN] Línea desconocida tras INSTALL=: {raw}")

            # Si pide letra de unidad, solicitarla y ajustar rutas
            if ask_letter:
                unidad = input("[ASKLETTER] Introduce la letra de unidad que deseas usar (por ejemplo, C, D, E): ").strip().upper()
                if len(unidad) != 1 or unidad not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    log(f"[ERROR] Letra de unidad inválida: {unidad}")
                    return
                instrucciones = [
                    (tipo,
                     izq.replace(f"{izq[0]}:\\", f"{unidad}:\\") if izq else izq,
                     der.replace(f"{der[0]}:\\", f"{unidad}:\\") if der else der)
                    for tipo, izq, der in instrucciones
                ]

            # Ejecutar comandos RUNBEFORE
            for cmd in run_before:
                try:
                    log(f"[INFO] Ejecutando RUNBEFORE: {cmd}")
                    subprocess.run(cmd, shell=True)
                except Exception as e:
                    log(f"[ERROR] en RUNBEFORE: {e}")

            # Copiar archivos según instrucciones INSTALL/IFEXISTS
            for tipo, carpeta, destino in instrucciones:
                if tipo == "IFEXISTS" and not os.path.exists(destino):
                    log(f"[INFO] IFEXISTS ignorado, no existe: {destino}")
                    continue
                origen = os.path.join(manifest_base, carpeta)
                if not os.path.exists(origen):
                    raise FileNotFoundError(f"No se encuentra la carpeta '{carpeta}' en el ZIP.")
                destino = os.path.normpath(destino)
                os.makedirs(destino, exist_ok=True)
                for item in os.listdir(origen):
                    src = os.path.join(origen, item)
                    dst = os.path.join(destino, item)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                        log(f"[DEBUG] Copiado directorio: {dst}")
                    else:
                        shutil.copy2(src, dst)
                        log(f"[DEBUG] Copiado archivo: {dst}")

            # Ejecutar comandos RUNAFTER
            for cmd in run_after:
                try:
                    log(f"[INFO] Ejecutando RUNAFTER: {cmd}")
                    subprocess.run(cmd, shell=True)
                except Exception as e:
                    log(f"[ERROR] en RUNAFTER: {e}")

            # Abrir comando final si existe
            if open_command:
                try:
                    log(f"[INFO] Ejecutando OPEN: {open_command}")
                    subprocess.Popen(shlex.split(open_command))
                except Exception as e:
                    log(f"[ERROR] OPEN falló: {e}")

            log("[INFO] Instalación completada.")

    except Exception as e:
        log(f"[ERROR] Ocurrió un error:\n{e}")

if __name__ == "__main__":
    silent = "--silent" in sys.argv
    instalar_zip(silent=silent)
