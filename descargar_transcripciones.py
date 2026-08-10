import yt_dlp
import os
import re

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

def descargar_transcripciones_canal(url_canal, carpeta_destino="transcripciones"):
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],  # Solo bajamos inglés para evitar el error de YouTube
        'subtitlesformat': 'vtt',
        'outtmpl': f'{carpeta_destino}/%(uploader)s - %(upload_date)s - %(title)s.%(ext)s',
        'ignoreerrors': True,
    }

    print(f"Iniciando extracción del canal: {url_canal}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url_canal])

    print(f"\n¡Descargas completadas! Limpiando el código basura de los archivos...")

    # Busca todos los archivos .vtt descargados y los limpia uno por uno
    for archivo in os.listdir(carpeta_destino):
        if archivo.endswith(".vtt"):
            ruta_completa = os.path.join(carpeta_destino, archivo)
            limpiar_vtt_a_txt(ruta_completa)

    print(f"¡Proceso 100% finalizado! Tienes tus archivos .txt limpios en {carpeta_destino}")

# ==========================================
# CONFIGURACIÓN DEL USUARIO
# ==========================================
url_del_canal = "https://www.youtube.com/@CanalDeEjemplo"
ruta_de_guardado = r"transcripciones/CanalDeEjemplo"

descargar_transcripciones_canal(url_del_canal, carpeta_destino=ruta_de_guardado)
