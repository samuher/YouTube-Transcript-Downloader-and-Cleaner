"""Pruebas locales sin peticiones de red."""

import importlib
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    import yt_dlp
except ImportError:
    falso = types.ModuleType("yt_dlp")
    falso.utils = types.SimpleNamespace(DownloadError=type("DownloadError", (Exception,), {}))
    sys.modules["yt_dlp"] = falso

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
descargar = importlib.import_module("descargar_transcripciones")
consolidador = importlib.import_module("Consolidador")


class PruebasLimpieza(unittest.TestCase):
    def test_solapamiento_automatico(self):
        vtt = """WEBVTT

00:00:01.000 --> 00:00:02.000
<c>Hello</c>

00:00:02.000 --> 00:00:03.000
Hello world

00:00:03.000 --> 00:00:04.000
world again
"""
        self.assertEqual(descargar.limpiar_vtt(vtt), "Hello world again")

    def test_multilinea_y_srt(self):
        texto = "1\n00:00:01,000 --> 00:00:03,000\n<v A>Hola &amp; adiós</v>\nsegunda línea\n\n2\n00:00:04,000 --> 00:00:05,000\nfinal\n"
        self.assertEqual(descargar.limpiar_vtt(texto), "Hola & adiós segunda línea final")

    def test_no_borra_original_vacio(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / "input.vtt"
            original.write_text("WEBVTT\n")
            with self.assertRaises(ValueError):
                descargar.limpiar_vtt_a_txt(original)
            self.assertTrue(original.exists())

    def test_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / "input.vtt"
            original.write_text("WEBVTT\n\n00:00:01 --> 00:00:02\nHola\n")
            resultado = descargar.limpiar_vtt_a_txt(original)
            self.assertEqual(resultado.read_text(), "Hola\n")
            self.assertFalse(original.exists())


class PruebasDescarga(unittest.TestCase):
    def test_normalizacion_canal(self):
        self.assertEqual(descargar.normalizar_url_canal("https://youtube.com/@canal?feature=shared"),
                         "https://www.youtube.com/@canal/videos")
        self.assertEqual(descargar.normalizar_url_canal("https://youtube.com/channel/UC123/shorts"),
                         "https://www.youtube.com/channel/UC123/shorts")
        self.assertEqual(descargar.nombre_carpeta_desde_url("https://youtube.com/channel/UC123"), "UC123")

    def test_url_video(self):
        self.assertEqual(descargar.normalizar_url_canal("https://youtu.be/abcdefghijk?t=3"),
                         "https://youtu.be/abcdefghijk")
        self.assertEqual(descargar.normalizar_url_canal("https://youtube.com/watch?v=abcdefghijk&t=3"),
                         "https://www.youtube.com/watch?v=abcdefghijk")

    def test_rechaza_url_ajena(self):
        for url in ("https://notyoutube.com/@foo", "file:///etc/passwd", "https://youtube.com/anything"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                descargar.normalizar_url_canal(url)

    def test_nombre_seguro(self):
        self.assertEqual(descargar.nombre_seguro('A: "B" / C?'), "A_ _B_ _ C")
        self.assertEqual(descargar.nombre_seguro("CON"), "_CON")

    def test_reanudacion(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            url = "https://www.youtube.com/@canal"
            videos = [("abcdefghijk", "Uno")]
            with patch.object(descargar, "listar_videos", return_value=videos), \
                 patch.object(descargar, "descargar_un_video", return_value=[]) as fake:
                resumen = descargar.descargar_transcripciones_canal(url, carpeta)
                self.assertEqual(resumen["sin_subtitulos"], 1)
                fake.assert_called_once()
            nombre = "Uno [abcdefghijk].en.txt"
            (carpeta / nombre).write_text("Texto\n")
            descargar.guardar_indice(carpeta, {"abcdefghijk": {
                "requested_languages": ["en"], "files": [nombre]
            }})
            with patch.object(descargar, "listar_videos", return_value=videos), \
                 patch.object(descargar, "descargar_un_video", return_value=[nombre]) as fake:
                resumen = descargar.descargar_transcripciones_canal(url, carpeta)
                self.assertEqual(resumen["omitidos"], 1)
                fake.assert_not_called()
                descargar.descargar_transcripciones_canal(url, carpeta, forzar=True)
                fake.assert_called_once()

    def test_descarga_simulada(self):
        class FakeYDL:
            def __init__(self, options):
                self.options = options
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def extract_info(self, url, download):
                fichero = Path(self.options["outtmpl"].replace("%(id)s", "abcdefghijk").replace("%(ext)s", "en.vtt"))
                fichero.write_text("WEBVTT\n\n00:00:01 --> 00:00:02\nProbando uno\n")
                return {"title": "Vídeo: bueno"}
        with tempfile.TemporaryDirectory() as tmp, patch.object(descargar.yt_dlp, "YoutubeDL", FakeYDL, create=True):
            creados = descargar.descargar_un_video("abcdefghijk", "Antiguo", Path(tmp), ("en",))
            self.assertEqual(len(creados), 1)
            self.assertEqual((Path(tmp) / creados[0]).read_text(), "Probando uno\n")


class PruebasConsolidacion(unittest.TestCase):
    def test_respeta_limite_con_encabezados(self):
        with tempfile.TemporaryDirectory() as tmp:
            origen, destino = Path(tmp) / "entrada", Path(tmp) / "salida"
            origen.mkdir()
            (origen / "uno.txt").write_text("a b c d e f g h i j")
            (origen / "dos.txt").write_text("k l m n o p q r s t")
            tomos = consolidador.consolidar_textos(origen, destino, 15, "Parte")
            self.assertEqual(len(tomos), 2)
            for tomo in tomos:
                self.assertLessEqual(len(tomo.read_text().split()), 15)

    def test_divide_sin_perder_palabras(self):
        with tempfile.TemporaryDirectory() as tmp:
            origen, destino = Path(tmp) / "entrada", Path(tmp) / "salida"
            origen.mkdir()
            palabras = [f"palabra{i}" for i in range(33)]
            (origen / "video.txt").write_text(" ".join(palabras))
            tomos = consolidador.consolidar_textos(origen, destino, 12, "Lote")
            self.assertGreater(len(tomos), 1)
            texto = " ".join(p.read_text() for p in tomos).split()
            for palabra in palabras:
                self.assertEqual(texto.count(palabra), 1)
            self.assertTrue(all(len(p.read_text().split()) <= 12 for p in tomos))

    def test_ignora_archivo_y_borra_tomos_obsoletos(self):
        with tempfile.TemporaryDirectory() as tmp:
            origen, destino = Path(tmp) / "entrada", Path(tmp) / "salida"
            origen.mkdir()
            destino.mkdir()
            (origen / "video.txt").write_text("Hola")
            (origen / "archivo_descargados.txt").write_text("historial youtube")
            (destino / "Lote_99.txt").write_text("antiguo")
            (destino / "otro.txt").write_text("no tocar")
            tomos = consolidador.consolidar_textos(origen, destino, 10, "Lote")
            self.assertEqual(len(tomos), 1)
            self.assertNotIn("historial", tomos[0].read_text())
            self.assertFalse((destino / "Lote_99.txt").exists())
            self.assertTrue((destino / "otro.txt").exists())

    def test_invalidos(self):
        with tempfile.TemporaryDirectory() as tmp:
            origen = Path(tmp)
            with self.assertRaises(ValueError):
                consolidador.consolidar_textos(origen, origen)
            with self.assertRaises(ValueError):
                consolidador.consolidar_textos(origen, origen / "out", 500001)
            with self.assertRaises(ValueError):
                consolidador.consolidar_textos(origen / "no-existe")


if __name__ == "__main__":
    unittest.main()
