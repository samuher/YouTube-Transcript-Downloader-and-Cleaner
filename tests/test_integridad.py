"""P0 regression tests for partial jobs, language integrity and playlists.

All extraction is simulated. No requests are sent to YouTube.
"""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient
from transcript_studio.app import create_app
from transcript_studio.provider import DownloadedCaption, VideoFailure, normalize_url
from transcript_studio.storage import Store
from transcript_studio.worker import Worker


def caption(language):
    return DownloadedCaption(
        language, "automatic", "WEBVTT", "Hola mundo",
        [{"start": 0.0, "end": 1.0, "text": "Hola mundo"}],
    )


class ChangingProvider:
    mode = "incomplete"
    calls = []

    def __init__(self, **kwargs):
        pass

    def list_videos(self, url, max_videos):
        return [
            {"video_id": "abcdefghijk", "title": "Primero"},
            {"video_id": "lmnopqrstuv", "title": "Segundo"},
        ]

    def get_captions(self, video_id, languages):
        self.calls.append(video_id)
        if self.mode == "incomplete":
            return [caption("es")] if video_id == "abcdefghijk" else []
        if self.mode == "error" and video_id == "lmnopqrstuv":
            raise VideoFailure("El vídeo no está accesible")
        return [caption("es"), caption("en-orig")]


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "library.sqlite3")
        self.worker = Worker(self.store, provider_factory=ChangingProvider)
        ChangingProvider.calls = []
        ChangingProvider.mode = "incomplete"

    def tearDown(self):
        self.tmp.cleanup()

    def new_job(self, languages=("es", "en")):
        return self.store.create_job(
            "https://www.youtube.com/@example/videos",
            list(languages),
            {"retries": 0, "pause_min": 0, "pause_max": 0, "backoff": 0,
             "max_backoff": 0, "max_videos": 0},
        )

    def run_next(self):
        job = self.store.next_job()
        self.assertIsNotNone(job)
        self.worker.process(job["id"])
        return self.store.get_job(job["id"])

    def test_partially_available_languages_are_not_marked_completed(self):
        job = self.new_job()
        result = self.run_next()
        self.assertEqual(result["id"], job["id"])
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["processed"], 2)
        self.assertEqual(self.store.video_status(job["id"], "abcdefghijk"), "partial")
        self.assertEqual(self.store.video_status(job["id"], "lmnopqrstuv"), "missing")
        self.assertFalse(self.store.has_languages("abcdefghijk", ["es", "en"]))

    def test_retry_only_incomplete_and_eventual_success(self):
        job = self.new_job()
        self.run_next()
        ChangingProvider.mode = "complete"
        self.assertTrue(self.store.set_status(job["id"], "queued", expected={"partial"}))
        result = self.run_next()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["downloaded"], 2)
        self.assertEqual(result["failed"], 0)
        self.assertTrue(self.store.has_languages("abcdefghijk", ["es", "en"]))
        self.assertTrue(self.store.has_languages("lmnopqrstuv", ["es", "en"]))
        self.assertEqual(self.store.video_status(job["id"], "abcdefghijk"), "downloaded")
        self.assertEqual(self.store.stats()["transcripts"], 4)

    def test_failed_video_never_yields_fully_completed_job(self):
        ChangingProvider.mode = "error"
        job = self.new_job(languages=("es", "en"))
        result = self.run_next()
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["failed"], 1)
        self.assertEqual(self.store.video_status(job["id"], "lmnopqrstuv"), "failed")

    def test_api_can_resume_partial_job(self):
        job = self.new_job()
        self.run_next()
        app = create_app(self.tmp.name, start_worker=False)
        with TestClient(app) as client:
            result = client.post(f'/api/jobs/{job["id"]}/resume')
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()["status"], "queued")

    def test_playlist_normalization_and_bad_ids(self):
        self.assertEqual(
            normalize_url("https://www.youtube.com/playlist?list=PL12345678901234&index=2"),
            "https://www.youtube.com/playlist?list=PL12345678901234",
        )
        with self.assertRaises(ValueError):
            normalize_url("https://youtube.com/playlist?list=bad&x=3")
        with self.assertRaises(ValueError):
            normalize_url("https://youtube.com/playlist?list=PL123%2Fbad")


if __name__ == "__main__":
    unittest.main()
