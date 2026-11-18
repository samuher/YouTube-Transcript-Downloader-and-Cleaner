"""Pruebas sin red de bloqueos, pausas, credenciales opcionales y reanudación."""

import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import descargar_transcripciones as app


URL = "https://www.youtube.com/@Canal"
VIDEOS = [("abcdefghijk", "Uno"), ("lmnopqrstuv", "Dos"), ("wxyzabcdefg", "Tres")]


def filas(carpeta):
    with (carpeta / app.REPORT_NAME).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


class PruebasResiliencia(unittest.TestCase):
    def test_429_temporal_recuperado(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            (carpeta / "ok.txt").write_text("Texto")
            with patch.object(app, "listar_videos", return_value=VIDEOS[:1]), \
                 patch.object(app, "descargar_un_video", side_effect=[
                     app.yt_dlp.utils.DownloadError("HTTP Error 429"), ["ok.txt"]
                 ]) as descarga, patch.object(app.time, "sleep") as dormir, \
                 patch.object(app.random, "uniform", return_value=1):
                resultado = app.descargar_transcripciones_canal(URL, carpeta, reintentos=1,
                                                                espera_inicial=5)
            self.assertEqual(resultado["descargados"], 1)
            self.assertEqual(descarga.call_count, 2)
            dormir.assert_called_once_with(5)
            self.assertEqual(filas(carpeta)[0]["intentos"], "2")

    def test_bloqueo_persistente_detiene_el_canal_y_conserva_txt(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            (carpeta / "ok.txt").write_text("Se conserva")
            with patch.object(app, "listar_videos", return_value=VIDEOS), \
                 patch.object(app, "descargar_un_video", side_effect=[
                     ["ok.txt"],
                     app.yt_dlp.utils.DownloadError("HTTP Error 429"),
                     app.yt_dlp.utils.DownloadError("HTTP Error 429")
                 ]) as descarga, patch.object(app.time, "sleep"), \
                 patch.object(app.random, "uniform", return_value=0):
                resultado = app.descargar_transcripciones_canal(
                    URL, carpeta, pausa_min=0, pausa_max=0, reintentos=1, espera_inicial=0)
            self.assertTrue(resultado["detenido"])
            self.assertEqual(resultado["bloqueados"], 1)
            self.assertEqual(resultado["pendientes"], 1)
            self.assertEqual(descarga.call_count, 3)
            self.assertTrue((carpeta / "ok.txt").exists())
            self.assertIn(VIDEOS[0][0], app.leer_indice(carpeta))
            self.assertNotIn(VIDEOS[1][0], app.leer_indice(carpeta))
            self.assertEqual([r["estado"] for r in filas(carpeta)], ["descargado", "bloqueado"])

    def test_403_o_bot_no_reintenta(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(app, "listar_videos", return_value=VIDEOS), \
             patch.object(app, "descargar_un_video", side_effect=app.yt_dlp.utils.DownloadError(
                 "Sign in to confirm you're not a bot")) as descargar:
            resultado = app.descargar_transcripciones_canal(URL, tmp, reintentos=5)
            descargar.assert_called_once()
            self.assertEqual(resultado["pendientes"], 2)
            self.assertEqual(resultado["bloqueados"], 1)

    def test_aviso_yt_dlp_429_no_es_sin_subtitulos(self):
        class FakeYDL:
            def __init__(self, opciones):
                self.opciones = opciones
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def extract_info(self, url, download):
                self.opciones["logger"].warning("Unable to download subtitles: HTTP Error 429")
                return {"title": "Vídeo"}
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(app.yt_dlp, "YoutubeDL", FakeYDL):
            with self.assertRaisesRegex(RuntimeError, "429"):
                app.descargar_un_video("abcdefghijk", "Vídeo", Path(tmp), ("es",))

    def test_reanudacion_y_csv_acumulativo(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            (carpeta / "ok.txt").write_text("Texto")
            app.guardar_indice(carpeta, {
                VIDEOS[0][0]: {"requested_languages": ["es"], "files": ["ok.txt"]}
            })
            with patch.object(app, "listar_videos", return_value=VIDEOS[:2]), \
                 patch.object(app, "descargar_un_video", return_value=[]) as descargar:
                for _ in range(2):
                    resultado = app.descargar_transcripciones_canal(
                        URL, carpeta, idiomas=("es",), pausa_min=0, pausa_max=0)
            self.assertEqual(resultado["omitidos"], 1)
            self.assertEqual(resultado["sin_subtitulos"], 1)
            self.assertEqual(descargar.call_count, 2)
            self.assertEqual([r["estado"] for r in filas(carpeta)],
                             ["ya_descargado", "sin_subtitulos"] * 2)

    def test_cookie_opcional_y_sesion_de_navegador(self):
        self.assertEqual(app._opciones_autenticacion("brave"), {
            "cookiesfrombrowser": ("brave",)
        })
        with tempfile.TemporaryDirectory() as tmp:
            cookies = Path(tmp) / "cookies.txt"
            cookies.write_text("# Netscape HTTP Cookie File")
            self.assertEqual(app._opciones_autenticacion(cookies=str(cookies)), {
                "cookiefile": str(cookies)
            })
            with self.assertRaises(ValueError):
                app._opciones_autenticacion("brave", str(cookies))

    def test_pausa_entre_videos_y_no_antes_del_primero(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(app, "listar_videos", return_value=VIDEOS), \
             patch.object(app, "descargar_un_video", return_value=[]), \
             patch.object(app.time, "sleep") as dormir, \
             patch.object(app.random, "uniform", return_value=4):
            app.descargar_transcripciones_canal(URL, tmp)
            self.assertEqual([x.args[0] for x in dormir.call_args_list], [4, 4])

    def test_sin_subtitulos_no_se_marca_completado(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(app, "listar_videos", return_value=VIDEOS[:1]), \
             patch.object(app, "descargar_un_video", return_value=[]):
            carpeta = Path(tmp)
            app.descargar_transcripciones_canal(URL, carpeta)
            self.assertEqual(app.leer_indice(carpeta), {})
            self.assertEqual(filas(carpeta)[0]["estado"], "sin_subtitulos")

    def test_titulo_externo_no_activa_formula_en_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            app.anotar_reporte(carpeta, "abcdefghijk", "=1+1", "error", detalle="+cmd")
            self.assertEqual(filas(carpeta)[0]["titulo"], "'=1+1")
            self.assertEqual(filas(carpeta)[0]["detalle"], "'+cmd")

    def test_listado_bloqueado_se_anota(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(app, "listar_videos", side_effect=app.yt_dlp.utils.DownloadError("403")):
            with self.assertRaises(app.DescargaInterrumpida):
                app.descargar_transcripciones_canal(URL, tmp)
            self.assertEqual(filas(Path(tmp))[0]["estado"], "bloqueado")

    def test_error_aislado_se_registra_y_continua(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(app, "listar_videos", return_value=VIDEOS[:2]), \
             patch.object(app, "descargar_un_video", side_effect=[
                 app.yt_dlp.utils.DownloadError("subtitle missing"), []
             ]):
            resumen = app.descargar_transcripciones_canal(URL, tmp, pausa_min=0, pausa_max=0)
            self.assertEqual(resumen["errores"], 1)
            self.assertEqual(resumen["sin_subtitulos"], 1)
            self.assertFalse(resumen["detenido"])

    def test_opciones_invalidas(self):
        for kwargs in ({"pausa_min": 9, "pausa_max": 4}, {"reintentos": -1},
                       {"espera_inicial": 60, "espera_maxima": 5}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                app.descargar_transcripciones_canal(URL, **kwargs)


if __name__ == "__main__":
    unittest.main()
