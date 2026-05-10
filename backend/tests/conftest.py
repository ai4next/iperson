"""Test configuration — shared fixtures for all test modules."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
)
from app.domain.pipeline import PipelineContext, PipelineOrchestrator
from app.domain.pipeline.stages import (
    GenerationStage,
    QualityGateStage,
    RankingStage,
    _get_llm,
)
from app.domain.persona import PersonaEngine
from app.domain.publish import DryRunPlatform, PlatformRegistry
from app.models.base import Base

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """In-memory SQLite session for testing."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def sample_persona_dict() -> dict[str, Any]:
    return {
        "id": "test-persona-001",
        "tenant_id": "test-tenant-001",
        "name": "Test Tech Analyst",
        "language": "zh",
        "system_prompt": "You are a sharp tech analyst writing in Chinese.",
        "tone_instruction": "Be insightful but concise.",
        "focus_areas": ["AI", "tech trends"],
        "keywords": ["machine learning", "AI"],
        "content_types": ["social_post"],
        "style_consistency_threshold": 0.65,
        "is_active": True,
    }


@pytest.fixture
def sample_topic() -> dict[str, Any]:
    return {
        "title": "GPT-5 breaks new records in reasoning benchmarks",
        "summary": "OpenAI's latest model shows unprecedented performance...",
        "source": "hackernews",
        "url": "https://example.com/gpt5",
        "heat_score": 0.95,
    }


@pytest.fixture
def pipeline_ctx(sample_topic: dict[str, Any]) -> PipelineContext:
    return PipelineContext(
        tenant_id="test-tenant-001",
        persona_id="test-persona-001",
        content_id="test-content-001",
        topics=[sample_topic],
        selected_topic=sample_topic,
    )


@pytest.fixture
def dry_run_platform() -> DryRunPlatform:
    return DryRunPlatform()