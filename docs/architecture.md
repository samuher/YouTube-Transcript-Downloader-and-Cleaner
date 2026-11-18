# Arquitectura

`provider.py` es el único módulo que consulta YouTube mediante yt-dlp. `captions.py` conserva las marcas temporales originales y genera texto limpiado sin modelos de pago. `worker.py` procesa una cola secuencial de trabajos de SQLite (`storage.py`), con interrupciones cooperativas y reintentos limitados. `app.py` expone una API HTTP exclusivamente local, con comprobación de Host y Origin; `static/` sirve una interfaz sin dependencias de CDN ni compilación JS. `exporting.py` crea archivos ZIP y verifica límites de palabras y bytes.

- La biblioteca y los trabajos se guardan fuera del repositorio, en la carpeta de datos del usuario.
- Un trabajo `running` pasa a `queued` al reiniciar la aplicación, salvo los estados `blocked`, `paused` y `cancelled`, que requieren intervención del usuario.
- Pausar o cancelar entre dos vídeos es inmediato; durante una petición de red puede retrasarse hasta que termine esa petición.
- No existe servidor remoto, ni autenticación multiusuario. **No publiques el puerto ni cambies la dirección de escucha de 127.0.0.1** sin añadir autenticación, TLS y controles de acceso.
- La API no permite consultar rutas arbitrarias ni ejecutar comandos; las cookies solo se pasan a yt-dlp desde la sesión local opcional.
- La aplicación no transcribe audio ni elimina controles de acceso de YouTube.

## API

- `GET /api/health`, `/api/stats`, `/api/jobs`, `/api/jobs/{id}`, `/api/transcripts`, `/api/transcripts/{id}`
- `POST /api/jobs`, `/api/jobs/{id}/pause`, `/api/jobs/{id}/resume`, `/api/jobs/{id}/cancel`
- `GET /api/export?ids=1,2&format=txt|md|json|srt|notebooklm`

## Pruebas de integración real

1. Ejecutar en una red doméstica sin VPN ni proxy y con la versión actual de yt-dlp.
2. Probar un único vídeo con subtítulos manuales; comprobar TXT, JSON y SRT.
3. Probar cinco vídeos del mismo canal, guardar los resultados y volver a ejecutar: comprobar que no duplica.
4. Probar un canal con algunos vídeos sin subtítulos.
5. Ante un 403 o 429, dejar de solicitar vídeos y revisar el estado `blocked` y la reanudación tras el bloqueo.
6. No introducir credenciales reales en tests o CI.
