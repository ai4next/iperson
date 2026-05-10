"""Domain services encapsulate core business logic."""

from app.domain.analytics import AnalyticsService, ContentPerformance, WeeklyReport
from app.domain.knowledge import KnowledgeBaseService, SemanticChunker
from app.domain.persona import PersonaEngine
from app.domain.pipeline import PipelineContext, PipelineOrchestrator, StageProtocol
from app.domain.pipeline.stages import (
    AdaptationStage,
    DiscoveryStage,
    GenerationStage,
    QualityGateStage,
    RankingStage,
)
from app.domain.publish import BasePlatform, DryRunPlatform, PlatformRegistry, PublishResult

__all__ = [
    "AdaptationStage",
    "AnalyticsService",
    "BasePlatform",
    "ContentPerformance",
    "DiscoveryStage",
    "DryRunPlatform",
    "GenerationStage",
    "KnowledgeBaseService",
    "PersonaEngine",
    "PipelineContext",
    "PipelineOrchestrator",
    "PlatformRegistry",
    "PublishResult",
    "QualityGateStage",
    "RankingStage",
    "SemanticChunker",
    "StageProtocol",
    "WeeklyReport",
]