from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from iperson.config import ensure_data_dirs
from iperson.core.kb.chunker import SemanticChunker
from iperson.core.kb.loader import load_document, load_documents_from_dir
from iperson.storage import init_db
from iperson.storage.db import get_connection

kb_group = typer.Typer(help="Knowledge base management")

console = Console()


@kb_group.command(name="import")
def import_docs(
    path: str = typer.Argument(..., help="File or directory to import"),
    glob: str = typer.Option("*.md", "--glob", "-g", help="File glob pattern"),
) -> None:
    """Import documents into the knowledge base."""
    asyncio.run(_import_docs(path, glob))


@kb_group.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    top_k: int = typer.Option(5, "--top-k", "-n", help="Number of results"),
) -> None:
    """Search the knowledge base."""
    asyncio.run(_search_kb(query, top_k))


async def _import_docs(path: str, glob_pattern: str) -> None:
    """Load documents from path, chunk them, and store in SQLite."""
    ensure_data_dirs()
    init_db()

    target_path = Path(path).expanduser()
    if not target_path.exists():
        console.print(f"[red]Error:[/red] Path not found: {target_path}")
        raise typer.Exit(1)

    # Load documents
    if target_path.is_file():
        documents = [load_document(str(target_path))]
    else:
        documents = load_documents_from_dir(str(target_path), glob_pattern)

    if not documents:
        console.print("[yellow]No documents found to import.[/yellow]")
        raise typer.Exit(0)

    chunker = SemanticChunker(chunk_size=512, overlap=64)
    conn = get_connection()

    try:
        total_chunks = 0
        for doc in documents:
            doc_id = uuid.uuid4().hex
            conn.execute(
                "INSERT INTO kb_docs (id, title, source, content) VALUES (?, ?, ?, ?)",
                (doc_id, doc["title"], doc.get("source_path", ""), doc["content"]),
            )

            chunks = chunker.chunk(doc["content"])
            for chunk in chunks:
                chunk_id = uuid.uuid4().hex
                conn.execute(
                    "INSERT INTO kb_chunks (id, kb_doc_id, chunk_index, content) VALUES (?, ?, ?, ?)",
                    (chunk_id, doc_id, chunk["index"], chunk["text"]),
                )
                total_chunks += 1

        conn.commit()
        console.print(f"[green]Successfully imported {len(documents)} document(s) ({total_chunks} chunks).[/green]")
    finally:
        conn.close()


async def _search_kb(query: str, top_k: int) -> None:
    """Query kb_chunks table with basic text search and display results."""
    ensure_data_dirs()
    init_db()

    conn = get_connection()
    try:
        # Basic LIKE-based text search on chunk content
        like_pattern = f"%{query}%"
        rows = conn.execute(
            """SELECT c.id, c.content, c.chunk_index, d.title as doc_title
               FROM kb_chunks c
               JOIN kb_docs d ON c.kb_doc_id = d.id
               WHERE c.content LIKE ?
               LIMIT ?""",
            (like_pattern, top_k),
        ).fetchall()

        if not rows:
            console.print("[yellow]No results found.[/yellow]")
            return

        table = Table(title=f"Search Results for: {query}")
        table.add_column("#", style="dim")
        table.add_column("Document", style="cyan")
        table.add_column("Chunk", style="magenta")
        table.add_column("Content Preview", style="white")

        for i, row in enumerate(rows, 1):
            content = row["content"]
            preview = content[:120] + "..." if len(content) > 120 else content
            table.add_row(str(i), row["doc_title"], str(row["chunk_index"]), preview)

        console.print(table)
    finally:
        conn.close()