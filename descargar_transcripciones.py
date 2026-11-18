"""Descarga subtítulos de un canal o vídeo de YouTube y los guarda como texto."""

import argparse
import csv
import html
import json
import random
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit, urlunsplit

import yt_dlp


VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
INDEX_NAME = ".transcripciones_index.json"
REPORT_NAME = "reporte_descargas.csv"
BROWSERS = {"brave", "chrome", "chromium", "edge", "firefox", "opera", "vivaldi"}
REPORT_FIELDS = ("fecha_utc", "video_id", "titulo", "estado", "intentos", "archivos", "detalle")


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



class DescargaInterrumpida(Exception):
    """No conviene seguir enviando solicitudes en esta ejecución."""

    def __init__(self, mensaje, intentos, tipo="bloqueado"):
        super().__init__(mensaje)
        self.intentos = intentos
        self.tipo = tipo


class FalloVideo(Exception):
    """Fallo específico de un vídeo, sin bloqueo global."""

    def __init__(self, mensaje, intentos):
        super().__init__(mensaje)
        self.intentos = intentos


def _opciones_autenticacion(navegador=None, cookies=None):
    if navegador and cookies:
        raise ValueError("Usa --navegador o --cookies, pero no ambos")
    if navegador:
        if navegador not in BROWSERS:
            raise ValueError(f"Navegador no admitido: {navegador}")
        return {"cookiesfrombrowser": (navegador,)}
    if cookies:
        ruta = Path(cookies).expanduser().resolve()
        if not ruta.is_file():
            raise ValueError("El archivo de cookies no existe")
        return {"cookiefile": str(ruta)}
    return {}


def _tipo_error(exc):
    mensaje = str(exc).casefold()
    if (re.search(r"\b(429|402)\b", mensaje) or "too many requests" in mensaje
            or "rate limit" in mensaje or "rate-limit" in mensaje):
        return "limite"
    if (re.search(r"\b(401|403)\b", mensaje) or "confirm you're not a bot" in mensaje
            or "confirm you’re not a bot" in mensaje or "sign in to confirm" in mensaje
            or "captcha" in mensaje or "unusual traffic" in mensaje):
        return "acceso"
    if (re.search(r"\b(500|502|503|504)\b", mensaje) or "timed out" in mensaje
            or "timeout" in mensaje or "connection reset" in mensaje or "remote end closed" in mensaje
            or "temporary failure" in mensaje or "network is unreachable" in mensaje):
        return "temporal"
    return "otro"


def _reintentar(accion, *, reintentos, espera_inicial, espera_maxima, descripcion):
    """Espera entre fallos transitorios; no insiste cuando aparece un bloqueo."""
    for intento in range(1, reintentos + 2):
        try:
            return accion(), intento
        except (yt_dlp.utils.DownloadError, OSError, RuntimeError) as exc:
            tipo = _tipo_error(exc)
            if tipo == "acceso":
                raise DescargaInterrumpida(
                    "YouTube requiere autenticación o deniega el acceso (posible bot/403). "
                    "Detenido para no insistir con más vídeos.", intento, "acceso") from exc
            if tipo not in {"limite", "temporal"}:
                raise FalloVideo(f"{type(exc).__name__}: {str(exc)[:250]}", intento) from exc
            if intento > reintentos:
                if tipo == "limite":
                    raise DescargaInterrumpida(
                        "Límite de solicitudes (429/402) persistente. Detenido; prueba más tarde.",
                        intento, "limite") from exc
                raise FalloVideo(f"Fallo temporal persistente: {str(exc)[:250]}", intento) from exc
            espera = min(espera_maxima, espera_inicial * 2 ** (intento - 1))
            espera *= random.uniform(0.9, 1.1)
            print(f"  {descripcion}: fallo {tipo}; reintento {intento}/{reintentos} tras {espera:.0f} s")
            time.sleep(espera)
    raise AssertionError("Bucle de reintentos agotado")


