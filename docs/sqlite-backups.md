# SQLite: migraciones, copias y restauración

## Qué cambia

Transcript Studio comprueba la versión del esquema al abrir `library.sqlite3`.
Las bases creadas por la versión 0.2.0 tenían `PRAGMA user_version=0`.
La nueva migración crea las tablas que falten y añade el campo `last_attempt_at` a los intentos de vídeo, conservando las filas existentes. La migración usa transacciones; si falla, se revierte.

Si una base fue modificada con una versión **más reciente** de la aplicación, no se abrirá con una versión antigua. Esto evita cambios accidentales por incompatibilidad.

**Antes de actualizar desde una instalación importante, haz una copia.**

## Copia de seguridad con la aplicación instalada

En PowerShell, dentro del entorno virtual del proyecto:

```powershell
python -m transcript_studio.database_backup backup --output "$HOME\Documents\TranscriptStudio-backup.sqlite3"
```

La copia incluye cambios confirmados que todavía estén en el WAL y se verifica con `PRAGMA integrity_check`. El programa nunca sobrescribe una copia existente. Para una ubicación de datos personalizada:

```powershell
python -m transcript_studio.database_backup backup --data-dir "D:\TranscriptStudio" --output "D:\Backups\studio.sqlite3"
```

Verificación independiente:

```powershell
python -m transcript_studio.database_backup verify --input "D:\Backups\studio.sqlite3"
```

La salida incluye versión del esquema, tamaño y recuentos de trabajos, vídeos y transcripciones.

## Restaurar sin perder tu biblioteca actual

**Cierra Transcript Studio** y elige una carpeta NUEVA:

```powershell
python -m transcript_studio.database_backup restore --input "D:\Backups\studio.sqlite3" --data-dir "D:\TranscriptStudioRestaurado"
```

El comando crea `D:\TranscriptStudioRestaurado\library.sqlite3` después de validar la copia. Nunca sobrescribe una base existente.

Después inicia la aplicación apuntando a esa carpeta:

```powershell
python -m transcript_studio --data-dir "D:\TranscriptStudioRestaurado"
```

Si el resultado es correcto, conserva la biblioteca anterior hasta validar a mano que los datos importantes se han restaurado. Una copia de `library.sqlite3` **no incluye** credenciales almacenadas en el navegador ni archivos de exportación guardados fuera de la base.

## Limitaciones

- La restauración no fusiona dos bibliotecas; crea una nueva.
- Un archivo corrupto o de esquema más reciente se rechaza.
- No uses copiar/pegar del archivo SQLite activo con WAL como sustituto del comando de backup.
- No sincronices en vivo una misma base SQLite entre dos equipos con herramientas de archivos.
- Antes de publicar o distribuir, falta una prueba manual de actualización y restauración en Windows.
