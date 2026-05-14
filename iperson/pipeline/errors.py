from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class PipelineError:
    error_code: str
    stage: str
    message: str
    recoverable: bool = False
    attempts: int = 1
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())