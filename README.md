

# ZipInstaller

**ZipInstaller** es una herramienta escrita en Python que permite ejecutar instalaciones automatizadas a partir de un archivo `.zip` que contiene un archivo de manifiesto (`MANIFEST.MAN`). Está diseñada para simplificar despliegues en entornos controlados, permitiendo copiar archivos, ejecutar comandos previos o posteriores, y registrar el proceso en un log.

---

## 🚀 Características

- Instala archivos desde un `.zip` utilizando instrucciones detalladas en `MANIFEST.MAN`.
- Soporta comandos previos (`RUNBEFORE`) y posteriores (`RUNAFTER`) a la instalación.
- Permite mostrar títulos e información con `TITLE` y `ECHO`.
- Soporta condiciones mediante `IFEXISTS`.
- Solicita al usuario una letra de unidad si se especifica `ASKLETTER`.
- Ejecución en modo gráfico o modo silencioso por línea de comandos.
- Registro completo en `instalador.log`.

---

## 📦 Estructura del archivo ZIP

El archivo `.zip` debe incluir:

```
/MANIFEST.MAN
/Carpeta1/
  archivo1.txt
  archivo2.dll
...
```

---

## 🧾 Formato de MANIFEST.MAN

El archivo `MANIFEST.MAN` contiene las instrucciones de instalación, con el siguiente formato:

```txt
TITLE=:
Nombre del programa
Versión 1.2.3
Desarrollado por X

INSTALL=:
ECHO Iniciando instalación...
RUNBEFORE=taskkill /IM app.exe /F
ASKLETTER=C
Carpeta1|C:\<LETRA>\Program Files\App
IFEXISTS=C:\Drivers|C:\Backup\Drivers
RUNAFTER=regedit /s settings.reg
OPEN=notepad.exe
```

---

## 🔧 Comandos disponibles

- **`TITLE=:`**  
  Muestra líneas siguientes como título o descripción inicial.

- **`INSTALL=:`**  
  Indica el inicio del bloque de instrucciones.

- **`ECHO <mensaje>`**  
  Muestra un mensaje en consola y lo guarda en el log.

- **`RUNBEFORE=<comando>`**  
  Ejecuta un comando antes de instalar los archivos.

- **`RUNAFTER=<comando>`**  
  Ejecuta un comando después de instalar los archivos.

- **`ASKLETTER=<letra>`**  
  Solicita al usuario una letra de unidad y sustituye en rutas.

- **`<origen>|<destino>`**  
  Copia desde el ZIP al destino especificado.

- **`IFEXISTS=<origen>|<destino>`**  
  Solo copia si `<origen>` existe.

- **`OPEN=<comando>`**  
  Ejecuta un comando al final de la instalación.

---

## 🖥️ Uso

### Modo gráfico (interactivo)

```bash
python ZipInstaller.py
```

Se abrirá una ventana para seleccionar el archivo `.zip`.

### Modo silencioso

```bash
python ZipInstaller.py --silent "ruta/del/archivo.zip"
```

Ejecuta directamente sin interfaz gráfica, útil para automatización.

---

## 📝 Log

Todo el proceso se registra en `instalador.log`, incluyendo errores, comandos ejecutados y operaciones de copia realizadas.

---

## ⚙️ Requisitos

- Python 3.x
- Bibliotecas estándar (`tkinter`, `zipfile`, `subprocess`, `shutil`, `tempfile`, etc.)

---

## 📄 Licencia

GNU GPLv3

---

## ✍️ Autor
Danucosukosuko.

