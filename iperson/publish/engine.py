from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from iperson.storage.db import get_connection

# Valid status transitions
VALID_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["queued"],
    "queued": ["publishing", "draft"],
    "publishing": ["published", "failed"],
    "failed": ["publishing", "draft"],
    "published": [],
}


class PublicationStatus:
    def __init__(self, initial: str = "draft") -> None:
        self.current = initial

    def can_transition_to(self, target: str) -> bool:
        return target in VALID_TRANSITIONS.get(self.current, [])

    def transition_to(self, target: str) -> str:
        if not self.can_transition_to(target):
            allowed = VALID_TRANSITIONS.get(self.current, [])
            raise ValueError(
                f"Cannot transition from {self.current} to {target}. "
                f"Allowed: {allowed}"
            )
        self.current = target
        return self.current


class PublishEngine:
    def create(
        self,
        content_id: str,
        platform: str,
        scheduled_at: str | None = None,
    ) -> dict[str, Any]:
        pub_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        conn = get_connection()
        try:
            conn.execute(
                """INSERT INTO publications (id, content_id, platform, status, scheduled_at, retry_count, error_message, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, 0, '', ?, ?)""",
                (pub_id, content_id, platform, "draft", scheduled_at or "", now, now),
            )
            conn.commit()
        finally:
            conn.close()
        return {
            "id": pub_id,
            "content_id": content_id,
            "platform": platform,
            "status": "draft",
            "scheduled_at": scheduled_at,
        }

    def update_status(self, pub_id: str, new_status: str, error: str = "") -> None:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT status FROM publications WHERE id = ?", (pub_id,)
            ).fetchone()
            if not row:
                raise ValueError(f"Publication not found: {pub_id}")
            status = PublicationStatus(row["status"])
            status.transition_to(new_status)
            now = datetime.now(timezone.utc).isoformat()
            if error:
                conn.execute(
                    "UPDATE publications SET status = ?, error_message = ?, retry_count = retry_count + 1, updated_at = ? WHERE id = ?",
                    (new_status, error, now, pub_id),
                )
            else:
                conn.execute(
                    "UPDATE publications SET status = ?, updated_at = ? WHERE id = ?",
                    (new_status, now, pub_id),
                )
            conn.commit()
        finally:
            conn.close()

    def list_publications(self, status: str | None = None) -> list[dict[str, Any]]:
        conn = get_connection()
        try:
            if status:
                rows = conn.execute(
                    "SELECT * FROM publications WHERE status = ? ORDER BY created_at DESC",
                    (status,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM publications ORDER BY created_at DESC"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()