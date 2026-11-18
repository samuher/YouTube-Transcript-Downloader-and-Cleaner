# Cambios

## Sin publicar — mantenimiento SQLite y empaquetado Windows (PR pendiente)

- Migraciones transaccionales del esquema SQLite desde instalaciones 0.2.0, conservando registros.
- Copias SQLite consistentes con WAL, verificación de integridad y restauración sin sobrescribir bibliotecas.
- Prueba opt-in de tres vídeos de YouTube, nunca automatizada contra la plataforma.
- Empaquetado PyInstaller e instalador Inno Setup sin firma, con pruebas Windows de arranque/reinicio/desinstalación y hashes SHA-256.
- Correcciones de cierre de conexiones SQLite en Windows.

**Los cambios aún no son una release, ni se han integrado en `main`.**


Se utiliza versionado semántico a partir de una futura publicación estable. **No se ha publicado una versión 1.0.**

## Sin publicar — propuesta P0 (PR pendiente)

- Los trabajos con vídeos sin subtítulos, con errores o idiomas parcialmente obtenidos terminan en estado `partial`, no `completed`.
- Los vídeos descargados parcialmente se pueden reintentar sin perder las pistas existentes.
- La interfaz permite reanudar trabajos `partial`.
- Se validan URL de listas de reproducción de YouTube.
- Se añaden pruebas de regresión, comprobación del empaquetado y propuestas automáticas de dependencias.

Estos cambios **no están en `main` mientras no se fusione el PR**.

## 0.2.0 — versión de código existente

- Aplicación local con FastAPI, biblioteca SQLite, cola persistente e interfaz web.
- Descarga de subtítulos disponibles y exportaciones TXT, Markdown, SRT, JSON y NotebookLM.
- Los scripts `descargar_transcripciones.py` y `Consolidador.py` se conservan por compatibilidad.

La fecha de publicación de una release oficial está por decidir.
