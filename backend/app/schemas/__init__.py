"""Pydantic schemas for API request/response validation."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── Auth ───────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)
    tenant_name: str = Field(min_length=1, max_length=100)
    tenant_slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Persona ────────────────────────────────────────────────────────────

class PersonaCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    language: str = Field(default="zh", pattern=r"^(zh|en|ja)$")
    system_prompt: str | None = None
    tone_instruction: str | None = None
    focus_areas: list[str] | None = None
    keywords: list[str] | None = None
    content_types: list[str] | None = None


class PersonaUpdate(BaseModel):
    name: str | None = None
    system_prompt: str | None = None
    tone_instruction: str | None = None
    focus_areas: list[str] | None = None
    keywords: list[str] | None = None
    content_types: list[str] | None = None
    is_active: bool | None = None


class PersonaResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    language: str
    system_prompt: str | None
    tone_instruction: str | None
    focus_areas: list[str] | None
    keywords: list[str] | None
    content_types: list[str] | None
    style_consistency_threshold: float
    is_active: bool
    created_at: datetime
    updated_at: datetime | None


# ── Content ────────────────────────────────────────────────────────────

class ContentCreate(BaseModel):
    persona_id: str
    title: str | None = None
    topic_id: str | None = None


class ContentUpdate(BaseModel):
    final_content: str | None = None
    status: str | None = None


class ContentApprove(BaseModel):
    final_content: str | None = None  # optional final edit before approval


class ContentSchedule(BaseModel):
    scheduled_at: datetime


class ContentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    persona_id: str
    topic_id: str | None
    title: str | None
    draft_content: str | None
    final_content: str | None
    status: str
    quality_score: float | None
    style_consistency: float | None
    scheduled_at: datetime | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime | None


# ── Generic ───────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int = 1
    page_size: int = 20