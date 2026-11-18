# Pruebas y publicación

## Pruebas repetibles (sin YouTube)

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
ruff check --select E9,F63,F7,F82 src tests
python -m pip check
python -m pip install build
python -m build --wheel --sdist
node --check src/transcript_studio/static/app.js
```

En GitHub Actions estas comprobaciones se ejecutan en Linux con Python 3.11, 3.12 y 3.13. Se prueban estados parciales, SQLite, normalización, API local, subtítulos y exportaciones mediante proveedores simulados.

**No** se ha validado una descarga real de YouTube ni se ha generado un benchmark comparativo. No presentar las pruebas unitarias como una garantía de compatibilidad externa.

## Integración manual

1. Instalar en una máquina personal con Python compatible, yt-dlp actualizado y motor JavaScript compatible.
2. Probar un vídeo público con subtítulos manuales y otro con subtítulos automáticos accesibles, con permiso para procesarlos.
3. Verificar idioma, contenido y timestamps contra el vídeo original.
4. Añadir un canal con 5 vídeos. Confirmar estados `completed`, `partial`, `blocked` según resultados.
5. Repetir el trabajo para comprobar que no duplica transcripciones ni sobrescribe datos válidos.
6. Simular la interrupción local y volver a abrir la aplicación.
7. Exportar a TXT, MD, SRT, JSON y NotebookLM; abrir los archivos y comprobar integridad.
8. En caso de 403/429, **detener** pruebas; nunca bombardear el servicio ni usar evasiones.

Registrar fecha, versión de yt-dlp, versión de Python, plataforma, número de pistas solicitadas/obtenidas y errores. No publicar cookies, IPs privadas ni información de cuenta.

## Benchmark reproducible

No se proporcionan tiempos de rendimiento hasta disponer de una muestra y de medidas reales. Para comparar con otra herramienta se usarán **exactamente** las mismas URL autorizadas, plataforma, condiciones de red, idiomas, tiempo de espera y límites.

Medidas: número de pistas correctas, porcentaje de estados fieles, latencia por vídeo, uso máximo de memoria, cantidad de peticiones, recuperación sin duplicados y errores. Publicar tanto éxitos como fallos.

## Política de publicación

- Rama de trabajo → PR → CI → revisión humana → fusión aprobada.
- Dependabot abre PR, no se configura auto-merge.
- No publicar nueva release o cambiar visibilidad/licencia hasta aprobación expresa.
- Toda release debe incluir instrucciones, checksums si hay binarios y cambios conocidos.
