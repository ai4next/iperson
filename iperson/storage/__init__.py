from __future__ import annotations

from iperson.storage.db import get_connection


def init_db() -> None:
    """Initialize all SQLite tables using CREATE TABLE IF NOT EXISTS."""
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS contents (
                id TEXT PRIMARY KEY,
                persona_id TEXT,
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

            CREATE TABLE IF NOT EXISTS personas (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL DEFAULT '',
                persona_type TEXT NOT NULL DEFAULT '',
                language TEXT NOT NULL DEFAULT 'zh-CN',
                system_prompt TEXT NOT NULL DEFAULT '',
                tone_instruction TEXT NOT NULL DEFAULT '',
                style_profile TEXT NOT NULL DEFAULT '',
                few_shot_examples TEXT NOT NULL DEFAULT '',
                banned_patterns TEXT NOT NULL DEFAULT '',
                keywords TEXT NOT NULL DEFAULT '',
                focus_areas TEXT NOT NULL DEFAULT '',
                content_types TEXT NOT NULL DEFAULT '',
                is_active INTEGER NOT NULL DEFAULT 1,
                config TEXT DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS publications (
                id TEXT PRIMARY KEY,
                content_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
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
                embedding BLOB,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (kb_doc_id) REFERENCES kb_docs(id)
            );

            CREATE TABLE IF NOT EXISTS audit_reports (
                id TEXT PRIMARY KEY,
                report_type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id TEXT PRIMARY KEY,
                pipeline_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                started_at TEXT,
                completed_at TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        conn.commit()
    finally:
        conn.close()