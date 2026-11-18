# Contribuir

Gracias por interesarte por Transcript Studio. Actualmente el repositorio es privado y **todavía no se ha definido una licencia pública**. No lo describas como open source ni redistribuyas el código sin una licencia aprobada.

## Antes de cambiar código

1. Abre un issue breve: problema, pasos de reproducción, comportamiento esperado y entorno.
2. Limita el cambio a una responsabilidad; conserva compatibilidad con la interfaz y los dos scripts antiguos cuando sea posible.
3. Crea una rama desde `main` y añade pruebas que reproduzcan el caso.
4. Ejecuta:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
ruff check --select E9,F63,F7,F82 src tests
python -m pip check
```

5. Abre un pull request explicando **qué se ha comprobado** y qué no ha podido verificarse.

Los tests no deben contactar YouTube, salvo integración manual y expresamente autorizada. Usa fixtures locales y proveedores simulados. No adjuntes subtítulos protegidos, cookies ni logs que contengan datos sensibles.

## Diseño

- `provider.py`: extracción de datos y clasificación de fallos.
- `captions.py`: conservación de pistas originales, limpieza y timestamps.
- `storage.py`: persistencia y consultas SQLite.
- `worker.py`: estados de trabajos y reintentos.
- `exporting.py`: exportaciones.
- `app.py` y `static/`: API local e interfaz.

Evita añadir servicios remotos, dependencias pesadas o procesadores de IA sin un caso de uso y pruebas concretas.
