import os
import argparse


def consolidar_textos(carpeta_origen, carpeta_destino=None,
                       limite_palabras_por_lote=450000, nombre_base=None):
    """
    Agrupa los .txt de carpeta_origen en 'megarchivos' respetando el límite
    de palabras por fuente de NotebookLM (500.000 palabras), dejando margen
    de seguridad (450.000 por defecto) en lugar de agrupar por número fijo
    de archivos.
    """
    if not carpeta_destino:
        carpeta_destino = "notebooklm_listo"

    if not nombre_base:
        # Usa el nombre de la carpeta de origen para nombrar los tomos automáticamente
        nombre_base = os.path.basename(os.path.normpath(carpeta_origen)) or "Fuente"
        nombre_base = f"{nombre_base}_Tomo"

    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    # Buscar solo los archivos .txt ya limpios (orden alfabético para que sea reproducible)
    archivos_txt = sorted(f for f in os.listdir(carpeta_origen) if f.endswith('.txt'))

    if not archivos_txt:
        print(f"No se encontraron archivos .txt en '{carpeta_origen}' para consolidar.")
        return

    lote_actual = 1
    contador_videos_lote = 0
    palabras_lote = 0
    texto_consolidado = ""
    total_lotes_creados = []

    print(f"Empezando a empaquetar {len(archivos_txt)} archivos "
          f"(límite: {limite_palabras_por_lote:,} palabras por lote)...")

    def guardar_lote(numero_lote, texto, num_archivos, num_palabras):
        nombre_salida = os.path.join(carpeta_destino, f"{nombre_base}_{numero_lote}.txt")
        with open(nombre_salida, 'w', encoding='utf-8') as f_out:
            f_out.write(texto)
        print(f"Guardado: {nombre_salida} ({num_archivos} archivos, {num_palabras:,} palabras)")
        total_lotes_creados.append(nombre_salida)

    for archivo in archivos_txt:
        ruta_archivo = os.path.join(carpeta_origen, archivo)

        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()

        palabras_archivo = len(contenido.split())

        if palabras_archivo > limite_palabras_por_lote:
            print(f"⚠️  Aviso: '{archivo}' tiene {palabras_archivo:,} palabras él solo, "
                  f"por encima del límite por lote. Se guardará en su propio tomo.")

        # Si añadir este archivo se pasa del límite, cerramos el lote actual primero
        if palabras_lote > 0 and (palabras_lote + palabras_archivo) > limite_palabras_por_lote:
            guardar_lote(lote_actual, texto_consolidado, contador_videos_lote, palabras_lote)
            lote_actual += 1
            contador_videos_lote = 0
            palabras_lote = 0
            texto_consolidado = ""

        # Añadir un separador claro con el nombre del archivo original para que la IA lo cite bien
        texto_consolidado += f"\n\n=========================================\n"
        texto_consolidado += f"FUENTE: {archivo.replace('.txt', '')}\n"
        texto_consolidado += f"=========================================\n\n"
        texto_consolidado += contenido

        contador_videos_lote += 1
        palabras_lote += palabras_archivo

    if contador_videos_lote > 0:
        guardar_lote(lote_actual, texto_consolidado, contador_videos_lote, palabras_lote)

    print(f"\n¡Listo! Se generaron {len(total_lotes_creados)} archivos en '{carpeta_destino}'.")

    if len(total_lotes_creados) > 50:
        print(f"⚠️  Atención: se generaron {len(total_lotes_creados)} archivos, por encima del límite "
              f"de 50 fuentes del plan gratuito de NotebookLM. Opciones: reparte los tomos en varios "
              f"notebooks, o sube 'limite_palabras_por_lote' (nunca por encima de 500.000, el máximo real de NotebookLM).")
    else:
        print("Estás dentro del límite de 50 fuentes del plan gratuito de NotebookLM.")


def pedir_datos_interactivos():
    """Pregunta los datos por pantalla cuando no se pasan como argumentos."""
    print("=== Consolidador de transcripciones para NotebookLM ===\n")
    carpeta_origen = input("Carpeta con los .txt sueltos a consolidar: ").strip()

    carpeta_destino = input(
        "Carpeta donde guardar los tomos consolidados (Enter para 'notebooklm_listo'): "
    ).strip()

    limite_input = input(
        "Límite de palabras por tomo (Enter para 450.000, máximo recomendado 450.000-500.000): "
    ).strip()
    limite_palabras = int(limite_input) if limite_input.isdigit() else 450000

    nombre_base = input(
        "Nombre para los tomos, ej. 'MiCanal' (Enter para usarlo según la carpeta de origen): "
    ).strip()

    return carpeta_origen, (carpeta_destino or None), limite_palabras, (nombre_base or None)


def main():
    parser = argparse.ArgumentParser(
        description="Consolida archivos .txt en megarchivos aptos para subir a NotebookLM."
    )
    parser.add_argument('-o', '--origen', help="Carpeta con los .txt sueltos a consolidar")
    parser.add_argument('-d', '--destino', help="Carpeta donde guardar los tomos consolidados")
    parser.add_argument(
        '-l', '--limite', type=int, default=None,
        help="Límite de palabras por tomo (por defecto: 450000)"
    )
    parser.add_argument('-n', '--nombre', help="Prefijo para nombrar los tomos generados")
    args = parser.parse_args()

    if args.origen:
        carpeta_origen = args.origen
        carpeta_destino = args.destino
        limite_palabras = args.limite or 450000
        nombre_base = args.nombre
    else:
        carpeta_origen, carpeta_destino, limite_palabras, nombre_base = pedir_datos_interactivos()

    if not carpeta_origen:
        print("No se ha indicado ninguna carpeta de origen. Saliendo.")
        return

    consolidar_textos(carpeta_origen, carpeta_destino, limite_palabras, nombre_base)


if __name__ == "__main__":
    main()