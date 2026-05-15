from __future__ import annotations

from html.parser import HTMLParser

from langchain_core.tools import tool


class _TextExtractor(HTMLParser):
    """HTML parser that accumulates plain text, stripping all tags."""

    def __init__(self) -> None:
        super().__init__()
        self._text_parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            stripped = data.strip()
            if stripped:
                self._text_parts.append(stripped)

    def get_text(self) -> str:
        return " ".join(self._text_parts)


def _strip_html(html: str) -> str:
    """Strip HTML tags and return plain text."""
    parser = _TextExtractor()
    parser.feed(html)
    return parser.get_text()


class _DDGResultParser(HTMLParser):
    """Parse DuckDuckGo HTML results page."""

    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._current: dict[str, str] | None = None
        self._in_result_a = False
        self._in_snippet = False
        self._in_snippet_a = False
        self._capture = False
        self._data_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)

        # Result title link: <a class="result__a" ...>
        if tag == "a" and attrs_dict.get("class") == "result__a":
            self._current = {"url": attrs_dict.get("href", ""), "title": ""}
            self._in_result_a = True
            self._data_parts = []
            return

        # Snippet link: <a class="result__snippet" ...>
        if tag == "a" and attrs_dict.get("class") == "result__snippet":
            self._in_snippet_a = True
            self._data_parts = []
            return

        if tag == "a" and attrs_dict.get("class") == "badge-link":
            self._data_parts = []
            return

    def handle_data(self, data: str) -> None:
        if self._in_result_a or self._in_snippet_a:
            self._data_parts.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_result_a and self._current is not None:
            self._current["title"] = " ".join(self._data_parts)
            self._in_result_a = False
            self._data_parts = []
            return

        if tag == "a" and self._in_snippet_a:
            snippet = " ".join(self._data_parts)
            if self._current is not None:
                self._current["snippet"] = snippet
                # Finalize current result
                if self._current.get("title") and self._current.get("url"):
                    self.results.append(self._current)
                self._current = None
            self._in_snippet_a = False
            self._data_parts = []
            return


@tool
def kb_search_tool(query: str, top_k: int = 5) -> str:
    """Search the local knowledge base using BM25 keyword search.
    Use this to find information stored in the personal knowledge base."""
    from iperson.core.kb.bm25 import BM25Index  # lazy import
    from iperson.storage.db import get_connection  # lazy import

    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT c.id, c.content, c.chunk_index, d.title AS doc_title
            FROM kb_chunks c
            JOIN kb_docs d ON c.kb_doc_id = d.id
            """
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        return "The knowledge base is empty. No results found."

    docs = [
        {"id": str(row["id"]), "text": row["content"]}
        for row in rows
    ]

    index = BM25Index()
    index.add_documents(docs)
    results = index.search(query, top_k=top_k)

    if not results:
        return f"No matching results found for query: {query}"

    lines: list[str] = [f"Top {len(results)} results for: {query}", ""]
    for i, r in enumerate(results, 1):
        # Find the matching row to get title and content
        row = next((row for row in rows if str(row["id"]) == r["id"]), None)
        if row:
            title = row["doc_title"] or "(no title)"
            content = row["content"]
        else:
            title = "(unknown)"
            content = r.get("text", "")

        preview = content[:200].replace("\n", " ").strip()
        score = r.get("score", 0.0)
        lines.append(f"{i}. [{title}] (score: {score:.3f})")
        lines.append(f"   {preview}...")
        lines.append("")

    return "\n".join(lines)


@tool
def web_search_tool(query: str, top_k: int = 5) -> str:
    """Search the web using DuckDuckGo.
    Use this for real-time or external information not in the local knowledge base."""
    import httpx

    url = f"https://html.duckduckgo.com/html/?q={query}"

    try:
        response = httpx.get(url, follow_redirects=True, timeout=15.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return f"Web search failed: {exc}"

    parser = _DDGResultParser()
    parser.feed(response.text)
    results = parser.results[:top_k]

    if not results:
        return f"No web search results found for: {query}"

    lines: list[str] = [f"Top {len(results)} web results for: {query}", ""]
    for i, r in enumerate(results, 1):
        title = r.get("title", "(no title)")
        snippet = r.get("snippet", "")
        result_url = r.get("url", "")
        lines.append(f"{i}. {title}")
        lines.append(f"   URL: {result_url}")
        if snippet:
            lines.append(f"   {snippet}")
        lines.append("")

    return "\n".join(lines)


@tool
def fetch_url_tool(url: str) -> str:
    """Fetch and extract plain text content from a URL.
    Returns the first 5000 characters of text content."""
    import httpx

    try:
        response = httpx.get(url, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return f"Failed to fetch URL: {exc}"

    text = _strip_html(response.text)
    if len(text) > 5000:
        text = text[:5000] + "\n\n[...content truncated at 5000 characters]"

    return text.strip() or "(no readable text content found on this page)"
