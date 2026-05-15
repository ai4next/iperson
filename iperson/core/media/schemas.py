from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GeneratedImage:
    path: Path
    prompt: str
    alt_text: str
    is_cover: bool = False
    position: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)