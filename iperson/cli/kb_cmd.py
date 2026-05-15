from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import numpy as np
import typer
from rich.console import Console
from rich.table import Table

from iperson.config import ensure_data_dirs
from iperson.core.kb.chunker import SemanticChunker
from iperson.core.kb.embedder import OpenAIEmbedder
from iperson.core.kb.loader import load_document, load_documents_from_dir
from iperson.core.kb.vector_store import VectorStore
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
    """Load documents from path, chunk them, generate embeddings, and store in SQLite."""
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

    embedder = OpenAIEmbedder()
    chunker = SemanticChunker(chunk_size=512, overlap=64)
    conn = get_connection()

    try:
        total_chunks = 0
        with console.status("[bold blue]Generating embeddings..."):
            for doc in documents:
                doc_id = uuid.uuid4().hex
                conn.execute(
                    "INSERT INTO kb_docs (id, title, source, content) VALUES (?, ?, ?, ?)",
                    (doc_id, doc["title"], doc.get("source_path", ""), doc["content"]),
                )

                chunks = chunker.chunk(doc["content"])
                chunk_texts = [chunk["text"] for chunk in chunks]
                chunk_embeddings = (
                    await embedder.embed_batch(chunk_texts) if chunk_texts else []
                )

                for chunk, emb in zip(chunks, chunk_embeddings):
                    chunk_id = uuid.uuid4().hex
                    emb_blob = np.array(emb, dtype=np.float64).tobytes()
                    conn.execute(
                        "INSERT INTO kb_chunks (id, kb_doc_id, chunk_index, content, embedding) VALUES (?, ?, ?, ?, ?)",
                        (chunk_id, doc_id, chunk["index"], chunk["text"], emb_blob),
                    )
                    total_chunks += 1

            conn.commit()
        console.print(f"[green]Successfully imported {len(documents)} document(s) ({total_chunks} chunks) with embeddings.[/green]")
    finally:
        conn.close()


async def _search_kb(query: str, top_k: int) -> None:
    """Search the knowledge base using vector similarity."""
    ensure_data_dirs()
    init_db()

    conn = get_connection()
    try:
        # Load chunks with embeddings from DB
        rows = conn.execute(
            """SELECT c.id, c.content, c.chunk_index, c.embedding, d.title as doc_title
               FROM kb_chunks c
               JOIN kb_docs d ON c.kb_doc_id = d.id
               WHERE c.embedding IS NOT NULL"""
        ).fetchall()

        if not rows:
            # Fallback to LIKE search if no embeddings exist
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

            table = Table(title=f"Search Results for: {query} (keyword)")
            table.add_column("#", style="dim")
            table.add_column("Document", style="cyan")
            table.add_column("Chunk", style="magenta")
            table.add_column("Content Preview", style="white")

            for i, row in enumerate(rows, 1):
                content = row["content"]
                preview = content[:120] + "..." if len(content) > 120 else content
                table.add_row(str(i), row["doc_title"], str(row["chunk_index"]), preview)

            console.print(table)
            return

        # Build in-memory VectorStore
        vs = VectorStore()
        for row in rows:
            emb = np.frombuffer(row["embedding"], dtype=np.float64).tolist()
            vs.add(emb, {
                "id": row["id"],
                "text": row["content"],
                "doc_title": row["doc_title"],
                "chunk_index": row["chunk_index"],
            })

        # Generate query embedding and search
        with console.status("[bold blue]Generating query embedding..."):
            embedder = OpenAIEmbedder()
            query_vector = await embedder.embed(query)

        results = vs.search(query_vector, top_k=top_k)

        if not results:
            console.print("[yellow]No relevant results found.[/yellow]")
            return

        table = Table(title=f"Search Results for: {query}")
        table.add_column("#", style="dim")
        table.add_column("Document", style="cyan")
        table.add_column("Score", style="green", justify="right")
        table.add_column("Content Preview", style="white")

        for i, result in enumerate(results, 1):
            content = result["text"]
            score = result["score"]
            preview = content[:120] + "..." if len(content) > 120 else content
            table.add_row(
                str(i),
                result.get("doc_title", "?"),
                f"{score:.3f}",
                preview,
            )

        console.print(table)
    finally:
        conn.close()