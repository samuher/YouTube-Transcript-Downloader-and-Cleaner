"""Descarga subtítulos de un canal o vídeo de YouTube y los guarda como texto."""

import argparse
import html
import json
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlsplit, urlunsplit

import yt_dlp


VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
INDEX_NAME = ".transcripciones_index.json"


def normalizar_url_canal(url):
    """Acepta URLs de canales y vídeos; en canales usa /videos por defecto."""
    url = url.strip()
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or host not in {
        "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"
    }:
        raise ValueError("Introduce una URL http(s) de youtube.com o youtu.be")

    path = parsed.path.rstrip("/")
    if host == "youtu.be":
        if not VIDEO_ID.fullmatch(path.lstrip("/")):
            raise ValueError("La URL corta no contiene un identificador de vídeo válido")
        return urlunsplit(("https", "youtu.be", path, "", ""))

    if path == "/watch":
        video_id = parse_qs(parsed.query).get("v", [""])[0]
        if not VIDEO_ID.fullmatch(video_id):
            raise ValueError("Falta un identificador de vídeo válido en la URL")
        return f"https://www.youtube.com/watch?v={video_id}"
    if path.startswith(("/shorts/", "/live/")):
        video_id = path.split("/")[2]
        if not VIDEO_ID.fullmatch(video_id):
            raise ValueError("Identificador de vídeo no válido")
        return f"https://www.youtube.com/watch?v={video_id}"

    parts = path.strip("/").split("/")
    is_channel = (
        len(parts) >= 1 and parts[0].startswith("@") and len(parts[0]) > 1
    ) or (len(parts) >= 2 and parts[0] in {"channel", "c", "user"} and bool(parts[1]))
    if not is_channel:
        raise ValueError("Usa una URL de canal (@usuario, /channel/, /c/, /user/) o de vídeo")
    if parts[-1] not in {"videos", "shorts", "streams", "playlists"}:
        path += "/videos"
    return urlunsplit(("https", "www.youtube.com", path, "", ""))


def nombre_carpeta_desde_url(url):
    parsed = urlsplit(normalizar_url_canal(url))
    parts = parsed.path.strip("/").split("/")
    if parts[0] in {"watch", "shorts", "live"} or parsed.hostname == "youtu.be":
        name = parse_qs(parsed.query).get("v", [parts[-1]])[0]
    elif parts[0] in {"channel", "c", "user"}:
        name = parts[1]
    else:
        name = parts[0].lstrip("@")
    return nombre_seguro(name)


def nombre_seguro(text):
    cleaned = INVALID_FILENAME.sub("_", str(text))
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ._")[:100].rstrip(" .")
    if cleaned.upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
        cleaned = "_" + cleaned
    return cleaned or "video"


def limpiar_vtt(contenido):
    """Limpia VTT/SRT y elimina el solapamiento típico de subtítulos automáticos."""
    bloques = re.split(r"\n\s*\n", contenido.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n"))
    anterior = []
    resultado = []
    for bloque in bloques:
        lineas = bloque.splitlines()
        if not lineas or lineas[0].strip().startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
            continue
        indice = next((i for i, linea in enumerate(lineas) if "-->" in linea), None)
        if indice is None:
            continue
        texto = " ".join(lineas[indice + 1:])
        texto = html.unescape(re.sub(r"<[^>]*>", "", texto))
        texto = re.sub(r"\s+", " ", texto).strip()
        if not texto:
            continue
        palabras = texto.split()
        prev_lower = [p.casefold() for p in anterior]
        curr_lower = [p.casefold() for p in palabras]
        coincidencia = 0
        for n in range(min(len(anterior), len(palabras)), 0, -1):
            if prev_lower[-n:] == curr_lower[:n]:
                coincidencia = n
                break
        if coincidencia == 0 and len(palabras) <= len(anterior) and curr_lower == prev_lower[:len(palabras)]:
            coincidencia = len(palabras)
        resultado.extend(palabras[coincidencia:])
        anterior = palabras
    return " ".join(resultado).strip()


def limpiar_vtt_a_txt(ruta_vtt, ruta_txt=None):
    """Escribe el TXT de forma atómica; solo borra el VTT si hubo texto válido."""
    origen = Path(ruta_vtt)
    destino = Path(ruta_txt) if ruta_txt else origen.with_suffix(".txt")
    texto = limpiar_vtt(origen.read_text(encoding="utf-8-sig"))
    if not texto:
        raise ValueError(f"No se encontró texto de subtítulos en {origen.name}")
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=destino.parent, suffix=".tmp", delete=False) as f:
            temporal = Path(f.name)
            f.write(texto + "\n")
        temporal.replace(destino)
    finally:
        if temporal and temporal.exists():
            temporal.unlink()
    origen.unlink()
    return destino


