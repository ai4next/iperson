from __future__ import annotations

from pathlib import Path


def load_document(path: str) -> dict:
    """Load a single document from the given file path.

    Supports .md, .txt, and .pdf file types.

    Args:
        path: Absolute or relative path to the document file.

    Returns:
        A dict with keys: title, content, source_type, source_path.

    Raises:
        ValueError: If the file type is unsupported.
    """
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix == ".md":
        content = file_path.read_text(encoding="utf-8")
        title = file_path.stem
    elif suffix == ".txt":
        content = file_path.read_text(encoding="utf-8")
        title = file_path.stem
    elif suffix == ".pdf":
        title = file_path.stem
        content = _load_pdf(file_path)
    else:
        msg = f"Unsupported file type: {suffix}"
        raise ValueError(msg)

    return {
        "title": title,
        "content": content,
        "source_type": "file",
        "source_path": str(file_path.resolve()),
    }


def _load_pdf(file_path: Path) -> str:
    """Extract text from a PDF file using PyPDF2.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Extracted text content.

    Raises:
        ValueError: If PyPDF2 is not installed.
    """
    try:
        import PyPDF2
    except ImportError:
        msg = (
            "PyPDF2 is required to load PDF files. "
            "Install it with: pip install PyPDF2"
        )
        raise ValueError(msg) from None

    text_parts: list[str] = []
    with file_path.open("rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    return "\n\n".join(text_parts)


def load_documents_from_dir(directory: str, glob_pattern: str = "*.md") -> list[dict]:
    """Load all documents matching the glob pattern from a directory.

    Args:
        directory: Path to the directory to scan.
        glob_pattern: Glob pattern for matching files (default: "*.md").

    Returns:
        A list of document dicts, each as returned by load_document.
    """
    dir_path = Path(directory)
    documents: list[dict] = []

    for file_path in sorted(dir_path.glob(glob_pattern)):
        if file_path.is_file():
            documents.append(load_document(str(file_path)))

    return documents