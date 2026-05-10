"""Platform account management and publish queue endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import get_current_tenant_id
from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.platform_account import PlatformAccount
from app.models.user import User

router = APIRouter(prefix="/publish", tags=["publish"])


@router.get("/accounts")
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tid = get_current_tenant_id()
    result = await db.execute(
        select(PlatformAccount).where(PlatformAccount.tenant_id == tid)
    )
    accounts = result.scalars().all()
    return [
        {
            "id": a.id,
            "platform": a.platform,
            "account_name": a.account_name,
            "is_active": a.is_active,
        }
        for a in accounts
    ]


@router.post("/accounts", status_code=status.HTTP_201_CREATED)
async def create_account(
    platform: str,
    account_name: str,
    access_token: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    tid = get_current_tenant_id()

    # Check if account already exists for this platform
    result = await db.execute(
        select(PlatformAccount).where(
            PlatformAccount.tenant_id == tid,
            PlatformAccount.platform == platform,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Account already exists for {platform}")

    account = PlatformAccount(
        tenant_id=tid,
        platform=platform,
        account_name=account_name,
        access_token=access_token,
    )
    db.add(account)
    await db.flush()
    return {"id": account.id, "platform": account.platform, "account_name": account.account_name}


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    tid = get_current_tenant_id()
    result = await db.execute(
        select(PlatformAccount).where(PlatformAccount.id == account_id, PlatformAccount.tenant_id == tid)
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    await db.delete(account)
    await db.flush()


@router.get("/queue")
async def get_publish_queue(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List pending publications in the queue."""
    from app.models.content import Content
    from app.models.publication import Publication

    tid = get_current_tenant_id()
    # Simple join without ORM relationship — use implicit join condition
    result = await db.execute(
        select(Publication)
        .join(Content, Publication.content_id == Content.id)
        .where(Content.tenant_id == tid, Publication.status == "pending")
        .order_by(Publication.published_at.desc().nullslast())
        .limit(50)
    )
    pubs = result.scalars().all()
    return {
        "queue": [
            {
                "id": p.id,
                "content_id": p.content_id,
                "platform": p.platform,
                "status": p.status,
                "published_at": str(p.published_at) if p.published_at else None,
            }
            for p in pubs
        ],
        "total": len(pubs),
    }