def leer_indice(carpeta):
    ruta = carpeta / INDEX_NAME
    if not ruta.exists():
        return {}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        return datos if isinstance(datos, dict) else {}
    except (OSError, ValueError):
        print("Aviso: el índice local está dañado. Se reconstruirá.", file=sys.stderr)
        return {}


def guardar_indice(carpeta, indice):
    destino = carpeta / INDEX_NAME
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=carpeta, suffix=".tmp", delete=False) as f:
        temporal = Path(f.name)
        json.dump(indice, f, ensure_ascii=False, indent=2, sort_keys=True)
    temporal.replace(destino)


def listar_videos(url, max_videos=None):
    opciones = {"extract_flat": "in_playlist", "skip_download": True, "quiet": True, "noplaylist": False}
    if max_videos:
        opciones["playlistend"] = max_videos
    with yt_dlp.YoutubeDL(opciones) as ydl:
        datos = ydl.extract_info(url, download=False)
    if not datos:
        raise RuntimeError("YouTube no ha devuelto ningún vídeo")
    entradas = datos.get("entries") if isinstance(datos, dict) else None
    entradas = entradas if entradas is not None else [datos]
    videos = []
    vistos = set()
    for entrada in entradas:
        if not isinstance(entrada, dict):
            continue
        video_id = entrada.get("id")
        if not isinstance(video_id, str) or not VIDEO_ID.fullmatch(video_id) or video_id in vistos:
            continue
        vistos.add(video_id)
        videos.append((video_id, entrada.get("title") or video_id))
        if max_videos and len(videos) >= max_videos:
            break
    return videos


def descargar_un_video(video_id, titulo, carpeta, idiomas):
    """Trabaja en un directorio temporal para no mezclar subtítulos de otros vídeos."""
    with tempfile.TemporaryDirectory(prefix="sub_", dir=carpeta) as temporal:
        temp = Path(temporal)
        opciones = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": list(idiomas),
            "subtitlesformat": "vtt/srt/best",
            "outtmpl": str(temp / "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": False,
            "retries": 3,
            "fragment_retries": 3,
            "sleep_interval_subtitles": 1,
        }
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
        if not info:
            raise RuntimeError("No se pudieron obtener los datos del vídeo")
        nombre = nombre_seguro(info.get("title") or titulo)
        creados = []
        for fichero in sorted(temp.iterdir()):
            if fichero.suffix.lower() not in {".vtt", ".srt"} or not fichero.name.startswith(video_id + "."):
                continue
            idioma = fichero.name[len(video_id) + 1:-len(fichero.suffix)]
            if not idioma:
                continue
            salida = carpeta / f"{nombre} [{video_id}].{nombre_seguro(idioma)}.txt"
            try:
                limpiar_vtt_a_txt(fichero, salida)
                creados.append(salida.name)
            except (OSError, UnicodeError, ValueError) as exc:
                print(f"  No se pudo limpiar {fichero.name}: {exc}", file=sys.stderr)
        return creados


