# Roadmap de producto

Objetivo inicial: utilidad local y fiabilidad para estudiantes, investigadores y desarrolladores. Versión actual en `main`: 0.2.0. Las tareas marcadas como propuestas no se consideran publicadas.

| Prioridad | Tarea | Archivos principales | Dependencias | Dificultad / riesgo | Criterio de aceptación |
| --- | --- | --- | --- | --- | --- |
| P0 | Estados de trabajo honestos | `storage.py`, `worker.py`, `app.py`, JS | Ninguna | Media / medio | Nunca `completed` con vídeos `failed`, `missing` o `partial`; pruebas de reanudación |
| P0 | Integridad multilingüe | `storage.py`, `worker.py` | Cambio anterior | Media / alto | Guardar las pistas parciales, reintentar las ausentes y no borrar las ya persistidas |
| P0 | Bloqueos y privacidad | `provider.py`, API | Dependencias yt-dlp | Alta / alto | 403 y bot no desencadenan bucles; no se registran cookies |
| P1 | Playlists | `provider.py`, tests | URL validada | Baja / medio | URL de playlist aceptada; URL manipulada rechazada |
| P1 | Mantenimiento CI | `tests.yml`, Dependabot | Ninguna | Baja / bajo | pytest, syntax JS, lint crítico, `pip check` y build correctos |
| P1 | Migraciones y backup SQLite | `storage.py`, CLI, tests | Diseño schema-version | Media / alto | Actualizar una base anterior sin pérdida y restaurar copia verificada |
| P1 | Recuperación por idioma | `worker.py`, UI | Modelo estado parcial | Media / medio | Usuario ve el idioma que falta y reintenta solo lo necesario |
| P1 | Pruebas de formatos reales | `tests/fixtures`, `captions.py` | Fixtures autorizadas | Media / medio | 100% fixtures de subtítulos conservan los timestamps y texto verificable |
| P2 | Buscador por timestamps | SQLite, frontend | Mejoras búsqueda | Media / bajo | Al hacer clic en un resultado abre el segundo asociado |
| P2 | Instalador Windows | packaging y CI | Fase 1 estable | Alta / alto | Instalación en Windows limpio sin Python preinstalado |
| P2 | Editor reversible | UI, almacenamiento | Historial de versiones | Alta / medio | Se conserva el original y se pueden deshacer cambios |
| P3 | ASR local opcional | nuevo módulo aislado | Permisos, recursos | Alta / alto | Solo archivos aportados lícitamente, con coste y privacidad explicados |

## Criterios para una versión 1.0

1. Pruebas de CI en Python soportado, wheel/sdist válidos.
2. Un vídeo manual, uno automático y un canal pequeño descargados satisfactoriamente en una red autorizada.
3. Bloqueos y ausencias reflejados en estados distintos, sin pérdida de datos.
4. Prueba de pausa, cierre, reinicio y recuperación con SQLite.
5. Exportaciones verificadas para TXT, MD, SRT, JSON y NotebookLM.
6. Política de seguridad, licencia aprobada y procedimiento de instalación estable.
7. Guía de incidencias y una release con changelog y limitaciones conocidas.

El criterio de éxito es **medible**, no el número de funcionalidades.

## Estado de los issues #6, #7 y #8

- **#6**: migraciones + backup/restore con pruebas automatizadas implementadas en la rama de trabajo. Falta validar una actualización personal en Windows con una copia real.
- **#7**: disponible el protocolo y script manual bajo consentimiento; pendiente el ensayo externo autorizado y adjuntar evidencias. **No dar por terminado** solo porque el script exista.
- **#8**: workflow y scripts de instalación creados; la aprobación de CI, pruebas en Windows limpio y firma del instalador son requisitos de publicación, no tareas ya finalizadas.
