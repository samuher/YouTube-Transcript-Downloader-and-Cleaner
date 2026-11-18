"""The opt-in live smoke test itself is validated without touching the network."""
from pathlib import Path
import importlib.util
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
module_path = Path(__file__).resolve().parents[1] / "scripts" / "yt_integration_smoke.py"
spec = importlib.util.spec_from_file_location("manual_smoke", module_path)
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)

from transcript_studio.provider import DownloadedCaption


class SmokeScriptTests(unittest.TestCase):
    def test_consent_required_without_network(self):
        with self.assertRaises(SystemExit) as context:
            smoke.main([
                "--manual", "es:https://www.youtube.com/watch?v=abcdefghijk",
                "--automatic", "es:https://www.youtube.com/watch?v=lmnopqrstuv",
                "--missing", "es:https://www.youtube.com/watch?v=wxyzabcdefg",
            ])
        self.assertEqual(context.exception.code, 2)

    def test_rejects_channel_and_third_party(self):
        with self.assertRaises(Exception):
            smoke.case_argument("es:https://youtube.com/@channel")
        with self.assertRaises(Exception):
            smoke.case_argument("es:https://example.org/watch?v=abcdefghijk")
        self.assertEqual(
            smoke.case_argument("es:https://youtu.be/abcdefghijk?t=2"),
            ("es", "abcdefghijk"),
        )

    def test_manual_track_export_validated_offline(self):
        sample = DownloadedCaption(
            language="es",
            kind="manual",
            original="WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nHola mundo\n",
            text="Hola mundo",
            segments=[{"start": 0.0, "end": 2.0, "text": "Hola mundo"}],
        )
        with patch.object(smoke.YouTubeProvider, "get_captions", return_value=[sample]) as mock:
            result = smoke.run_case("manual", "es", "abcdefghijk")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["segments"], 1)
        mock.assert_called_once()

    def test_missing_track_requires_no_captions(self):
        with patch.object(smoke.YouTubeProvider, "get_captions", return_value=[]):
            result = smoke.run_case("missing", "es", "abcdefghijk")
        self.assertEqual(result["status"], "expected_missing")


if __name__ == "__main__":
    unittest.main()