def descargar_transcripciones_canal(url_canal, carpeta_destino=None, idiomas=("en",), max_videos=None, forzar=False):
    url = normalizar_url_canal(url_canal)
    idiomas = tuple(dict.fromkeys(lang.strip() for lang in idiomas if lang.strip()))
    if not idiomas:
        raise ValueError("Indica al menos un idioma, por ejemplo 'es' o 'en'")
    if max_videos is not None and max_videos < 1:
        raise ValueError("--max-videos debe ser mayor que cero")
    carpeta = Path(carpeta_destino) if carpeta_destino else Path("transcripciones") / nombre_carpeta_desde_url(url)
    carpeta.mkdir(parents=True, exist_ok=True)
    videos = listar_videos(url, max_videos)
    indice = leer_indice(carpeta)
    resumen = {"descargados": 0, "omitidos": 0, "sin_subtitulos": 0, "errores": 0}
    print(f"Vídeos encontrados: {len(videos)}. Destino: {carpeta}")
    for numero, (video_id, titulo) in enumerate(videos, start=1):
        previo = indice.get(video_id, {})
        guardados = previo.get("files", []) if isinstance(previo, dict) else []
        pedidos = previo.get("requested_languages", []) if isinstance(previo, dict) else []
        if (not forzar and set(idiomas).issubset(pedidos) and guardados
                and all((carpeta / nombre).is_file() and (carpeta / nombre).stat().st_size for nombre in guardados)):
            resumen["omitidos"] += 1
            continue
        print(f"[{numero}/{len(videos)}] {titulo}")
        try:
            creados = descargar_un_video(video_id, titulo, carpeta, idiomas)
            if not creados:
                resumen["sin_subtitulos"] += 1
                print("  Sin subtítulos descargables en los idiomas solicitados")
                continue
            # Conservar el histórico de idiomas procesados y los archivos existentes.
            existentes = [nombre for nombre in guardados if (carpeta / nombre).is_file()]
            indice[video_id] = {
                "requested_languages": sorted(set(pedidos) | set(idiomas)),
                "files": sorted(set(existentes) | set(creados)),
            }
            guardar_indice(carpeta, indice)
            resumen["descargados"] += 1
            print(f"  Guardados: {len(creados)} TXT")
        except (yt_dlp.utils.DownloadError, OSError, ValueError, RuntimeError) as exc:
            resumen["errores"] += 1
            print(f"  Error en {video_id}: {exc}", file=sys.stderr)
    print("Resultado: " + ", ".join(f"{k}: {v}" for k, v in resumen.items()))
    return resumen


def main(argv=None):
    parser = argparse.ArgumentParser(description="Descarga los subtítulos de un canal o vídeo como TXT.")
    parser.add_argument("-c", "--canal", help="URL de canal o vídeo")
    parser.add_argument("-d", "--destino", help="Carpeta donde guardar los archivos")
    parser.add_argument("-i", "--idiomas", help="Idiomas separados por comas (por defecto: en)")
    parser.add_argument("--max-videos", type=int, help="Procesa como máximo este número de vídeos")
    parser.add_argument("--forzar", action="store_true", help="Vuelve a descargar vídeos ya procesados")
    args = parser.parse_args(argv)
    if args.canal:
        url, destino, idiomas = args.canal, args.destino, args.idiomas or "en"
    else:
        url = input("URL de canal o vídeo de YouTube: ").strip()
        destino = input("Carpeta de destino (Enter = automática): ").strip() or None
        idiomas = input("Idiomas separados por comas (Enter = en): ").strip() or "en"
    try:
        if not url:
            raise ValueError("No has indicado ninguna URL")
        resumen = descargar_transcripciones_canal(url, destino, idiomas.split(","), args.max_videos, args.forzar)
        return 1 if resumen["errores"] else 0
    except (OSError, ValueError, RuntimeError, yt_dlp.utils.DownloadError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
