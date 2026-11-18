"""Transactional SQLite persistence. A fresh connection per operation avoids cross-thread use."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from uuid import uuid4

from .migrations import migrate


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self):
        with self.connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            migrate(conn)
            # An interrupted process must not leave a job 'running' forever.
            conn.execute("UPDATE jobs SET status='queued', updated_at=? WHERE status='running'", (now(),))

    def backup(self, destination):
        """Create an atomic, integrity-checked copy without pausing readers."""
        from .database_backup import backup_database
        return backup_database(self.path, destination)

    def create_job(self, url, languages, options):
        job_id = uuid4().hex[:16]
        stamp = now()
        with self.connection() as conn:
            conn.execute("""INSERT INTO jobs(id,url,languages,options,status,created_at,updated_at)
                            VALUES(?,?,?,?, 'queued',?,?)""",
                         (job_id, url, json.dumps(languages), json.dumps(options), stamp, stamp))
        return self.get_job(job_id)

    @staticmethod
    def _job(row):
        if row is None:
            return None
        job = dict(row)
        job["languages"] = json.loads(job["languages"])
        job["options"] = json.loads(job["options"])
        return job

    def get_job(self, job_id):
        with self.connection() as conn:
            return self._job(conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())

    def list_jobs(self, limit=100):
        with self.connection() as conn:
            return [self._job(row) for row in conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC,id DESC LIMIT ?", (limit,))]

    def next_job(self):
        with self.connection() as conn:
            row = conn.execute("SELECT id FROM jobs WHERE status='queued' ORDER BY created_at,id LIMIT 1").fetchone()
            if not row:
                return None
            result = conn.execute("UPDATE jobs SET status='running',updated_at=? WHERE id=? AND status='queued'",
                                  (now(), row['id']))
            return self._job(conn.execute('SELECT * FROM jobs WHERE id=?',(row['id'],)).fetchone()) if result.rowcount else None

    def set_status(self, job_id, status, error="", expected=None):
        with self.connection() as conn:
            if expected:
                result = conn.execute("UPDATE jobs SET status=?,error=?,updated_at=? WHERE id=? AND status IN (" +
                                      ",".join("?" for _ in expected) + ")",
                                      (status, error[:500], now(), job_id, *expected))
            else:
                result = conn.execute("UPDATE jobs SET status=?,error=?,updated_at=? WHERE id=?",
                                      (status, error[:500], now(), job_id))
            return result.rowcount > 0

    def record_video(self, job_id, video_id, title, status, error="", attempts=0):
        with self.connection() as conn:
            conn.execute("""INSERT INTO job_videos(job_id,video_id,title,status,error,attempts)
                VALUES(?,?,?,?,?,?) ON CONFLICT(job_id,video_id) DO UPDATE SET
                status=excluded.status,error=excluded.error,attempts=excluded.attempts,title=excluded.title""",
                (job_id, video_id, title[:400], status, error[:500], attempts))
            conn.execute("UPDATE job_videos SET last_attempt_at=? WHERE job_id=? AND video_id=?",
                         (now(), job_id, video_id))
            counts = conn.execute("""SELECT COUNT(*) n,
                SUM(status='downloaded') downloaded, SUM(status='skipped') skipped,
                SUM(status='failed') failed FROM job_videos
                WHERE job_id=? AND status IN ('downloaded','skipped','failed','missing','partial')""",
                (job_id,)).fetchone()
            conn.execute("""UPDATE jobs SET processed=?,downloaded=?,skipped=?,failed=?,updated_at=? WHERE id=?""",
                         (counts['n'] or 0, counts['downloaded'] or 0,
                          counts['skipped'] or 0, counts['failed'] or 0, now(), job_id))

    def set_total(self, job_id, total):
        with self.connection() as conn:
            conn.execute("UPDATE jobs SET total=?,updated_at=? WHERE id=?", (total, now(), job_id))

    def video_status(self, job_id, video_id):
        with self.connection() as conn:
            row = conn.execute("SELECT status FROM job_videos WHERE job_id=? AND video_id=?",
(job_id, video_id)).fetchone()
            return row['status'] if row else None

    def list_job_videos(self, job_id, limit=500):
        with self.connection() as conn:
            return [dict(row) for row in conn.execute(
                "SELECT * FROM job_videos WHERE job_id=? ORDER BY rowid DESC LIMIT ?", (job_id, limit))]

    def upsert_transcript(self, *, video_id, title, language, kind, source_url, original, text, segments):
        with self.connection() as conn:
            conn.execute("""INSERT INTO transcripts(video_id,title,language,kind,source_url,original,text,segments,created_at)
                VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(video_id,language) DO UPDATE SET
                title=excluded.title,kind=excluded.kind,source_url=excluded.source_url,
                original=excluded.original,text=excluded.text,segments=excluded.segments""",
                (video_id,title[:400],language,kind,source_url,original,text,json.dumps(segments,ensure_ascii=False),now()))

    def has_languages(self, video_id, languages):
        with self.connection() as conn:
            found = {row['language'] for row in conn.execute(
                'SELECT language FROM transcripts WHERE video_id=?', (video_id,))}
        # Tracks such as "en-orig" and "es-419" satisfy the requested base language.
        # Never mark a requested language successful unless a matching file exists.
        return all(any(actual == wanted or actual.startswith(wanted + '-')
                       for actual in found) for wanted in languages)

    def status_counts(self, job_id):
        """Authoritative per-video counts, including missing and partial captions."""
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) n FROM job_videos WHERE job_id=? GROUP BY status",
                (job_id,),
            ).fetchall()
        return {row['status']: row['n'] for row in rows}

    def search(self, query="", limit=100, offset=0, language=""):
        with self.connection() as conn:
            sql = 'SELECT id,video_id,title,language,kind,source_url,created_at,substr(text,1,220) preview FROM transcripts WHERE 1=1'
            params = []
            if query:
                sql += " AND (title LIKE ? ESCAPE '\\' OR text LIKE ? ESCAPE '\\')"
                escaped = query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
                params += ['%'+escaped+'%']*2
            if language:
                sql += ' AND language=?'
                params.append(language)
            sql += ' ORDER BY created_at DESC,id DESC LIMIT ? OFFSET ?'
            params += [limit,offset]
            return [dict(r) for r in conn.execute(sql,params)]

    def get_transcript(self, item_id):
        with self.connection() as conn:
            row=conn.execute('SELECT * FROM transcripts WHERE id=?',(item_id,)).fetchone()
            if row is None:
                return None
            item=dict(row)
            item['segments']=json.loads(item['segments'])
            return item

    def get_transcripts(self, ids):
        ids=list(dict.fromkeys(ids))
        if not ids or len(ids)>500:
            return []
        with self.connection() as conn:
            rows=conn.execute(f"SELECT * FROM transcripts WHERE id IN ({','.join('?'*len(ids))})",ids).fetchall()
        found={r['id']:{**dict(r),'segments':json.loads(r['segments'])} for r in rows}
        return [found[i] for i in ids if i in found]

    def stats(self):
        with self.connection() as conn:
            jobs=conn.execute("SELECT status,count(*) n FROM jobs GROUP BY status").fetchall()
            count=conn.execute('SELECT COUNT(*) n, COUNT(DISTINCT video_id) videos FROM transcripts').fetchone()
            return {"transcripts":count['n'],"videos":count['videos'],
                    "jobs":{row['status']:row['n'] for row in jobs}}
