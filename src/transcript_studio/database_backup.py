"""Safe SQLite backup, validation and restore tools.

Backups use sqlite3.backup() so concurrent WAL writers cannot produce partial copies.
Files are created atomically without overwriting an existing user database.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from .migrations import SCHEMA_VERSION

REQUIRED = {"jobs", "job_videos", "transcripts"}


def _read_connection(source: Path) -> sqlite3.Connection:
    if not source.is_file():
        raise FileNotFoundError(f"No se encuentra la base de datos: {source}")
    return sqlite3.connect(source.as_uri() + "?mode=ro", uri=True, timeout=30)


def verify_database(source: str | Path) -> dict:
    """Check SQLite integrity, schema compatibility, and row counts."""
    source = Path(source).expanduser().resolve()
    with closing(_read_connection(source)) as conn:
        result = conn.execute("PRAGMA integrity_check").fetchone()
        if not result or result[0] != "ok":
            raise ValueError(f"SQLite integrity_check failed: {result}")
        version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        if version > SCHEMA_VERSION:
            raise ValueError(f"Esquema {version} incompatible: aplicación admite hasta {SCHEMA_VERSION}")
        tables = {
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if not REQUIRED.issubset(tables):
            raise ValueError("El archivo no contiene una biblioteca válida de Transcript Studio")
        counts = {
            name: conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            for name in sorted(REQUIRED)
        }
        return {"ok": True, "schema_version": version, "counts": counts,
                "bytes": source.stat().st_size}


def _atomic_sqlite_copy(source: Path, destination: Path) -> Path:
    source = source.expanduser().resolve()
    destination = destination.expanduser().resolve()
    if source == destination:
        raise ValueError("Origen y destino deben ser distintos")
    if destination.exists():
        raise FileExistsError(f"El destino ya existe y no se sobrescribirá: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=destination.parent, prefix=".transcript-studio-", suffix=".sqlite3",
            delete=False,
        ) as tmp:
            temporary = Path(tmp.name)
        # No writes to the active database: sqlite3 handles a consistent snapshot,
        # including transactions not yet checkpointed from WAL.
        with closing(_read_connection(source)) as input_db:
            with closing(sqlite3.connect(temporary, timeout=30)) as output_db:
                input_db.backup(output_db, pages=128, sleep=0.1)
                output_db.commit()
        verify_database(temporary)
        # Hardlink publishes the fully validated file, atomically and without replacing
        # any existing destination. Both paths are on the same filesystem.
        os.link(temporary, destination)
        return destination
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def backup_database(source: str | Path, destination: str | Path) -> Path:
    verify_database(source)
    return _atomic_sqlite_copy(Path(source), Path(destination))


def restore_database(source: str | Path, new_data_dir: str | Path) -> Path:
    """Restore into a NEW data directory; never replace the active user's DB."""
    source = Path(source).expanduser().resolve()
    root = Path(new_data_dir).expanduser().resolve()
    target = root / "library.sqlite3"
    if target.exists():
        raise FileExistsError(f"Ya existe {target}; elige otra carpeta de destino")
    verify_database(source)
    return _atomic_sqlite_copy(source, target)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Copias verificadas de la biblioteca SQLite")
    sub = parser.add_subparsers(dest="command", required=True)
    backup = sub.add_parser("backup", help="Guardar copia sin modificar la biblioteca")
    backup.add_argument("--data-dir", help="Directorio de datos actual")
    backup.add_argument("--output", required=True, help="Ruta nueva del archivo .sqlite3")
    verify = sub.add_parser("verify", help="Comprobar integridad de una copia")
    verify.add_argument("--input", required=True)
    restore = sub.add_parser("restore", help="Restaurar en un directorio NUEVO")
    restore.add_argument("--input", required=True, help="Copia de origen")
    restore.add_argument("--data-dir", required=True, help="Nueva carpeta sin biblioteca previa")
    args = parser.parse_args(argv)
    try:
        if args.command == "backup":
            from .app import default_data_dir
            root = Path(args.data_dir or default_data_dir()).expanduser()
            output = backup_database(root / "library.sqlite3", args.output)
            result = {"backup": str(output), **verify_database(output)}
        elif args.command == "verify":
            result = verify_database(args.input)
        else:
            output = restore_database(args.input, args.data_dir)
            result = {"restored": str(output), **verify_database(output)}
    except (OSError, sqlite3.DatabaseError, ValueError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
