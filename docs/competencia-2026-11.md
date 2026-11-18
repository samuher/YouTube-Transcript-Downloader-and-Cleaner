# Investigación competitiva — noviembre de 2026

La comparación se basa en documentación pública, páginas oficiales y problemas reportados por usuarios. **No** se ha realizado una comparación de tiempos de descarga ni de precisión, por lo que no se declara un ganador.

| Alternativa | Capacidades documentadas | Limitación / oportunidad para nosotros | Fuente |
| --- | --- | --- | --- |
| yt-dlp | Gran variedad de fuentes, CLI y extracción de subtítulos, actualizaciones frecuentes | No es una biblioteca de conocimiento local con interfaz de revisión integrada | https://github.com/yt-dlp/yt-dlp |
| youtube-transcript-api | API Python para obtener pistas y formatearlas a TXT/JSON/SRT/VTT | Alcance orientado a API; su documentación reconoce límites de cookies | https://github.com/jdepoix/youtube-transcript-api |
| DownSub | Descarga de subtítulos, playlists, formatos, traducción y herramientas de IA | Producto online; evaluar necesidades de trabajo local sin depender de servicios adicionales | https://app.downsub.com/ |
| Glasp | Extensión para ver transcripciones, resúmenes, lectura y exportación de apuntes | Su objetivo principal es lectura/anotación, no una cola local inspeccionable con base SQLite | https://glasp.co/youtube-summary |
| Tactiq | Generador de transcripciones y herramientas de análisis/colaboración | Más orientado a flujos de reuniones y análisis, aunque también tiene herramientas YouTube | https://help.tactiq.io/en/articles/9832255-how-to-use-tactiq-to-transcribe-youtube-videos |

## Señales de usuarios y limitaciones

- Incidencia abierta de yt-dlp el **17-11-2026** sobre HTTP 429: https://github.com/yt-dlp/yt-dlp/issues/18073.
- Incidencia de subtítulos y 429 ampliamente discutida: https://github.com/yt-dlp/yt-dlp/issues/13831.
- Discusión de noviembre de 2026 sobre fallos de subtítulos automáticos: https://www.reddit.com/r/youtubedl/comments/1xm1qdz/.
- La documentación de youtube-transcript-api menciona problemas de autenticación por cookies: https://github.com/jdepoix/youtube-transcript-api/blob/master/README.md.

Los comentarios comunitarios son indicios, no medidas representativas de incidencia. No extrapolar a una tasa global de fallos.

## Usuario principal y propuesta de valor

**Principal:** persona que estudia, investiga o desarrolla y necesita conservar, consultar y exportar muchas transcripciones sin servicios de IA obligatorios.

**Propuesta verificable (objetivo):** para un conjunto de vídeos con subtítulos accesibles, conservar cada pista original y limpia, explicar los fallos por vídeo/idioma, reanudar sin duplicados y exportar una biblioteca local que pueda auditarse.

### Qué implementar, qué posponer y qué descartar

- **CORE:** acceso con límites, registros, estado real, normalización, marca temporal, persistencia y exportación.
- **ADVANCED:** playlists, búsqueda en segmentos, reproducir desde el timestamp, etiquetas y lotes de exportación.
- **OPTIONAL:** subtitulado de medios aportados legalmente mediante ASR, resúmenes optativos, integración con notas.
- **REJECTED por ahora:** sincronización multiusuario, dependencia obligatoria de IA, microservicios, infraestructura cloud y técnicas para eludir accesos.

## Cómo comparar antes de afirmar ventajas

Preparar una muestra autorizada y reproducible que incluya 10 vídeos con pistas manuales y automáticas, varios idiomas, un vídeo sin pista y un canal pequeño; fijar entorno, fecha, red y versiones. Medir:

- Pistas correctas obtenidas / pistas accesibles del conjunto.
- Tiempo total con las mismas restricciones y número de solicitudes.
- Integridad temporal: segmentos exportados vs. fuente.
- Resumen de estados: no ocultar fallos.
- Recuperación: segundo intento sin repetir descargas completadas.
- Fricción de instalación y uso.

Registrar todos los resultados, incluyendo errores; nunca inventar porcentajes o afirmar superioridad sin datos comparables.
