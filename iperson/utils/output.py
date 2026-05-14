from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from iperson.config import get_output_dir


def _slugify(text: str) -> str:
    """Convert text to a safe filesystem slug."""
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[-\s]+", "-", slug).strip("-")
    return slug or "untitled"


def create_output_dir(topic: str) -> Path:
    """Create a timestamped output directory for the given topic.

    Returns a path like: output/{timestamp}-{slug}/
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = _slugify(topic)
    out_dir = get_output_dir() / f"{timestamp}-{slug}"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def write_article(out_dir: Path, content: str) -> Path:
    """Write an article file to the given output directory."""
    path = out_dir / "article.md"
    path.write_text(content, encoding="utf-8")
    return path


def write_audit_report(out_dir: Path, report: dict[str, Any]) -> Path:
    """Write an audit report (JSON) to the given output directory."""
    path = out_dir / "audit_report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_platform_content(out_dir: Path, platform: str, content: str) -> Path:
    """Write platform-specific content to platforms/ subdirectory."""
    platforms_dir = out_dir / "platforms"
    platforms_dir.mkdir(exist_ok=True)
    path = platforms_dir / f"{platform}.md"
    path.write_text(content, encoding="utf-8")
    return path


def write_publish_package(out_dir: Path, package: dict[str, Any]) -> Path:
    """Write a publish package (JSON) to the given output directory."""
    path = out_dir / "publish_package.json"
    path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    return path