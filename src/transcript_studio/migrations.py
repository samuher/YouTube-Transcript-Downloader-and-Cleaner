"""Transactional SQLite schema migrations.

0.2.0 installations used PRAGMA user_version=0. Migrations preserve existing rows
and are committed as one transaction; unsupported newer schemas fail closed.
"""
from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 2
SCHEMA_SQL = "CREATE TABLE IF NOT EXISTS jobs (\n                  id TEXT PRIMARY KEY, url TEXT NOT NULL, languages TEXT NOT NULL,\n                  options TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued',\n                  total INTEGER NOT NULL DEFAULT 0, processed INTEGER NOT NULL DEFAULT 0,\n                  downloaded INTEGER NOT NULL DEFAULT 0, skipped INTEGER NOT NULL DEFAULT 0,\n                  failed INTEGER NOT NULL DEFAULT 0, error TEXT NOT NULL DEFAULT '',\n                  created_at TEXT NOT NULL, updated_at TEXT NOT NULL\n                );\n                CREATE TABLE IF NOT EXISTS job_videos (\n                  job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,\n                  video_id TEXT NOT NULL, title TEXT NOT NULL, status TEXT NOT NULL,\n                  error TEXT NOT NULL DEFAULT '', attempts INTEGER NOT NULL DEFAULT 0,\n                  PRIMARY KEY (job_id, video_id)\n                );\n                CREATE TABLE IF NOT EXISTS transcripts (\n                  id INTEGER PRIMARY KEY AUTOINCREMENT,\n                  video_id TEXT NOT NULL, title TEXT NOT NULL,\n                  language TEXT NOT NULL, kind TEXT NOT NULL,\n                  source_url TEXT NOT NULL, original TEXT NOT NULL,\n                  text TEXT NOT NULL, segments TEXT NOT NULL,\n                  created_at TEXT NOT NULL,\n                  UNIQUE(video_id, language)\n                );\n                CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status,created_at);\n                CREATE INDEX IF NOT EXISTS idx_transcripts_title ON transcripts(title);\n                CREATE INDEX IF NOT EXISTS idx_job_videos_status ON job_videos(job_id,status);"

REQUIRED_TABLES = {"jobs", "job_videos", "transcripts"}


def migrate(conn: sqlite3.Connection) -> None:
    version = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if version > SCHEMA_VERSION:
        raise RuntimeError(
            f"Database schema version {version} is newer than supported {SCHEMA_VERSION}. "
            "Update the application; the database was not modified."
        )
    conn.execute("BEGIN IMMEDIATE")
    try:
        # Separate statements preserve transactional DDL semantics; executescript()
        # commits an open transaction and would make a mid-migration failure unsafe.
        for statement in SCHEMA_SQL.split(";"):
            if statement.strip():
                conn.execute(statement)
        present = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        if not REQUIRED_TABLES.issubset(present):
            raise RuntimeError("Database schema is incomplete")
        required = {
            "jobs": {"id", "url", "languages", "options", "status", "processed", "total"},
            "job_videos": {"job_id", "video_id", "status", "attempts"},
            "transcripts": {"id", "video_id", "language", "text", "segments"},
        }
        for table, columns in required.items():
            actual = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
            if not columns.issubset(actual):
                raise RuntimeError(f"Incompatible schema for {table}; database unchanged")
        if version < 2:
            columns = {r[1] for r in conn.execute("PRAGMA table_info(job_videos)")}
            if "last_attempt_at" not in columns:
                conn.execute("ALTER TABLE job_videos ADD COLUMN last_attempt_at TEXT")
        conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
