from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any


class AuditReport:
    """Data model for an audit report covering all 6 quality dimensions."""

    def __init__(self, content_id: str) -> None:
        self.id = str(uuid.uuid4())
        self.content_id = content_id
        self.version = 1
        self.created_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.scores: dict[str, float] = {}
        self.dimensions: dict[str, Any] = {}

    def add_dimension(self, name: str, result: dict) -> None:
        """Store a dimension check result and its score."""
        self.dimensions[name] = result
        self.scores[name] = result.get("score", 0.0)

    @property
    def overall_status(self) -> str:
        """Determine overall audit status.

        - "pass" if all dimension scores >= 0.5 and all critical dimension scores >= 0.3
        - "fail" if any critical dimension score < 0.3
        - "review" otherwise
        """
        if not self.scores:
            return "fail"

        critical_dimensions = {"grounding", "keyword_fit"}
        has_critical = any(c in self.scores for c in critical_dimensions)

        all_above_half = all(v >= 0.5 for v in self.scores.values())
        critical_ok = True
        if has_critical:
            critical_ok = all(
                self.scores.get(c, 1.0) >= 0.3 for c in critical_dimensions
            )

        if all_above_half and critical_ok:
            return "pass"

        if has_critical and any(
            self.scores.get(c, 1.0) < 0.3 for c in critical_dimensions
        ):
            return "fail"

        return "review"

    def to_dict(self) -> dict:
        """Serialize the report to a dictionary."""
        return {
            "id": self.id,
            "content_id": self.content_id,
            "version": self.version,
            "created_at": self.created_at,
            "scores": dict(self.scores),
            "dimensions": dict(self.dimensions),
            "overall_status": self.overall_status,
        }