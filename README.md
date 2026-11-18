# Transcript Studio

**Una biblioteca local para los subtítulos de YouTube.** Descarga los subtítulos accesibles de vídeos, playlists y canales, conserva sus marcas de tiempo, ofrece búsqueda en la biblioteca y los exporta a TXT, Markdown, SRT, JSON o tomos para NotebookLM.

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
3. En **Descargas**, consulta progreso, pausa o reanuda. Un trabajo que termina con idiomas ausentes o vídeos sin subtítulos aparece como **Incompleto**, no como un éxito total. Puedes volver a intentarlo sin perder las pistas ya guardadas. Ante un bloqueo, queda `Bloqueado` y no reintenta indefinidamente.
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

- [Auditoría técnica y riesgos](docs/auditoria-2026-11.md)
- [Comparativa de herramientas y oportunidad de producto](docs/competencia-2026-11.md)
- [Roadmap con criterios de aceptación](docs/roadmap.md)
- [Pruebas, benchmarks y publicación](docs/quality.md)
- [Cómo contribuir](CONTRIBUTING.md) · [Seguridad](SECURITY.md) · [Cambios](CHANGELOG.md)
- [Arquitectura, API y checklist de integración](docs/architecture.md)
- [Documentación de yt-dlp](https://github.com/yt-dlp/yt-dlp)


## Copias, compatibilidad y Windows

- **Copias SQLite:** `python -m transcript_studio.database_backup backup --output "mi-copia.sqlite3"`. Comprueba con `verify --input "mi-copia.sqlite3"` y restaura únicamente en una **carpeta nueva**. [Instrucciones](docs/sqlite-backups.md).
- **Compatibilidad real con YouTube:** prueba opcional de tres vídeos con permiso expreso, sin cookies ni reintentos agresivos. [Protocolo manual](docs/youtube-compatibility.md).
- **Windows sin Python:** hay un workflow que construye un instalador **sin firmar** y lo prueba sin publicar releases. No incluye Deno; la descarga de YouTube puede necesitarlo. [Detalles del instalador](docs/windows-installer.md).

**Seguridad:** evita publicar transcripciones personales, bases de datos y cookies. Las migraciones no deben ejecutarse con dos instancias de Transcript Studio utilizando simultáneamente la misma carpeta de datos.

## Limitaciones

- Solo los subtítulos que YouTube permite obtener. Una cuenta o cookies no garantiza acceso ni evita 403/429.
- La cola funciona mientras el servidor esté iniciado. Los trabajos quedan guardados y se retoman al iniciar otra vez.
- Pausa y cancelación son cooperativas: una solicitud de red ya iniciada puede tardar en terminar.
- La búsqueda actual utiliza SQLite y paginación básica; no implementa un motor semántico ni traducciones.
- No es una aplicación multiusuario ni un servicio listo para exponerse a Internet. Utiliza únicamente `127.0.0.1`.
- No se dispone de un ejecutable instalador; se instala mediante Python.

Contribuciones y problemas reproducibles son bienvenidos. No publiques cookies ni datos de inicio de sesión en incidencias.

**Estado de publicación:** el repositorio continúa privado y todavía no tiene una licencia de distribución aprobada. La publicación como open source y las releases se decidirán tras revisión y autorización.
