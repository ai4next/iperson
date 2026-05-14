from __future__ import annotations

from pathlib import Path

import pytest

from iperson.core.kb.loader import load_document, load_documents_from_dir


def test_load_markdown(tmp_path: Path) -> None:
    """Test loading a .md file returns correct title, content, and source_type."""
    md_file = tmp_path / "test_doc.md"
    md_file.write_text("# Hello\n\nThis is a test markdown file.")

    result = load_document(str(md_file))

    assert result["title"] == "test_doc"
    assert result["content"] == "# Hello\n\nThis is a test markdown file."
    assert result["source_type"] == "file"
    assert result["source_path"] == str(md_file)


def test_load_txt(tmp_path: Path) -> None:
    """Test loading a .txt file returns correct content."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Some plain text content.")

    result = load_document(str(txt_file))

    assert result["title"] == "notes"
    assert result["content"] == "Some plain text content."
    assert result["source_type"] == "file"


def test_load_from_dir(tmp_path: Path) -> None:
    """Test loading multiple .md files from a directory."""
    (tmp_path / "doc1.md").write_text("# Doc 1")
    (tmp_path / "doc2.md").write_text("# Doc 2")
    (tmp_path / "doc3.md").write_text("# Doc 3")

    results = load_documents_from_dir(str(tmp_path), "*.md")

    assert len(results) == 3
    titles = {r["title"] for r in results}
    assert titles == {"doc1", "doc2", "doc3"}


def test_unsupported_type_raises(tmp_path: Path) -> None:
    """Test that unsupported file types raise ValueError."""
    xyz_file = tmp_path / "test.xyz"
    xyz_file.write_text("some data")

    with pytest.raises(ValueError, match="Unsupported file type"):
        load_document(str(xyz_file))