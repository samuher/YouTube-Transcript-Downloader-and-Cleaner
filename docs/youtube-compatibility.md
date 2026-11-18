# Prueba de compatibilidad real con YouTube

Las pruebas automatizadas usan subtítulos simulados y no consultan YouTube. Para comprobar el comportamiento externo se requiere un ensayo **manual**, pequeño y autorizado.

## Preparación

Elige tres vídeos públicos sobre los que tengas derecho a procesar los subtítulos:

1. Un vídeo con subtítulos manuales del idioma elegido.
2. Un vídeo con subtítulos automáticos del idioma elegido.
3. Un vídeo sin subtítulos accesibles para el idioma elegido.

No utilices cookies, listas, canales ni vídeos privados en el script. Si aparece 403, 429 o una comprobación de bot, **detén la prueba** y no reintentes repetidamente.

## Ejecutar un ensayo limitado

Con `python -m pip install -e .` ejecutado:

```powershell
python scripts/yt_integration_smoke.py --manual "es:https://www.youtube.com/watch?v=ABCDEFGHIJK" --automatic "es:https://www.youtube.com/watch?v=LMNOPQRSTUV" --missing "es:https://www.youtube.com/watch?v=WXYZabcdefg" --consent --report "$HOME\Documents\studio-smoke.json"
```

Reemplaza los ID de ejemplo por identificadores reales, verifica que son públicos y que la descripción del tipo de subtítulo es correcta. **No inventamos vídeos de referencia porque la disponibilidad de pistas cambia**.

El script procesa como máximo tres vídeos, realiza una pausa mínima de 5 segundos, no usa sesión ni cookies, comprueba texto, timestamps y exportaciones, y anota versión de Python, `yt-dlp`, Deno, plataforma, fecha y resultados. Un 403/429 detiene el ensayo.

## Prueba de reanudación de la interfaz

1. Inicia `python -m transcript_studio` y crea un trabajo pequeño de cinco vídeos.
2. Comprueba que aparezcan algunos subtítulos y cierra la aplicación por terminal.
3. Reinicia con la misma carpeta de datos: los vídeos completados deben seguir visibles.
4. Verifica que trabajos interrumpidos continúan y que los vídeos ya descargados no se duplican.
5. Exporta TXT, SRT y JSON para contrastar los tiempos y contenido de la pista original.
6. Si el trabajo pasa a `blocked`, espera y revisa el mensaje antes de reanudar.

No hagas el ensayo sobre cientos de vídeos ni uses técnicas de evasión para obtener resultados favorables.

## Criterio de cierre del issue #7

Debe adjuntarse al issue un resumen sin secretos de los tres casos, fechas, versiones y errores. Hasta ese momento, el script es una **herramienta de validación, no un resultado de integración probado**.
