# Transcript Studio

**Una biblioteca local para los subtítulos de YouTube.** Descarga los subtítulos accesibles de vídeos y canales, conserva sus marcas de tiempo, ofrece búsqueda en la biblioteca y los exporta a TXT, Markdown, SRT, JSON o tomos para NotebookLM.

La aplicación tiene una interfaz web local. No exige cuentas, servicios externos de IA ni compilación de frontend. **No descarga el vídeo ni transcribe su audio.** Si YouTube bloquea el acceso a los subtítulos, no existe una garantía de recuperación.

## Instalar y abrir

Necesitas **Python 3.11 o superior** y una versión reciente de yt-dlp. En Windows abre PowerShell; en Linux/macOS, una terminal.

```bash
git clone https://github.com/samuher/YouTube-Transcript-Downloader-and-Cleaner.git
cd YouTube-Transcript-Downloader-and-Cleaner
python -m venv .venv
```

Activa el entorno virtual:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- Linux/macOS: `source .venv/bin/activate`

Después ejecuta:

```bash
python -m pip install -e .
python -m transcript_studio
```

Se abrirá **http://127.0.0.1:8765**. Si no se abre automáticamente, copia ese enlace en tu navegador. Para finalizar, vuelve a la terminal y pulsa `Ctrl+C`. Puedes usar `--no-browser` o `--port 8766`.

> YouTube cambia frecuentemente su sistema de acceso. La documentación de yt-dlp recomienda tener su paquete actualizado y, para soporte completo de YouTube, contar con un motor JavaScript compatible junto con yt-dlp-ejs. Consulta [yt-dlp](https://github.com/yt-dlp/yt-dlp) para los requisitos más recientes. Las cookies del navegador son opcionales y deben tratarse como credenciales privadas.

## Uso

1. En **Resumen**, pega un enlace de un vídeo o canal y selecciona idiomas (p. ej., `es,en`).
2. Prueba primero **5 vídeos**. Cuando funcione, pon **0** para intentar toda la pestaña `/videos`.
3. En **Descargas**, consulta progreso, pausa o reanuda. Ante un bloqueo, el trabajo queda `Bloqueado` y no reintenta indefinidamente.
4. Busca en **Biblioteca**, abre una transcripción o selecciona las que quieras exportar.
5. En **Exportaciones**, elige formato y descarga un ZIP. NotebookLM crea tomos limitados por palabras **y por bytes**.

Los datos permanecen en la carpeta local de la aplicación: `%LOCALAPPDATA%\TranscriptStudio` en Windows, `~/.local/share/transcript-studio` en Linux, `~/Library/Application Support/TranscriptStudio` en macOS. Puedes usar `python -m transcript_studio --data-dir "ruta"` para elegir otra ubicación.

Los scripts antiguos `descargar_transcripciones.py` y `Consolidador.py` se mantienen para compatibilidad. Los trabajos de esos scripts **no se importan automáticamente** en la nueva biblioteca SQLite; evita usar los dos flujos simultáneamente sobre la misma carpeta de resultados.

## Desarrollo y calidad

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
```

Hay pruebas unitarias y de API sin peticiones reales a YouTube. Las integraciones reales dependen de la disponibilidad del servicio y requieren pruebas específicas en una máquina con conexión.

- [Arquitectura, API y checklist de integración](docs/architecture.md)
- [Documentación de yt-dlp](https://github.com/yt-dlp/yt-dlp)

## Limitaciones

- Solo los subtítulos que YouTube permite obtener. Una cuenta o cookies no garantiza acceso ni evita 403/429.
- La cola funciona mientras el servidor esté iniciado. Los trabajos quedan guardados y se retoman al iniciar otra vez.
- Pausa y cancelación son cooperativas: una solicitud de red ya iniciada puede tardar en terminar.
- La búsqueda actual utiliza SQLite y paginación básica; no implementa un motor semántico ni traducciones.
- No es una aplicación multiusuario ni un servicio listo para exponerse a Internet. Utiliza únicamente `127.0.0.1`.
- No se dispone de un ejecutable instalador; se instala mediante Python.

Contribuciones y problemas reproducibles son bienvenidos. No publiques cookies ni datos de inicio de sesión en incidencias.
