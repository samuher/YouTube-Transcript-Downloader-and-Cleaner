# YouTube Transcript Downloader & Cleaner

[English](README.en.md) · [中文](README.zh.md)

Descarga los subtítulos disponibles de un canal o vídeo de YouTube y los guarda como archivos TXT sin marcas de tiempo. También puedes agrupar los textos para NotebookLM.

**No descarga vídeos ni transcribe audio.** Un vídeo sin subtítulos accesibles no producirá texto.

## Instalación

Requiere Python 3.11 o superior:

```bash
git clone https://github.com/samuher/YouTube-Transcript-Downloader-and-Cleaner.git
cd YouTube-Transcript-Downloader-and-Cleaner
python -m pip install -r requirements.txt
```

Si `python` no se reconoce, prueba `py` en Windows o `python3` en macOS/Linux.

## Descargar transcripciones

```bash
python descargar_transcripciones.py -c "https://www.youtube.com/@NombreDelCanal" -i es,en
```

Por defecto guarda los archivos en `transcripciones/NombreDelCanal/`. Para elegir carpeta y probar con cinco vídeos:

```bash
python descargar_transcripciones.py -c "https://www.youtube.com/@NombreDelCanal" -d "mis_transcripciones" -i es --max-videos 5
```

También acepta un enlace a un vídeo individual (`watch?v=...` o `youtu.be/...`). Si ejecutas el programa sin `-c`, te preguntará los datos.

| Opción | Función |
| --- | --- |
| `-c, --canal` | URL de canal o vídeo |
| `-i, --idiomas` | Idiomas separados por comas; por defecto `en` |
| `-d, --destino` | Carpeta de destino |
| `--max-videos N` | Procesar como máximo N vídeos |
| `--forzar` | Repetir las descargas ya completadas |

Cada TXT incluye el ID para evitar colisiones: `Título [abcdefghijk].es.txt`. El archivo oculto `.transcripciones_index.json` registra los vídeos descargados correctamente para evitar procesarlos dos veces. Los vídeos sin subtítulos no se marcan como completados y pueden reintentarse.

## Descargas largas: pausas, reintentos y reanudación

Para descargar **todos los vídeos de la pestaña /videos**, ejecuta sin `--max-videos`. Un enlace a `/shorts` o `/streams` procesa únicamente esa pestaña. El programa descarga los subtítulos accesibles, **no transcribe audio** ni garantiza acceso a todos los vídeos.

**Prueba inicial (los primeros cinco vídeos):**

```bash
python descargar_transcripciones.py -c "https://www.youtube.com/@NombreDelCanal" -i es,en --max-videos 5
```

Luego ejecuta el mismo comando **sin** `--max-videos` para recorrer todo el canal: omite los vídeos completados. `--max-videos` selecciona siempre los *primeros N*, no sirve para saltar a los siguientes N.

**Ejemplo de ejecución más pausada:**

```bash
python descargar_transcripciones.py -c "https://www.youtube.com/@NombreDelCanal" -i es,en --pausa-min 5 --pausa-max 12 --reintentos 3
```

| Opción | Valor inicial | Función |
| --- | --- | --- |
| `--pausa-min` / `--pausa-max` | 3 / 7 segundos | Espera aleatoria entre solicitudes de vídeos nuevos |
| `--reintentos` | 2 | Reintentos adicionales ante 429, 5xx o errores temporales de red |
| `--espera-inicial` | 30 segundos | Primera espera tras un error temporal; crece progresivamente |
| `--espera-maxima` | 300 segundos | Límite de espera progresiva |
| `--espera-subtitulos` | 1 segundo | Espera de yt-dlp antes de solicitar cada subtítulo |
| `--forzar` | Desactivado | Vuelve a descargar vídeos completados |
| `--navegador` | Desactivado | Lee la sesión de un navegador local |
| `--cookies` | Desactivado | Usa un archivo Netscape `cookies.txt` local |

Si persisten errores **429**, aparece **403** o se requiere identificación por posible detección de bot, el programa **se detiene** en vez de enviar solicitudes al resto del canal. Los archivos descargados no se eliminan; al volver a ejecutar con la misma carpeta, se omiten los completados. No reinicies repetidamente mientras exista un bloqueo.

Dentro de la carpeta de salida encontrarás:

- `.transcripciones_index.json`: estado de las descargas completadas (no se guardan contraseñas).
- `reporte_descargas.csv`: historial acumulativo por vídeo, con fecha, resultado, número de intentos y archivos. Los estados incluyen `descargado`, `ya_descargado`, `sin_subtitulos`, `error`, `bloqueado` e `interrumpido`.

Un vídeo sin subtítulos **no** se marca como completado y podrá volver a intentarse. El programa detecta también errores 429/403 que yt-dlp comunica como advertencias, sin lanzar una excepción.

### Uso opcional de tu sesión de YouTube

No necesitas iniciar sesión para subtítulos públicos. Si tienes acceso legítimo mediante tu navegador y decides usar su sesión:

```bash
python descargar_transcripciones.py -c "https://www.youtube.com/@NombreDelCanal" -i es --navegador brave
```

También puedes indicar un archivo de cookies en formato Netscape:

```bash
python descargar_transcripciones.py -c "https://www.youtube.com/@NombreDelCanal" -i es --cookies "cookies.txt"
```

No se pueden combinar las dos opciones. **Las cookies son credenciales sensibles:** nunca las subas al repositorio ni las compartas. Usar una cuenta puede suponer restricciones o riesgos para ella. Consulta las [notas de YouTube de yt-dlp](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#youtube) y su [guía de cookies](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp). Las cookies no garantizan resolver los errores 403/429 ni las comprobaciones de bot.

## Preparar tomos para NotebookLM

```bash
python Consolidador.py -o "transcripciones/NombreDelCanal" -d "notebooklm_listo"
```

Con un límite personalizado:

```bash
python Consolidador.py -o "mis_transcripciones" -d "notebooklm_listo" -l 100000 -n "Curso"
```

Por defecto utiliza 450 000 palabras por tomo (máximo configurable: 500 000), **incluidos los encabezados**. Si un TXT es muy largo, lo divide sin perder palabras y etiqueta cada parte. Origen y destino deben ser carpetas distintas.

El consolidador reemplaza los tomos numerados del mismo prefijo y elimina los sobrantes de ejecuciones anteriores. No edites directamente esos archivos si quieres conservar los cambios.

Google documenta un límite de 500 000 palabras por fuente y 50 fuentes por cuaderno en el nivel gratuito; pueden cambiar y también existen límites de tamaño: [ayuda oficial de NotebookLM](https://support.google.com/gemininotebook/answer/16215270?hl=en). El programa controla palabras, no bytes.

## Problemas habituales

- **No se genera ningún TXT:** comprueba que el vídeo tenga subtítulos disponibles para el idioma indicado.
- **Errores 403/429 o de autenticación:** YouTube puede bloquear las peticiones; prueba más tarde. Este proyecto no evita sus restricciones.
- **Deja de funcionar la descarga:** actualiza con `python -m pip install -U yt-dlp`.
- **Quedan frases raras o repetidas:** el limpiador reduce solapamientos comunes, pero no corrige errores de reconocimiento de voz.

## Ejecutar pruebas

```bash
python -m unittest discover -s tests -v
```

Las pruebas automatizadas no requieren YouTube. La descarga real depende de la disponibilidad de subtítulos y de los cambios del servicio.
