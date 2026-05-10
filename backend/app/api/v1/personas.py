"""Persona CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import get_current_tenant_id
from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.persona import Persona
from app.models.user import User
from app.schemas import PersonaCreate, PersonaResponse, PersonaUpdate

router = APIRouter(prefix="/personas", tags=["personas"])


@router.get("/", response_model=list[PersonaResponse])
async def list_personas(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tid = get_current_tenant_id()
    result = await db.execute(
        select(Persona).where(Persona.tenant_id == tid).order_by(Persona.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=PersonaResponse, status_code=status.HTTP_201_CREATED)
async def create_persona(
    body: PersonaCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    tid = get_current_tenant_id()
    persona = Persona(
        tenant_id=tid,
        name=body.name,
        language=body.language,
        system_prompt=body.system_prompt,
        tone_instruction=body.tone_instruction,
        focus_areas=body.focus_areas,
        keywords=body.keywords,
        content_types=body.content_types,
    )
    db.add(persona)
    await db.flush()
    return persona


@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(
    persona_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tid = get_current_tenant_id()
    result = await db.execute(
        select(Persona).where(Persona.id == persona_id, Persona.tenant_id == tid)
    )
    persona = result.scalar_one_or_none()
    if persona is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")
    return persona


@router.patch("/{persona_id}", response_model=PersonaResponse)
async def update_persona(
    persona_id: str,
    body: PersonaUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("editor")),
):
    tid = get_current_tenant_id()
    result = await db.execute(
        select(Persona).where(Persona.id == persona_id, Persona.tenant_id == tid)
    )
    persona = result.scalar_one_or_none()
    if persona is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(persona, key, value)
    await db.flush()
    return persona


@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_persona(
    persona_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    tid = get_current_tenant_id()
    result = await db.execute(
        select(Persona).where(Persona.id == persona_id, Persona.tenant_id == tid)
    )
    persona = result.scalar_one_or_none()
    if persona is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")
    await db.delete(persona)
    await db.flush()