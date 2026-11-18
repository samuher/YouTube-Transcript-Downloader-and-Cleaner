"""Agrupa transcripciones TXT en tomos con un límite de palabras comprobable."""

import argparse
import re
import sys
import tempfile
from pathlib import Path

LIMITE_PREDETERMINADO = 450_000
LIMITE_MAXIMO = 500_000
ARCHIVOS_A_IGNORAR = {"archivo_descargados.txt"}


def _encabezado(nombre, parte=None):
    etiqueta = f"FUENTE: {nombre}"
    if parte is not None:
        etiqueta += f" (parte {parte})"
    return f"\n\n---\n{etiqueta}\n---\n\n"


def consolidar_textos(carpeta_origen, carpeta_destino=None,
                       limite_palabras_por_lote=LIMITE_PREDETERMINADO, nombre_base=None):
    origen = Path(carpeta_origen).expanduser().resolve()
    destino = Path(carpeta_destino or "notebooklm_listo").expanduser().resolve()
    if not origen.is_dir():
        raise ValueError(f"La carpeta de origen no existe: {origen}")
    if origen == destino:
        raise ValueError("Origen y destino deben ser carpetas distintas")
    if not 1 <= limite_palabras_por_lote <= LIMITE_MAXIMO:
        raise ValueError(f"El límite debe estar entre 1 y {LIMITE_MAXIMO:,} palabras")
    base = nombre_base if nombre_base is not None else f"{origen.name}_Tomo"
    base = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", base).strip(" ._")
    if not base or base in {".", ".."}:
        raise ValueError("El nombre de los tomos no puede estar vacío")

    archivos = sorted((p for p in origen.iterdir() if p.is_file() and p.suffix.lower() == ".txt"
                       and p.name.lower() not in ARCHIVOS_A_IGNORAR), key=lambda p: p.name.casefold())
    if not archivos:
        print(f"No hay archivos TXT para consolidar en {origen}")
        return []

    destino.mkdir(parents=True, exist_ok=True)
    creados = []
    partes = []
    palabras_tomo = 0
    fuentes_tomo = 0

    def guardar():
        nonlocal partes, palabras_tomo, fuentes_tomo
        if not partes:
            return
        ruta = destino / f"{base}_{len(creados) + 1}.txt"
        temporal = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=destino, suffix=".tmp", delete=False) as f:
                temporal = Path(f.name)
                f.write("".join(partes).lstrip() + "\n")
            temporal.replace(ruta)
        finally:
            if temporal is not None and temporal.exists():
                temporal.unlink()
        cuenta_real = len(ruta.read_text(encoding="utf-8").split())
        assert cuenta_real <= limite_palabras_por_lote, "Se ha superado el límite configurado"
        creados.append(ruta)
        print(f"{ruta.name}: {cuenta_real:,} palabras, {fuentes_tomo} fragmentos")
        partes = []
        palabras_tomo = 0
        fuentes_tomo = 0

    def agregar(texto, encabezado):
        nonlocal palabras_tomo, fuentes_tomo
        n = len(encabezado.split()) + len(texto.split())
        if n > limite_palabras_por_lote:
            raise ValueError("Un fragmento supera el límite configurado")
        if palabras_tomo + n > limite_palabras_por_lote:
            guardar()
        partes.append(encabezado + texto)
        palabras_tomo += n
        fuentes_tomo += 1

    for archivo in archivos:
        contenido = archivo.read_text(encoding="utf-8-sig").strip()
        if not contenido:
            print(f"Omitido (vacío): {archivo.name}")
            continue
        encabezado = _encabezado(archivo.stem)
        palabras = contenido.split()
        if len(palabras) + len(encabezado.split()) <= limite_palabras_por_lote:
            agregar(contenido, encabezado)
            continue

        if partes:
            guardar()
        comienzo = 0
        parte = 1
        while comienzo < len(palabras):
            cabecera = _encabezado(archivo.stem, parte)
            capacidad = limite_palabras_por_lote - len(cabecera.split())
            if capacidad <= 0:
                raise ValueError("Límite demasiado pequeño para incluir el nombre de la fuente")
            trozo = " ".join(palabras[comienzo:comienzo + capacidad])
            agregar(trozo, cabecera)
            comienzo += capacidad
            parte += 1

    guardar()
    patron = re.compile(rf"^{re.escape(base)}_(\d+)\.txt$", re.IGNORECASE)
    for archivo in destino.iterdir():
        if archivo.is_file() and patron.fullmatch(archivo.name) and archivo not in creados:
            archivo.unlink()
    print(f"Tomos generados: {len(creados)} en {destino}")
    return creados


def main(argv=None):
    parser = argparse.ArgumentParser(description="Agrupa TXT sin superar el límite de palabras por tomo.")
    parser.add_argument("-o", "--origen", help="Carpeta con TXT individuales")
    parser.add_argument("-d", "--destino", help="Carpeta de salida (notebooklm_listo)")
    parser.add_argument("-l", "--limite", type=int, default=None, help="Máximo de palabras por tomo (450000)")
    parser.add_argument("-n", "--nombre", help="Prefijo del nombre de los tomos")
    args = parser.parse_args(argv)
    if args.origen:
        origen, destino, limite, nombre = args.origen, args.destino, args.limite or LIMITE_PREDETERMINADO, args.nombre
    else:
        origen = input("Carpeta con los TXT: ").strip()
        destino = input("Carpeta de salida (Enter = notebooklm_listo): ").strip() or None
        limite_txt = input("Límite de palabras (Enter = 450000): ").strip()
        nombre = input("Prefijo de tomos (Enter = automático): ").strip() or None
        try:
            limite = int(limite_txt) if limite_txt else LIMITE_PREDETERMINADO
        except ValueError:
            print("Error: introduce un número entero", file=sys.stderr)
            return 1
    try:
        consolidar_textos(origen, destino, limite, nombre)
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
