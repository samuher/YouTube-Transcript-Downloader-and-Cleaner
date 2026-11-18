"""Small, opt-in YouTube compatibility smoke test.

Never invoked by CI. Requires the user to supply three authorized public videos
and an explicit --consent. No cookies, login or high-volume retries.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import platform
import re
import subprocess
import sys
import time
from urllib.parse import parse_qs, urlsplit

from transcript_studio.captions import parse_captions
from transcript_studio.exporting import export_one
from transcript_studio.provider import AccessBlocked, RateLimited, YouTubeProvider, normalize_url

SINGLE_VIDEO = re.compile(r"^[A-Za-z0-9_-]{11}$")


def case_argument(raw):
    try:
        language, url = raw.split(":", 1)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Formato esperado: idioma:https://youtube.com/watch?v=ID") from exc
    if not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z]{2,8})?", language):
        raise argparse.ArgumentTypeError("Idioma inválido")
    try:
        normal = normalize_url(url)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    parsed = urlsplit(normal)
    video_id = parse_qs(parsed.query).get("v", [""])[0]
    if not SINGLE_VIDEO.fullmatch(video_id):
        raise argparse.ArgumentTypeError("Utiliza un vídeo individual, no un canal ni una lista")
    return (language, video_id)


def runtime():
    try:
        import yt_dlp
        yt_version = yt_dlp.version.__version__
    except (ImportError, AttributeError):
        yt_version = "unavailable"
    try:
        deno = subprocess.run(
            ["deno", "--version"], capture_output=True, text=True, timeout=4, check=False,
        )
        deno_version = (deno.stdout.splitlines() or ["unavailable"])[0] if deno.returncode == 0 else "unavailable"
    except (OSError, subprocess.TimeoutExpired):
        deno_version = "unavailable"
    return {"os": platform.platform(), "python": platform.python_version(),
            "yt_dlp": yt_version, "deno": deno_version,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def run_case(kind, language, video_id):
    provider = YouTubeProvider(subtitle_delay=2)
    tracks = provider.get_captions(video_id, [language])
    if kind == "missing":
        if tracks:
            raise AssertionError("Expected no accessible subtitle for the requested language")
        return {"kind": kind, "video_id": video_id, "language": language, "status": "expected_missing"}
    matches = [track for track in tracks if track.kind == kind]
    if not matches:
        raise AssertionError(f"No {kind} subtitle track for {language}; observed kinds: {[t.kind for t in tracks]}")
    for track in matches:
        parsed = parse_captions(track.original)
        if not parsed:
            raise AssertionError("Empty original timed captions")
        if not track.text.strip():
            raise AssertionError("Empty cleaned transcription")
        if any(seg["end"] <= seg["start"] for seg in track.segments):
            raise AssertionError("Non-positive timestamp range")
        item = {"video_id": video_id, "title": "Compatibility fixture",
                "language": track.language, "kind": track.kind,
                "source_url": "https://www.youtube.com/watch?v=" + video_id,
                "text": track.text, "segments": track.segments}
        for fmt in ("txt", "md", "srt", "json"):
            if not export_one(item, fmt):
                raise AssertionError(f"Empty {fmt} export")
    return {"kind": kind, "video_id": video_id, "language": language,
            "status": "ok", "tracks": len(matches),
            "segments": sum(len(x.segments) for x in matches)}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Prueba MANUAL de tres vídeos de YouTube")
    parser.add_argument("--manual", type=case_argument, required=True, metavar="es:URL")
    parser.add_argument("--automatic", type=case_argument, required=True, metavar="es:URL")
    parser.add_argument("--missing", type=case_argument, required=True, metavar="es:URL")
    parser.add_argument("--consent", action="store_true",
                        help="Confirmo que tengo permiso para procesar los tres vídeos")
    parser.add_argument("--pause", type=float, default=8,
                        help="Pausa entre vídeos (mínimo 5 s)")
    parser.add_argument("--report", help="Guardar reporte JSON local sin tokens ni cookies")
    args = parser.parse_args(argv)
    if not args.consent:
        parser.error("Debes confirmar --consent para evitar pruebas de red accidentales")
    if args.pause < 5:
        parser.error("La pausa mínima es 5 segundos")
    cases = [("manual", *args.manual), ("automatic", *args.automatic), ("missing", *args.missing)]
    report = {"environment": runtime(), "cases": [], "passed": False}
    try:
        for index, (kind, lang, video_id) in enumerate(cases):
            if index:
                time.sleep(args.pause)
            print(f"Testing {kind}: {video_id} ({lang})", flush=True)
            result = run_case(kind, lang, video_id)
            report["cases"].append(result)
        report["passed"] = True
    except (AccessBlocked, RateLimited) as exc:
        report["stopped"] = "access_blocked_or_rate_limited"
        print(f"Access blocked; stopping the smoke test. {type(exc).__name__}", file=sys.stderr)
    except (Exception, KeyboardInterrupt) as exc:
        report["stopped"] = type(exc).__name__
        print(f"Test not complete: {exc}", file=sys.stderr)
    if args.report:
        from pathlib import Path
        path = Path(args.report).expanduser().resolve()
        if path.exists():
            parser.error("El reporte ya existe: no se sobrescribirá")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