class _RegistroYtDlp:
    """Captura también los errores de subtítulos que yt-dlp comunica como avisos."""

    def __init__(self):
        self.mensajes = []

    def debug(self, mensaje):
        pass

    def warning(self, mensaje):
        self.mensajes.append(str(mensaje))

    def error(self, mensaje):
        self.mensajes.append(str(mensaje))

    def error_critico(self):
        for mensaje in self.mensajes:
            if _tipo_error(mensaje) in {"limite", "acceso", "temporal"}:
                return mensaje
        return None


def _csv_seguro(valor):
    """Evita que títulos externos se interpreten como fórmulas en Excel."""
    texto = str(valor).replace("\r", " ").replace("\n", " ")
    if texto.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + texto
    return texto


def anotar_reporte(carpeta, video_id, titulo, estado, intentos=0, archivos=(), detalle=""):
    ruta = carpeta / REPORT_NAME
    nuevo = not ruta.exists() or ruta.stat().st_size == 0
    with ruta.open("a", encoding="utf-8-sig" if nuevo else "utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REPORT_FIELDS)
        if nuevo:
            writer.writeheader()
        writer.writerow({
            "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "video_id": video_id,
            "titulo": _csv_seguro(titulo),
            "estado": estado,
            "intentos": intentos,
            "archivos": " | ".join(_csv_seguro(n) for n in archivos),
            "detalle": _csv_seguro(detalle)[:350],
        })
        f.flush()


def listar_videos(url, max_videos=None, autenticacion=None):
    registro = _RegistroYtDlp()
    opciones = {
        "extract_flat": "in_playlist", "skip_download": True,
        "quiet": True, "noplaylist": False, "ignoreerrors": False,
        "logger": registro, "socket_timeout": 20,
        **(autenticacion or {}),
    }
    if max_videos:
        opciones["playlistend"] = max_videos
    with yt_dlp.YoutubeDL(opciones) as ydl:
        datos = ydl.extract_info(url, download=False)
    if registro.error_critico():
        raise RuntimeError(registro.error_critico())
    if not datos:
        raise RuntimeError("YouTube no ha devuelto datos del canal o vídeo")
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
    if not videos:
        raise RuntimeError("No se encontraron vídeos válidos; revisa la URL o el acceso al canal")
    return videos

def descargar_un_video(video_id, titulo, carpeta, idiomas, autenticacion=None, espera_subtitulos=1):
    """Cada vídeo se descarga en un directorio temporal aislado."""
    with tempfile.TemporaryDirectory(prefix="sub_", dir=carpeta) as temporal:
        temp = Path(temporal)
        registro = _RegistroYtDlp()
        opciones = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": list(idiomas),
            "subtitlesformat": "vtt/srt",
            "outtmpl": str(temp / "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": False,
            "ignoreerrors": False,
            "retries": 2,
            "fragment_retries": 2,
            "sleep_interval_subtitles": espera_subtitulos,
            "logger": registro, "socket_timeout": 20,
            **(autenticacion or {}),
        }
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
        if not info:
            raise RuntimeError("YouTube no devolvió datos para el vídeo")
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
        # Algunos errores de subtítulos aparecen como warning, no excepción.
        aviso = registro.error_critico()
        if aviso:
            raise RuntimeError(aviso)
        return creados

def descargar_transcripciones_canal(url_canal, carpeta_destino=None, idiomas=("en",), max_videos=None,
                                     forzar=False, *, navegador=None, cookies=None,
                                     pausa_min=3, pausa_max=7, reintentos=2,
                                     espera_inicial=30, espera_maxima=300, espera_subtitulos=1):
    url = normalizar_url_canal(url_canal)
    idiomas = tuple(dict.fromkeys(lang.strip() for lang in idiomas if lang.strip()))
    if not idiomas:
        raise ValueError("Indica al menos un idioma (por ejemplo, es o en)")
    if max_videos is not None and max_videos < 1:
        raise ValueError("--max-videos debe ser un entero positivo")
    if (not 0 <= pausa_min <= pausa_max or reintentos < 0
            or espera_inicial < 0 or espera_maxima < espera_inicial or espera_subtitulos < 0):
        raise ValueError("Los tiempos deben ser positivos y los máximos no menores que los mínimos")
    autenticacion = _opciones_autenticacion(navegador, cookies)
    carpeta = Path(carpeta_destino) if carpeta_destino else Path("transcripciones") / nombre_carpeta_desde_url(url)
    carpeta.mkdir(parents=True, exist_ok=True)
    print(f"Destino: {carpeta} | Reporte: {carpeta / REPORT_NAME}")
    try:
        videos, _ = _reintentar(
            lambda: listar_videos(url, max_videos, autenticacion),
            reintentos=reintentos, espera_inicial=espera_inicial,
            espera_maxima=espera_maxima, descripcion="Listado del canal",
        )
    except (DescargaInterrumpida, FalloVideo) as exc:
        anotar_reporte(carpeta, "", url, "bloqueado" if isinstance(exc, DescargaInterrumpida) else "error",
                       exc.intentos, detalle=str(exc))
        raise

    indice = leer_indice(carpeta)
    resumen = {"descargados": 0, "omitidos": 0, "sin_subtitulos": 0, "errores": 0,
               "bloqueados": 0, "pendientes": 0, "detenido": False}
    print(f"Vídeos encontrados: {len(videos)}")
    procesados = 0
    ultima_solicitud = False
    for numero, (video_id, titulo) in enumerate(videos, start=1):
        previo = indice.get(video_id, {})
        guardados = previo.get("files", []) if isinstance(previo, dict) else []
        pedidos = previo.get("requested_languages", []) if isinstance(previo, dict) else []
        if (not forzar and set(idiomas).issubset(pedidos) and guardados
                and all((carpeta / nombre).is_file() and (carpeta / nombre).stat().st_size for nombre in guardados)):
            resumen["omitidos"] += 1
            procesados += 1
            anotar_reporte(carpeta, video_id, titulo, "ya_descargado", archivos=guardados)
            continue
        print(f"[{numero}/{len(videos)}] {titulo}")
        try:
            if ultima_solicitud:
                pausa = random.uniform(pausa_min, pausa_max)
                if pausa:
                    print(f"  Pausa entre vídeos: {pausa:.1f} s")
                    time.sleep(pausa)
            ultima_solicitud = True
            creados, intentos = _reintentar(
                lambda: descargar_un_video(video_id, titulo, carpeta, idiomas, autenticacion, espera_subtitulos),
                reintentos=reintentos, espera_inicial=espera_inicial,
                espera_maxima=espera_maxima, descripcion=f"Vídeo {video_id}",
            )
            if not creados:
                resumen["sin_subtitulos"] += 1
                anotar_reporte(carpeta, video_id, titulo, "sin_subtitulos", intentos,
                               detalle="No hay subtítulos descargables en los idiomas pedidos")
                print("  Sin subtítulos descargables; se podrá reintentar después")
            else:
                existentes = [n for n in guardados if (carpeta / n).is_file()]
                indice[video_id] = {
                    "requested_languages": sorted(set(pedidos) | set(idiomas)),
                    "files": sorted(set(existentes) | set(creados)),
                }
                guardar_indice(carpeta, indice)
                resumen["descargados"] += 1
                anotar_reporte(carpeta, video_id, titulo, "descargado", intentos, creados)
                print(f"  Guardados: {len(creados)} TXT")
            procesados += 1
        except DescargaInterrumpida as exc:
            resumen["bloqueados"] += 1
            resumen["detenido"] = True
            anotar_reporte(carpeta, video_id, titulo, "bloqueado", exc.intentos, detalle=str(exc))
            print(f"  {exc}", file=sys.stderr)
            procesados += 1
            break
        except FalloVideo as exc:
            resumen["errores"] += 1
            anotar_reporte(carpeta, video_id, titulo, "error", exc.intentos, detalle=str(exc))
            print(f"  Error en {video_id}: {exc}", file=sys.stderr)
            procesados += 1
        except KeyboardInterrupt:
            resumen["detenido"] = True
            anotar_reporte(carpeta, video_id, titulo, "interrumpido", detalle="Interrupción del usuario")
            print("\nInterrumpido. Puedes volver a ejecutar para continuar.", file=sys.stderr)
            break
    resumen["pendientes"] = len(videos) - procesados
    print("Resultado: " + ", ".join(f"{k}: {v}" for k, v in resumen.items()))
    print(f"Historial de intentos: {carpeta / REPORT_NAME}")
    return resumen

def main(argv=None):
    parser = argparse.ArgumentParser(description="Descarga subtítulos de un canal o vídeo en TXT, con pausas y reanudación.")
    parser.add_argument("-c", "--canal", help="URL de canal o vídeo")
    parser.add_argument("-d", "--destino", help="Carpeta de salida")
    parser.add_argument("-i", "--idiomas", help="Idiomas separados por comas (defecto: en)")
    parser.add_argument("--max-videos", type=int, help="Procesa los primeros N vídeos")
    parser.add_argument("--forzar", action="store_true", help="Reprocesa vídeos completados")
    autenticacion = parser.add_mutually_exclusive_group()
    autenticacion.add_argument("--navegador", choices=sorted(BROWSERS), help="Usa las cookies de tu navegador local (opcional)")
    autenticacion.add_argument("--cookies", help="Archivo Netscape cookies.txt local (no lo subas a GitHub)")
    parser.add_argument("--pausa-min", type=float, default=3, help="Pausa mínima entre vídeos en segundos (3)")
    parser.add_argument("--pausa-max", type=float, default=7, help="Pausa máxima entre vídeos en segundos (7)")
    parser.add_argument("--reintentos", type=int, default=2, help="Reintentos extra ante 429/red/5xx (2)")
    parser.add_argument("--espera-inicial", type=float, default=30, help="Espera inicial tras 429 o error temporal (30 s)")
    parser.add_argument("--espera-maxima", type=float, default=300, help="Tope de espera progresiva (300 s)")
    parser.add_argument("--espera-subtitulos", type=float, default=1, help="Espera de yt-dlp antes de cada subtítulo (1 s)")
    args = parser.parse_args(argv)
    if args.canal:
        url, destino, idiomas = args.canal, args.destino, args.idiomas or "en"
    else:
        url = input("URL del canal o vídeo: ").strip()
        destino = input("Carpeta (Enter = automática): ").strip() or None
        idiomas = input("Idiomas (Enter = en): ").strip() or "en"
    try:
        if not url:
            raise ValueError("No se ha indicado ninguna URL")
        resumen = descargar_transcripciones_canal(
            url, destino, idiomas.split(","), args.max_videos, args.forzar,
            navegador=args.navegador, cookies=args.cookies, pausa_min=args.pausa_min,
            pausa_max=args.pausa_max, reintentos=args.reintentos,
            espera_inicial=args.espera_inicial, espera_maxima=args.espera_maxima,
            espera_subtitulos=args.espera_subtitulos,
        )
        return 2 if resumen["detenido"] else 1 if resumen["errores"] else 0
    except (OSError, ValueError, RuntimeError, yt_dlp.utils.DownloadError, DescargaInterrumpida, FalloVideo) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2 if isinstance(exc, DescargaInterrumpida) else 1
    except KeyboardInterrupt:
        print("\nInterrumpido antes de empezar; no se han borrado transcripciones.", file=sys.stderr)
        return 130

if __name__ == "__main__":
    sys.exit(main())
