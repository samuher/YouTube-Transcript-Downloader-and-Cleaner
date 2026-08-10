import yt_dlp
import os
import re
import argparse
from urllib.parse import urlparse


def limpiar_vtt_a_txt(ruta_vtt):
    """Abre el archivo .vtt, elimina tiempos y etiquetas, y lo convierte a un .txt limpio"""
    try:
        with open(ruta_vtt, 'r', encoding='utf-8') as f:
            lineas = f.readlines()

        texto_limpio = []
        linea_anterior = ""

        for linea in lineas:
            # 1. Ignorar cabeceras y líneas de tiempo (ej. 00:00:01.000 --> 00:00:02.000)
            if "WEBVTT" in linea or "-->" in linea or "Kind:" in linea or "Language:" in linea:
                continue

            # 2. Eliminar todas las etiquetas <00:00:00> y <c>
            linea_limpia = re.sub(r'<[^>]+>', '', linea).strip()

            # 3. Guardar solo si tiene texto y evitar que YouTube repita la misma frase dos veces
            if linea_limpia and linea_limpia != linea_anterior:
                texto_limpio.append(linea_limpia)
                linea_anterior = linea_limpia

        # Guardar como un archivo .txt plano
        ruta_txt = ruta_vtt.replace('.vtt', '.txt')
        with open(ruta_txt, 'w', encoding='utf-8') as f:
            f.write(" ".join(texto_limpio))  # Une todo separando con espacios

        # Borrar el archivo .vtt original que ya no necesitamos
        os.remove(ruta_vtt)

    except Exception as e:
        print(f"Error al limpiar {ruta_vtt}: {e}")


def normalizar_url_canal(url_canal):
    """
    Asegura que la URL apunte a la pestaña /videos del canal.
    Si el usuario pega solo la URL raíz, yt-dlp también rastrearía Shorts,
    directos y todas las playlists, descargando vídeos repetidos.
    """
    url_canal = url_canal.strip().rstrip('/')
    if url_canal.endswith(('/videos', '/shorts', '/streams', '/playlists')):
        return url_canal
    return url_canal + '/videos'


def nombre_carpeta_desde_url(url_canal):
    """Genera automáticamente un nombre de carpeta legible a partir de la URL del canal."""
    partes = urlparse(url_canal).path.strip('/').split('/')
    nombre = partes[0] if partes else 'canal'
    nombre = nombre.lstrip('@')
    nombre = re.sub(r'[^A-Za-z0-9_-]', '_', nombre)
    return nombre or 'canal'


def descargar_transcripciones_canal(url_canal, carpeta_destino=None, idiomas=('en',)):
    url_canal = normalizar_url_canal(url_canal)

    if not carpeta_destino:
        carpeta_destino = os.path.join('transcripciones', nombre_carpeta_desde_url(url_canal))

    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': list(idiomas),
        'subtitlesformat': 'vtt',
        'outtmpl': f'{carpeta_destino}/%(uploader)s - %(upload_date)s - %(title)s.%(ext)s',
        'ignoreerrors': True,
        # Evita reprocesar el mismo vídeo si aparece en varias playlists del canal,
        # y permite reanudar sin repetir descargas si se corta la ejecución.
        'download_archive': os.path.join(carpeta_destino, 'archivo_descargados.txt'),
    }

    print(f"Canal: {url_canal}")
    print(f"Idiomas de subtítulos: {', '.join(idiomas)}")
    print(f"Guardando en: {carpeta_destino}\n")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url_canal])

    print("\n¡Descargas completadas! Limpiando el código basura de los archivos...")

    for archivo in os.listdir(carpeta_destino):
        if archivo.endswith(".vtt"):
            ruta_completa = os.path.join(carpeta_destino, archivo)
            limpiar_vtt_a_txt(ruta_completa)

    print(f"¡Proceso 100% finalizado! Tienes tus archivos .txt limpios en {carpeta_destino}")
    return carpeta_destino


def pedir_datos_interactivos():
    """Pregunta los datos por pantalla cuando no se pasan como argumentos."""
    print("=== Descargador de transcripciones de YouTube ===\n")
    url_canal = input("URL del canal de YouTube (ej: https://www.youtube.com/@NombreCanal): ").strip()

    carpeta_destino = input(
        "Carpeta donde guardar los .txt (Enter para usar una por defecto según el canal): "
    ).strip()

    idiomas_input = input(
        "Idioma(s) de subtítulos, separados por coma si son varios (Enter para 'en'): "
    ).strip()
    idiomas = tuple(i.strip() for i in idiomas_input.split(',') if i.strip()) if idiomas_input else ('en',)

    return url_canal, (carpeta_destino or None), idiomas


def main():
    parser = argparse.ArgumentParser(
        description="Descarga y limpia las transcripciones de todos los vídeos de un canal de YouTube."
    )
    parser.add_argument('-c', '--canal', help="URL del canal de YouTube (con o sin /videos al final)")
    parser.add_argument('-d', '--destino', help="Carpeta donde guardar los .txt")
    parser.add_argument(
        '-i', '--idiomas',
        help="Idiomas de subtítulos separados por coma, ej: en,es (por defecto: en)"
    )
    args = parser.parse_args()

    if args.canal:
        url_canal = args.canal
        carpeta_destino = args.destino
        idiomas = tuple(i.strip() for i in args.idiomas.split(',') if i.strip()) if args.idiomas else ('en',)
    else:
        url_canal, carpeta_destino, idiomas = pedir_datos_interactivos()

    if not url_canal:
        print("No se ha indicado ninguna URL de canal. Saliendo.")
        return

    descargar_transcripciones_canal(url_canal, carpeta_destino, idiomas)


if __name__ == "__main__":
    main()