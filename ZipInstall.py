import tkinter as tk
from tkinter import filedialog
import zipfile
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
    # Selección del ZIP
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
        if len(sys.argv) < 3:
            log("[ERROR] Ruta ZIP no proporcionada en modo silencioso.")
            return
        zip_path = sys.argv[2]

    zip_dir = os.path.dirname(zip_path)
    flat_files = []  # archivos extraídos al nivel raiz para limpieza

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            names = zip_ref.namelist()
            log("== ARCHIVOS ENCONTRADOS EN EL ZIP ==")
            for nombre in names:
                log(f" - {nombre}")
            log("===================================")

            # Enumerar subcarpetas y su contenido
            subfolders = sorted({n.split('/', 1)[0] for n in names if '/' in n})
            if subfolders:
                log("== SUBCARPETAS ==")
                for folder in subfolders:
                    log(f" - {folder}")
                    files = [f for f in names if f.startswith(folder + '/') and not f.endswith('/')]
                    for f in files:
                        log(f"     - {f.split('/', 1)[1]}")
                log("===================================")

            # Extracción manual de directorios y archivos (estructura original)
            for member in zip_ref.infolist():
                member_path = member.filename
                target_path = os.path.join(zip_dir, member_path)
                if member.is_dir():
                    os.makedirs(target_path, exist_ok=True)
                    log(f"[DEBUG] Creado directorio: {target_path}")
                else:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with zip_ref.open(member) as src, open(target_path, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
                    log(f"[DEBUG] Extraído en estructura: {target_path}")

                    # Extracción plana de este archivo al nivel raíz
                    base_name = os.path.basename(member_path)
                    flat_dest = os.path.join(zip_dir, base_name)
                    name, ext = os.path.splitext(base_name)
                    count = 1
                    while os.path.exists(flat_dest):
                        flat_dest = os.path.join(zip_dir, f"{name}_{count}{ext}")
                        count += 1
                    with zip_ref.open(member) as src2, open(flat_dest, 'wb') as dst2:
                        shutil.copyfileobj(src2, dst2)
                    log(f"[DEBUG] Extraído plano: {flat_dest}")
                    flat_files.append(os.path.basename(flat_dest))

        # Procesar MANIFEST.MAN
        manifest_path = os.path.join(zip_dir, "MANIFEST.MAN")
        if not os.path.isfile(manifest_path):
            raise FileNotFoundError("MANIFEST.MAN no encontrado en el ZIP.")

        with open(manifest_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        # Mostrar título
        if "TITLE=:" not in lines:
            raise ValueError("MANIFEST.MAN inválido: falta TITLE=:")
        title_idx = lines.index("TITLE=:")
        log("== TÍTULO DEL PROGRAMA ==")
        for line in lines[title_idx + 1:]:
            if line.startswith("INSTALL=:"):
                break
            log(f" - {line}")
        log("===========================")

        # Parse instrucciones
        instrucciones = []
        open_cmd = None
        run_before, run_after = [], []
        ask_letter = None

        if "INSTALL=:" in lines:
            idx = lines.index("INSTALL=:")
            for raw in lines[idx + 1:]:
                if raw.startswith("ECHO "):
                    log(f"[ECHO] {raw[5:].strip()}")
                elif raw.startswith("OPEN="):
                    open_cmd = raw.split("=", 1)[1].strip()
                elif raw.startswith("RUNBEFORE="):
                    run_before.append(raw.split("=", 1)[1].strip())
                elif raw.startswith("RUNAFTER="):
                    run_after.append(raw.split("=", 1)[1].strip())
                elif raw.startswith("ASKLETTER="):
                    ask_letter = raw.split("=", 1)[1].strip()
                elif "|" in raw:
                    left, right = [x.strip().strip('"') for x in raw.split("|", 1)]
                    if left.upper().startswith("IFEXISTS="):
                        path = left.split("=", 1)[1].strip()
                        instrucciones.append(("IFEXISTS", path, right))
                    else:
                        instrucciones.append(("INSTALL", left, right))
                else:
                    log(f"[WARN] Línea desconocida: {raw}")

        # Solicitar letra de unidad si es necesario
        if ask_letter:
            unidad = input("[ASKLETTER] Introduce letra de unidad (C, D, etc.): ").strip().upper()
            if unidad not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                log(f"[ERROR] Letra inválida: {unidad}")
                return
            instrucciones = [(
                t,
                d.replace(f"{d[0]}:/", f"{unidad}:/") if d else d,
                h.replace(f"{h[0]}:/", f"{unidad}:/") if h else h
            ) for t, d, h in instrucciones]

        # Ejecutar RUNBEFORE
        for cmd in run_before:
            log(f"[INFO] RUNBEFORE: {cmd}")
            subprocess.run(cmd, shell=True)

        # Ejecutar instrucciones de copia
        for tipo, src_folder, dst_folder in instrucciones:
            if tipo == "IFEXISTS" and not os.path.exists(dst_folder):
                log(f"[INFO] IFEXISTS ignorado: {dst_folder} no existe")
                continue
            origen = os.path.join(zip_dir, src_folder)
            if not os.path.exists(origen):
                raise FileNotFoundError(f"Carpeta no encontrada: {src_folder}")
            os.makedirs(dst_folder, exist_ok=True)
            for item in os.listdir(origen):
                s = os.path.join(origen, item)
                d = os.path.join(dst_folder, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                    log(f"[DEBUG] Copiado dir: {d}")
                else:
                    shutil.copy2(s, d)
                    log(f"[DEBUG] Copiado archivo: {d}")

        # Ejecutar RUNAFTER
        for cmd in run_after:
            log(f"[INFO] RUNAFTER: {cmd}")
            subprocess.run(cmd, shell=True)

        # Ejecutar OPEN
        if open_cmd:
            log(f"[INFO] OPEN: {open_cmd}")
            subprocess.Popen(shlex.split(open_cmd))

        # Limpieza de archivos planos extraídos
        for fname in flat_files:
            try:
                os.remove(os.path.join(zip_dir, fname))
                log(f"[INFO] Borrado plano: {fname}")
            except Exception as e:
                log(f"[WARN] No se pudo borrar plano {fname}: {e}")

        log("[INFO] Instalación completa y limpieza finalizada.")

    except Exception as e:
        log(f"[ERROR] Error: {e}")


if __name__ == "__main__":
    silent = "--silent" in sys.argv
    instalar_zip(silent=silent)
