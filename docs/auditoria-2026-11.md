# Auditoría técnica — 18 de noviembre de 2026

Base inspeccionada: rama `main`, revisión inicial `63e0b784`. Código revisado: `provider.py`, `worker.py`, `storage.py`, `captions.py`, `exporting.py`, `app.py`, `static/`, `pyproject.toml`, pruebas y GitHub Actions.

La auditoría es **estática** y se complementa con pruebas de CI. No se ha validado de extremo a extremo contra YouTube real ni se ha realizado un pentest. Los estados "implementado" no equivalen a certificar funcionamiento universal.

| Componente | Estado verificado en código | Problema o riesgo | Prioridad | Acción |
| --- | --- | --- | --- | --- |
| Motor de extracción | Implementado con yt-dlp | YouTube puede exigir autenticación, rechazar subtítulos o devolver 429 | P0 | Mantener bloqueos acotados y registrar sin insistir |
| Progreso y reanudación | SQLite conserva trabajos y cambia `running` a `queued` al abrir | Los vídeos con algunos idiomas faltantes se marcaban `downloaded` | P0 | Estado `partial`, comprobación por idioma y reintentos |
| Estado final | `worker.py` terminaba en `completed` aun con vídeos `failed` o `missing` | Mensaje de éxito incorrecto | P0 | Distinguir `completed` y `partial` |
| Subtítulos | Se preserva VTT/SRT original, segmentos y texto limpio | Solapamientos y estilos raros pueden alterar la limpieza | P1 | Fixtures de variantes reales, revisión lado a lado |
| Biblioteca | SQLite transaccional con índice por vídeo/idioma | No hay migraciones versionadas ni copias automáticas | P1 | Migraciones verificadas y copia en caliente |
| Exportación | TXT, MD, SRT, JSON y ZIP NotebookLM | Sin comparación automática con herramientas externas ni estrés de ficheros grandes | P1 | Fixtures multilingües y benchmarks |
| URL | Admitía vídeo y pestañas de canal | La URL de playlist era rechazada | P1 | Admitir playlist validada |
| API local | FastAPI en loopback, validación Host y Origin | No hay modelo de usuarios; exponer el puerto sería inseguro | P0 | Mantener uso exclusivo en `127.0.0.1` |
| Frontend | HTML/CSS/JS estáticos sin CDN | La interfaz no representaba estado parcial | P1 | Añadir estado y acción de recuperación |
| Calidad | pytest y comprobación JS en 3 versiones de Python | Sin chequeos de dependencias, empaquetado o lint crítico | P1 | Extender CI y Dependabot |
| Distribución | `pip install -e .`; sin binarios | Instalación difícil para personas no técnicas | P2 | Validar wheel y posteriormente instalador Windows |
| Repositorio | Privado, documentación básica | Falta licencia pública aprobada y política de contribución | P1 | Documentar; no cambiar visibilidad ni licencia unilateralmente |

## Regresiones que deben evitarse

1. Un vídeo descargado en `es` no puede darse por completo si también se pidió `en`.
2. `en-orig` puede representar una pista en inglés; no se considera automáticamente disponible un idioma inexistente.
3. Un error de subtítulos en el vídeo N no puede convertir el trabajo en éxito total.
4. Un bloqueo 403/429 persistente debe detener el procesamiento y preservar los datos ya guardados.
5. Pausar o cancelar durante una solicitud puede tardar, pero no debe terminar en `completed` incorrectamente.
6. Importar un módulo no debe iniciar peticiones a YouTube.
7. El proveedor externo nunca debe recibir URL arbitrarias no validadas.
8. No deben publicarse cookies, tokens, SQLite personales ni logs con datos privados.

## Deuda técnica todavía abierta

- Migraciones SQLite y backup/restore con prueba de recuperación.
- Sincronización de progreso en UI mediante datos más detallados; mejor diagnóstico por vídeo/idioma.
- Gestión de peticiones grandes: bibliotecas y exportaciones limitadas por memoria y paginación.
- Actualización de metadatos de vídeos previamente vistos; gestión de títulos que cambian.
- Comprobación visual de accesibilidad, navegación por teclado y tamaños de pantalla.
- Estrategia de licencia, reputación del paquete, distribución Windows y firma de binarios.

## Resultado de esta iteración

La rama `fix/p0-job-integrity-quality` implementa reparación de estados parciales, verificación de idiomas, playlists, pruebas de regresión y controles CI. No fusionar ni publicar una release hasta revisar el PR y los controles de aceptación.
