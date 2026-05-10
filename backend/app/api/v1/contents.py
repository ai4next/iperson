"""Content pipeline endpoints — create, review, schedule, publish."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import paginate, paginated_response, pagination_params
from app.core.tenant import get_current_tenant_id
from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.content import Content
from app.models.user import User
from app.models.version import ContentVersion
from app.schemas import (
    ContentApprove,
    ContentCreate,
    ContentResponse,
    ContentSchedule,
    ContentUpdate,
)

router = APIRouter(prefix="/contents", tags=["contents"])


async def _get_content(db: AsyncSession, content_id: str) -> Content:
    """Fetch content with tenant-scoped access check."""
    tid = get_current_tenant_id()
    result = await db.execute(
        select(Content).where(Content.id == content_id, Content.tenant_id == tid)
    )
    content = result.scalar_one_or_none()
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    return content


async def _create_version(
    db: AsyncSession, content: Content, reason: str, changed_by: str = "system"
) -> None:
    """Create an immutable snapshot of content state."""
    # Find next version number
    result = await db.execute(
        select(ContentVersion).where(ContentVersion.content_id == content.id)
        .order_by(ContentVersion.version.desc()).limit(1)
    )
    last = result.scalar_one_or_none()
    next_ver = (last.version + 1) if last else 1

    version = ContentVersion(
        content_id=content.id,
        version=next_ver,
        content_text=content.final_content or content.draft_content,
        status=content.status,
        changed_by=changed_by,
        change_reason=reason,
        created_at=datetime.now(UTC),
    )
    db.add(version)


@router.get("/")
async def list_contents(
    pagination: tuple[int, int, int] = Depends(pagination_params),
    status_filter: str | None = Query(None, alias="status"),
    persona_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    page, page_size, offset = pagination
    tid = get_current_tenant_id()
    query = select(Content).where(Content.tenant_id == tid)

    if status_filter:
        query = query.where(Content.status == status_filter)
    if persona_id:
        query = query.where(Content.persona_id == persona_id)

    query = query.order_by(Content.created_at.desc())
    items, total = await paginate(db, query, page, page_size)

    return paginated_response(
        items=[ContentResponse.model_validate(c) for c in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("/", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    body: ContentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("editor")),
):
    tid = get_current_tenant_id()
    content = Content(
        tenant_id=tid,
        persona_id=body.persona_id,
        title=body.title,
        topic_id=body.topic_id,
        status="draft",
    )
    db.add(content)
    await db.flush()
    return content


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await _get_content(db, content_id)


@router.get("/{content_id}/versions")
async def get_content_versions(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get version history for a piece of content."""
    content = await _get_content(db, content_id)
    result = await db.execute(
        select(ContentVersion).where(ContentVersion.content_id == content.id)
        .order_by(ContentVersion.version.desc())
    )
    versions = result.scalars().all()
    return [
        {
            "version": v.version,
            "status": v.status,
            "changed_by": v.changed_by,
            "reason": v.change_reason,
            "created_at": str(v.created_at),
            "text_preview": (v.content_text or "")[:200],
        }
        for v in versions
    ]


@router.patch("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: str,
    body: ContentUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("editor")),
):
    content = await _get_content(db, content_id)

    update_data = body.model_dump(exclude_unset=True)
    status_changed = "status" in update_data and update_data["status"] != content.status

    for key, value in update_data.items():
        setattr(content, key, value)

    if status_changed:
        await _create_version(db, content, reason=f"Status changed to {content.status}", changed_by=user.display_name)

    await db.flush()
    return content


@router.post("/{content_id}/approve", response_model=ContentResponse)
async def approve_content(
    content_id: str,
    body: ContentApprove,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("editor")),
):
    content = await _get_content(db, content_id)

    if body.final_content is not None:
        content.final_content = body.final_content
    content.status = "approved"

    await _create_version(db, content, reason="Content approved by editor", changed_by=user.display_name)
    await db.flush()
    return content


@router.post("/{content_id}/reject", response_model=ContentResponse)
async def reject_content(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("editor")),
):
    content = await _get_content(db, content_id)
    content.status = "draft"  # Send back to draft for revision
    await _create_version(db, content, reason="Content rejected, returned to draft", changed_by=user.display_name)
    await db.flush()
    return content


@router.post("/{content_id}/schedule", response_model=ContentResponse)
async def schedule_content(
    content_id: str,
    body: ContentSchedule,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("editor")),
):
    content = await _get_content(db, content_id)
    content.scheduled_at = body.scheduled_at
    content.status = "scheduled"
    await db.flush()
    return content