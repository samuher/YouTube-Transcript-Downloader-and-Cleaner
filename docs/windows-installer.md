# Instalador Windows — versión de revisión sin firma

Se ha incorporado un empaquetado en **PyInstaller + Inno Setup**, con un workflow que ejecuta pruebas de Python, crea un instalador de usuario, abre el servidor local, comprueba persistencia tras reinicio y desinstala sin borrar la biblioteca.

**El archivo generado es un artefacto de CI privado, no una release pública ni un instalador firmado.**

## Obtener el artefacto

1. Abre el pull request y su workflow `Windows installer (unsigned preview)` en GitHub Actions.
2. Espera a que termine en verde.
3. En la sección *Artifacts*, descarga `transcript-studio-windows-preview-unsigned`.
4. Extrae el ZIP y revisa que incluya el instalador `.exe` y `SHA256SUMS.txt`.
5. Verifica el hash en PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 ".\TranscriptStudio-Setup-0.2.0-win-x64.exe"
```

Compara el hash con el archivo de suma del mismo workflow.

## Instalación

- El instalador incluye el intérprete de Python y las dependencias empaquetadas: no necesitas instalar Python en el equipo de destino.
- Para **compatibilidad completa con YouTube**, puede seguir siendo necesario instalar Deno u otro runtime JS compatible según `yt-dlp`. El instalador no incorpora Deno.
- Usa instalador por usuario sin permisos de administrador; el programa sigue escuchando solo en `127.0.0.1`.
- El desinstalador **no elimina** la base de datos ni las transcripciones que estén en `%LOCALAPPDATA%\TranscriptStudio`.

## Limitaciones de seguridad

El instalador **no está firmado**. Windows SmartScreen puede mostrar advertencias. No lo publiques a terceros como producto verificado.

Antes de distribuir: verificar la procedencia y licencias de dependencias, firmar el binario con un certificado adecuado, probar en VM Windows limpia, instalar y desinstalar, actualizar desde una instalación anterior y conservar una copia de seguridad de SQLite. La verificación en el runner CI no sustituye una prueba independiente en un Windows limpio.

## Construir manualmente en Windows

Instala Python 3.12, Inno Setup 6 y Git. Desde el repositorio:

```powershell
python -m pip install -e . "pyinstaller>=6.13,<7"
.\packaging\windows\build.ps1
```

El instalador se genera en `dist\installer\`. Nunca se publica automáticamente.
