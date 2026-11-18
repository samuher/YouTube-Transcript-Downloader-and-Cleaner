"""Migration and backup regression tests: no external network or YouTube access."""
from __future__ import annotations

from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from transcript_studio.database_backup import backup_database, restore_database, verify_database
from transcript_studio.migrations import SCHEMA_SQL, SCHEMA_VERSION
from transcript_studio.storage import Store
import transcript_studio.migrations as migrations


def legacy_database(path):
    """Create a representative SQLite schema written by Transcript Studio 0.2.0."""
    with sqlite3.connect(path) as conn:
        for statement in SCHEMA_SQL.split(";"):
            if statement.strip():
                conn.execute(statement)
        conn.execute("PRAGMA user_version=0")
        conn.execute(
            "INSERT INTO jobs(id,url,languages,options,status,created_at,updated_at) "
            "VALUES('legacy','https://www.youtube.com/watch?v=abcdefghijk','[\"es\"]',"
            "'{}','paused','2026-01-01','2026-01-01')"
        )
        conn.execute(
            "INSERT INTO job_videos(job_id,video_id,title,status,error,attempts) "
            "VALUES('legacy','abcdefghijk','Clase','downloaded','',1)"
        )
        conn.execute(
            "INSERT INTO transcripts(video_id,title,language,kind,source_url,original,text,segments,created_at) "
            "VALUES('abcdefghijk','Clase','es','automatic','https://www.youtube.com/watch?v=abcdefghijk',"
            "'WEBVTT','Hola','[]','2026-01-01')"
        )


class DatabaseMaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_migrates_legacy_rows_without_loss(self):
        path = self.root / "legacy.sqlite3"
        legacy_database(path)
        store = Store(path)
        self.assertEqual(store.get_job("legacy")["status"], "paused")
        self.assertEqual(store.stats()["transcripts"], 1)
        self.assertEqual(store.video_status("legacy", "abcdefghijk"), "downloaded")
        with sqlite3.connect(path) as conn:
            self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
            columns = {x[1] for x in conn.execute("PRAGMA table_info(job_videos)")}
            self.assertIn("last_attempt_at", columns)
        Store(path)
        self.assertEqual(store.stats()["transcripts"], 1)

    def test_new_database_and_timestamp(self):
        store = Store(self.root / "fresh.sqlite3")
        job = store.create_job("https://youtube.com/watch?v=abcdefghijk", ["es"], {})
        store.record_video(job["id"], "abcdefghijk", "Test", "downloaded", attempts=2)
        with sqlite3.connect(store.path) as conn:
            value = conn.execute("SELECT last_attempt_at FROM job_videos").fetchone()[0]
            self.assertTrue(value.startswith("20"))

    def test_transactional_rollback_on_migration_error(self):
        path = self.root / "broken.sqlite3"
        with patch.object(
            migrations, "SCHEMA_SQL", "CREATE TABLE attempted(x INTEGER); SELECT does_not_exist FROM attempted;"
        ):
            with self.assertRaises(sqlite3.DatabaseError):
                Store(path)
        with sqlite3.connect(path) as conn:
            self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 0)
            self.assertIsNone(
                conn.execute("SELECT name FROM sqlite_master WHERE name='attempted'").fetchone()
            )

    def test_newer_schema_refused(self):
        path = self.root / "newer.sqlite3"
        legacy_database(path)
        with sqlite3.connect(path) as conn:
            conn.execute("PRAGMA user_version=999")
        with self.assertRaises(RuntimeError):
            Store(path)
        with sqlite3.connect(path) as conn:
            self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 999)

    def test_backup_includes_committed_wal_rows(self):
        store = Store(self.root / "library.sqlite3")
        store.create_job("https://youtube.com/watch?v=abcdefghijk", ["es"], {})
        backup = self.root / "backups" / "snapshot.sqlite3"
        with sqlite3.connect(store.path) as writer:
            writer.execute("PRAGMA journal_mode=WAL")
            writer.execute("INSERT INTO jobs(id,url,languages,options,status,created_at,updated_at) "
                           "VALUES('second','https://youtube.com/@test','[\"es\"]','{}','paused','x','x')")
            writer.commit()
            result = store.backup(backup)
        self.assertEqual(result, backup)
        self.assertEqual(verify_database(backup)["counts"]["jobs"], 2)
        with self.assertRaises(FileExistsError):
            backup_database(store.path, backup)

    def test_restore_new_directory_preserves_data(self):
        store = Store(self.root / "library.sqlite3")
        job = store.create_job("https://youtube.com/watch?v=abcdefghijk", ["es"], {})
        backup = backup_database(store.path, self.root / "snapshot.sqlite3")
        restored = restore_database(backup, self.root / "restored")
        self.assertEqual(restored, self.root / "restored" / "library.sqlite3")
        reopened = Store(restored)
        self.assertIsNotNone(reopened.get_job(job["id"]))
        with self.assertRaises(FileExistsError):
            restore_database(backup, self.root / "restored")

    def test_invalid_file_is_rejected(self):
        corrupted = self.root / "bad.sqlite3"
        corrupted.write_text("not sqlite", encoding="utf-8")
        with self.assertRaises((sqlite3.DatabaseError, ValueError)):
            verify_database(corrupted)
        with self.assertRaises((sqlite3.DatabaseError, ValueError)):
            restore_database(corrupted, self.root / "restored")
        self.assertFalse((self.root / "restored" / "library.sqlite3").exists())


if __name__ == "__main__":
    unittest.main()
