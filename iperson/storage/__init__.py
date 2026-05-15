from __future__ import annotations

from iperson.storage.db import get_connection


def init_db() -> None:
    """Initialize all SQLite tables using CREATE TABLE IF NOT EXISTS."""
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS contents (
                id TEXT PRIMARY KEY,
                persona_name TEXT,
                recipe_name TEXT,
                topic TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL DEFAULT '',
                content_type TEXT NOT NULL DEFAULT '',
                draft_content TEXT,
                final_content TEXT,
                quality_score REAL,
                style_consistency REAL,
                ai_score REAL,
                model_used TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS publications (
                id TEXT PRIMARY KEY,
                content_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                scheduled_at TEXT,
                retry_count INTEGER DEFAULT 0,
                error_message TEXT DEFAULT '',
                published_at TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (content_id) REFERENCES contents(id)
            );

            CREATE TABLE IF NOT EXISTS kb_docs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS kb_chunks (
                id TEXT PRIMARY KEY,
                kb_doc_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (kb_doc_id) REFERENCES kb_docs(id)
            );

            CREATE TABLE IF NOT EXISTS content_metrics (
                id TEXT PRIMARY KEY,
                content_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                collected_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (content_id) REFERENCES contents(id)
            );
        """)
        conn.commit()
    finally:
        conn.close()