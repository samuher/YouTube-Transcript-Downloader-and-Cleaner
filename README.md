# 📺 Descargador y Limpiador de Transcripciones de YouTube

**🌐 Idiomas / Languages / 语言:** [Español](README.md) · [English](README.en.md) · [中文](README.zh.md)

Script en Python que descarga automáticamente las transcripciones (subtítulos) de todos los vídeos de un canal de YouTube y las convierte en archivos `.txt` limpios, sin marcas de tiempo ni etiquetas — listos para leer, analizar o usar como texto plano.

---

## 📑 Tabla de contenidos

- [¿Qué hace este script?](#-qué-hace-este-script)
- [Requisitos previos](#-requisitos-previos)
- [1. Instalar Python](#1-instalar-python)
- [2. Descargar el proyecto](#2-descargar-el-proyecto)
- [3. Instalar las dependencias](#3-instalar-las-dependencias)
<<<<<<< HEAD
- [4. Configurar el canal a descargar](#4-configurar-el-canal-a-descargar)
- [5. Ejecutar el script](#5-ejecutar-el-script)
=======
- [4. Descargar las transcripciones de un canal](#4-descargar-las-transcripciones-de-un-canal)
- [5. Consolidar las transcripciones para NotebookLM](#5-consolidar-las-transcripciones-para-notebooklm)
>>>>>>> dac8465 (Cambios importantes en las transcripciones asi como consolidador si utilizas Notebook)
- [6. Personalizar el proyecto](#6-personalizar-el-proyecto)
- [Alternativas sin instalar nada: Google Colab / Jupyter](#-alternativas-sin-instalar-nada-google-colab--jupyter)
- [Notas y problemas comunes](#-notas-y-problemas-comunes)

---

## 🔍 ¿Qué hace este script?

1. Recibe la URL de un canal de YouTube.
2. Usa la librería [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) para descargar **solo los subtítulos** de cada vídeo (no descarga el vídeo en sí).
3. Limpia cada archivo de subtítulos (`.vtt`): elimina marcas de tiempo, etiquetas HTML y líneas repetidas.
4. Guarda el resultado como un archivo `.txt` plano por cada vídeo.
5. Borra los `.vtt` originales, dejando solo los `.txt` limpios en la carpeta de destino.

---

## ✅ Requisitos previos

- **Python 3.8 o superior**
- **Conexión a internet estable** — el script descarga datos de YouTube vídeo por vídeo, así que en canales grandes puede tardar y consumir bastante ancho de banda.

---

## 1. Instalar Python

### Comprobar si ya lo tienes instalado

Abre una terminal (en Windows, `cmd` o `PowerShell`; en macOS/Linux, `Terminal`) y escribe:

```bash
python --version
```

Si no reconoce el comando, prueba con:

```bash
python3 --version
```

Si te aparece algo como `Python 3.11.4`, ya lo tienes instalado y puedes saltar al [paso 2](#2-descargar-el-proyecto).

### Si no lo tienes instalado

1. Ve a la web oficial: **[python.org/downloads](https://www.python.org/downloads/)**
2. Descarga la última versión estable para tu sistema operativo.
3. **Windows:** durante la instalación, marca la casilla **"Add python.exe to PATH"** antes de darle a instalar (es el paso donde más gente se equivoca).
4. **macOS:** puedes usar el instalador oficial, o si tienes [Homebrew](https://brew.sh/), ejecutar `brew install python`.
5. **Linux (Debian/Ubuntu):** normalmente ya viene instalado; si no, ejecuta:
   ```bash
   sudo apt update && sudo apt install python3 python3-pip
   ```
6. Cierra y vuelve a abrir la terminal, y repite el comando `python --version` para confirmar que se instaló bien.

---

## 2. Descargar el proyecto

Clona el repositorio con Git:

```bash
git clone https://github.com/<tu-usuario>/<tu-repositorio>.git
cd <tu-repositorio>
```

Si no usas Git, también puedes descargar el proyecto como ZIP desde GitHub (botón verde **"Code" → "Download ZIP"**) y descomprimirlo.

---

## 3. Instalar las dependencias

Este proyecto solo necesita una librería externa: `yt-dlp` (las demás, `os` y `re`, ya vienen incluidas con Python).

Desde la carpeta del proyecto, ejecuta:

```bash
pip install -r requirements.txt
```

Si `pip` no funciona, prueba con `pip3` o `python -m pip install -r requirements.txt`.

---

<<<<<<< HEAD
## 4. Configurar el canal a descargar

Abre `descargar_transcripciones.py` y busca estas dos líneas al final del archivo:

```python
url_del_canal = "https://www.youtube.com/@CanalDeEjemplo"
ruta_de_guardado = r"transcripciones/CanalDeEjemplo"
```

- **`url_del_canal`**: sustitúyela por la URL del canal que quieras (por ejemplo `https://www.youtube.com/@NombreDelCanal` o `https://www.youtube.com/channel/UCxxxxxx`).
- **`ruta_de_guardado`**: es el nombre de la carpeta donde se guardarán los `.txt`. Puedes ponerle el nombre que quieras.

---

## 5. Ejecutar el script

Desde la carpeta del proyecto:
=======
## 4. Descargar las transcripciones de un canal

Tienes dos formas de ejecutarlo — elige la que prefieras.

### Opción A: modo interactivo (recomendado si no te manejas con la terminal)

Desde la carpeta del proyecto, ejecuta:
>>>>>>> dac8465 (Cambios importantes en las transcripciones asi como consolidador si utilizas Notebook)

```bash
python descargar_transcripciones.py
```

<<<<<<< HEAD
(o `python3 descargar_transcripciones.py` según tu sistema)

El script irá mostrando el progreso en la terminal y, al terminar, encontrarás los archivos `.txt` limpios dentro de la carpeta que indicaste en `ruta_de_guardado`.
=======
El script te irá preguntando:
1. La URL del canal (por ejemplo `https://www.youtube.com/@NombreDelCanal`)
2. La carpeta donde guardar los `.txt` (pulsa Enter para que la genere automáticamente a partir del nombre del canal)
3. El idioma de los subtítulos (pulsa Enter para usar inglés por defecto)

> 💡 No hace falta que añadas `/videos` al final de la URL — el script lo hace automáticamente, para evitar descargar Shorts, directos y vídeos repetidos de las playlists del canal.

### Opción B: por línea de comandos (para automatizar o repetirlo sin escribir nada a mano)

```bash
python descargar_transcripciones.py -c "https://www.youtube.com/@NombreDelCanal" -d "transcripciones/MiCanal" -i es,en
```

| Parámetro | Qué hace | Obligatorio |
|---|---|---|
| `-c`, `--canal` | URL del canal de YouTube | Sí |
| `-d`, `--destino` | Carpeta donde guardar los `.txt` | No (se genera sola si no lo indicas) |
| `-i`, `--idiomas` | Idiomas de subtítulos separados por coma (ej. `en,es`) | No (por defecto `en`) |

El script mostrará el progreso en la terminal y, al terminar, tendrás los `.txt` limpios en la carpeta de destino.

---

## 5. Consolidar las transcripciones para NotebookLM

Si vas a subir las transcripciones a [NotebookLM](https://notebooklm.google/), el proyecto incluye `Consolidador.py`, que agrupa los `.txt` sueltos en "tomos" respetando el límite de **500.000 palabras por fuente** de NotebookLM (con un margen de seguridad de 450.000 por defecto), en vez de subir cada vídeo como fuente separada y agotar rápido el límite de 50 fuentes del plan gratuito.

### Opción A: modo interactivo

```bash
python Consolidador.py
```

Te pedirá la carpeta de origen (donde están los `.txt`), la carpeta de destino, el límite de palabras por tomo y, opcionalmente, un nombre para los archivos generados.

### Opción B: por línea de comandos

```bash
python Consolidador.py -o "transcripciones/MiCanal" -d "notebooklm_listo" -l 450000 -n "MiCanal"
```

| Parámetro | Qué hace | Obligatorio |
|---|---|---|
| `-o`, `--origen` | Carpeta con los `.txt` sueltos a consolidar | Sí |
| `-d`, `--destino` | Carpeta donde guardar los tomos consolidados | No (por defecto `notebooklm_listo`) |
| `-l`, `--limite` | Límite de palabras por tomo | No (por defecto 450.000) |
| `-n`, `--nombre` | Prefijo para nombrar los tomos generados | No (se genera a partir de la carpeta de origen) |

Al terminar, el script avisa si el número de tomos generados supera el límite de 50 fuentes del plan gratuito de NotebookLM.
>>>>>>> dac8465 (Cambios importantes en las transcripciones asi como consolidador si utilizas Notebook)

---

## 6. Personalizar el proyecto

<<<<<<< HEAD
| Qué quieres cambiar | Dónde tocar | Cómo |
|---|---|---|
| El canal a descargar | `url_del_canal` | Pega la URL del nuevo canal |
| La carpeta de salida | `ruta_de_guardado` | Escribe la ruta/nombre que quieras |
| El idioma de los subtítulos | `'subtitleslangs': ['en']` dentro de `ydl_opts` | Cambia `'en'` por `'es'` (español), `'fr'` (francés), etc. Puedes poner varios: `['es', 'en']` |
| El formato del nombre de archivo | `'outtmpl'` dentro de `ydl_opts` | Usa las [plantillas de salida de yt-dlp](https://github.com/yt-dlp/yt-dlp#output-template) |
=======
La mayoría de ajustes (canal, carpeta, idioma, límite de palabras) ya no requieren tocar el código — se pasan como parámetros o se responden por pantalla, como se explica en los pasos 4 y 5.

Si quieres ir más allá, esto sí requiere editar el código directamente:

| Qué quieres cambiar | Dónde tocar | Cómo |
|---|---|---|
| El formato del nombre de archivo de cada vídeo | `'outtmpl'` dentro de `ydl_opts` en `descargar_transcripciones.py` | Usa las [plantillas de salida de yt-dlp](https://github.com/yt-dlp/yt-dlp#output-template) |
| El separador entre transcripciones en los tomos consolidados | El bloque `texto_consolidado += ...` en `Consolidador.py` | Cambia el texto del separador y la etiqueta `FUENTE:` a tu gusto |
>>>>>>> dac8465 (Cambios importantes en las transcripciones asi como consolidador si utilizas Notebook)

---

## 💻 Alternativas sin instalar nada: Google Colab / Jupyter

Si no quieres instalar Python en tu ordenador, puedes ejecutar este mismo código en un notebook:

- **[Google Colab](https://colab.research.google.com/)**: crea un notebook nuevo, pega el código en una celda y, antes de ejecutarlo, añade una celda con `!pip install yt-dlp`. Solo necesitas una cuenta de Google.
- **Jupyter Notebook**: si prefieres tenerlo en tu propio equipo, instálalo con `pip install notebook` y ábrelo con `jupyter notebook`.

⚠️ **Ten en cuenta antes de usar Colab u otro notebook en la nube:**
- Necesitas **conexión a internet estable durante toda la ejecución**, ya que cada vídeo se descarga en el momento.
- En canales con muchos vídeos, el proceso puede ser **largo** y consumir bastante almacenamiento temporal en la sesión del notebook.
- Las sesiones gratuitas de Colab se desconectan tras un tiempo de inactividad, así que canales muy grandes pueden requerir dividir el trabajo en varias ejecuciones.

---

## 🛠 Notas y problemas comunes

- **Error de subtítulos no disponibles**: no todos los vídeos tienen subtítulos automáticos o manuales en el idioma configurado; el script los ignorará y seguirá con el resto (gracias a `'ignoreerrors': True`).
- **yt-dlp deja de funcionar de un día para otro**: YouTube cambia su plataforma con frecuencia. Si el script empieza a fallar, actualiza la librería:
  ```bash
  pip install -U yt-dlp
  ```
- **El proceso es muy lento**: es normal en canales con muchos vídeos, ya que se hace una petición por cada uno. No hay forma de paralelizarlo sin arriesgarte a que YouTube bloquee temporalmente las peticiones.
