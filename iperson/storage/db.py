from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from iperson.config import load_config


def get_connection() -> sqlite3.Connection:
    """Create and return a SQLite connection with WAL mode and foreign keys enabled.

    Uses IPERSON_DB_PATH env var override if set, otherwise reads from config.
    Returns a plain sqlite3.Connection (not async) for simplicity in CLI context.
    """
    db_path_str = os.environ.get("IPERSON_DB_PATH")
    if db_path_str:
        db_path = Path(db_path_str)
    else:
        config = load_config()
        db_path = Path(config["db"]["path"]).expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn