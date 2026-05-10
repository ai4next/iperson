"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── tenants ─────────────────────────────────────────────────────
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("plan_tier", sa.String(50), server_default="free"),
        sa.Column("settings", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # ── users ───────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("tenant_id", sa.String(32), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("role", sa.String(20), server_default="editor"),
        sa.Column("avatar_url", sa.String(2048), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("oauth_provider", sa.String(50), nullable=True),
        sa.Column("oauth_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # ── personas ────────────────────────────────────────────────────
    op.create_table(
        "personas",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("tenant_id", sa.String(32), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("language", sa.String(10), server_default="zh"),
        sa.Column("system_prompt", sa.Text, nullable=True),
        sa.Column("tone_instruction", sa.Text, nullable=True),
        sa.Column("style_profile", sa.JSON, nullable=True),
        sa.Column("few_shot_examples", sa.JSON, nullable=True),
        sa.Column("banned_patterns", sa.JSON, nullable=True),
        sa.Column("visual_theme", sa.JSON, nullable=True),
        sa.Column("focus_areas", sa.JSON, nullable=True),
        sa.Column("keywords", sa.JSON, nullable=True),
        sa.Column("content_types", sa.JSON, nullable=True),
        sa.Column("style_consistency_threshold", sa.Float, server_default="0.65"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # ── topics (discovery pool) ─────────────────────────────────────
    op.create_table(
        "topics",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("tenant_id", sa.String(32), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("source", sa.String(100), nullable=False, index=True),
        sa.Column("source_id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("url", sa.Text, nullable=True),
        sa.Column("heat_score", sa.Float, nullable=True),
        sa.Column("ai_rank_score", sa.Float, nullable=True),
        sa.Column("metadata_", sa.String(2048), nullable=True),
        sa.Column("title_hash", sa.String(64), nullable=True, index=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.UniqueConstraint("source", "source_id", name="uq_topic_source"),
    )

    # ── contents ────────────────────────────────────────────────────
    op.create_table(
        "contents",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("tenant_id", sa.String(32), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("persona_id", sa.String(32), sa.ForeignKey("personas.id"), nullable=False, index=True),
        sa.Column("topic_id", sa.String(32), sa.ForeignKey("topics.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("draft_content", sa.Text, nullable=True),
        sa.Column("final_content", sa.Text, nullable=True),
        sa.Column("prompt_version", sa.String(50), nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("generation_tokens", sa.Integer, nullable=True),
        sa.Column("status", sa.String(30), server_default="draft", index=True),
        sa.Column("quality_score", sa.Float, nullable=True),
        sa.Column("style_consistency", sa.Float, nullable=True),
        sa.Column("quality_issues", sa.String(2048), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # ── publications ────────────────────────────────────────────────
    op.create_table(
        "publications",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("content_id", sa.String(32), sa.ForeignKey("contents.id"), nullable=False, index=True),
        sa.Column("platform", sa.String(50), nullable=False, index=True),
        sa.Column("platform_post_id", sa.String(255), nullable=True),
        sa.Column("platform_url", sa.Text, nullable=True),
        sa.Column("status", sa.String(30), server_default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("publish_metadata", sa.String(2048), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── content_versions ─────────────────────────────────────────────
    op.create_table(
        "content_versions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("content_id", sa.String(32), sa.ForeignKey("contents.id"), nullable=False, index=True),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("content_text", sa.Text, nullable=True),
        sa.Column("status", sa.String(30), nullable=True),
        sa.Column("changed_by", sa.String(100), nullable=True),
        sa.Column("change_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── metrics ─────────────────────────────────────────────────────
    op.create_table(
        "metrics",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("publication_id", sa.String(32), sa.ForeignKey("publications.id"), nullable=False, index=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("likes", sa.Integer, server_default="0"),
        sa.Column("comments", sa.Integer, server_default="0"),
        sa.Column("shares", sa.Integer, server_default="0"),
        sa.Column("saves", sa.Integer, server_default="0"),
        sa.Column("views", sa.Integer, server_default="0"),
        sa.Column("clicks", sa.Integer, server_default="0"),
        sa.Column("followers_gained", sa.Integer, server_default="0"),
        sa.Column("raw_data", sa.String(4096), nullable=True),
    )

    # ── knowledge_docs ──────────────────────────────────────────────
    op.create_table(
        "knowledge_docs",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("tenant_id", sa.String(32), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("persona_id", sa.String(32), sa.ForeignKey("personas.id"), nullable=True, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("source_type", sa.String(50), server_default="upload"),
        sa.Column("source_url", sa.Text, nullable=True),
        sa.Column("content_text", sa.Text, nullable=True),
        sa.Column("file_path", sa.Text, nullable=True),
        sa.Column("metadata_", sa.String(2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── knowledge_chunks ────────────────────────────────────────────
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("tenant_id", sa.String(32), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("doc_id", sa.String(32), sa.ForeignKey("knowledge_docs.id"), nullable=False, index=True),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("metadata_", sa.String(2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── platform_accounts ───────────────────────────────────────────
    op.create_table(
        "platform_accounts",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("tenant_id", sa.String(32), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("platform", sa.String(50), nullable=False, index=True),
        sa.Column("account_name", sa.String(255), nullable=True),
        sa.Column("account_id", sa.String(255), nullable=True),
        sa.Column("access_token", sa.Text, nullable=True),
        sa.Column("refresh_token", sa.Text, nullable=True),
        sa.Column("token_expires_at", sa.String(50), nullable=True),
        sa.Column("extra_config", sa.JSON, nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "platform", name="uq_tenant_platform"),
    )

    # ── pipeline_runs ───────────────────────────────────────────────
    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("tenant_id", sa.String(32), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("persona_id", sa.String(32), sa.ForeignKey("personas.id"), nullable=True),
        sa.Column("content_id", sa.String(32), sa.ForeignKey("contents.id"), nullable=True),
        sa.Column("status", sa.String(30), server_default="running"),
        sa.Column("stages_completed", sa.String(4096), nullable=True),
        sa.Column("errors", sa.String(4096), nullable=True),
        sa.Column("context_snapshot", sa.String(8192), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── prompts ─────────────────────────────────────────────────────
    op.create_table(
        "prompts",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("persona_id", sa.String(32), sa.ForeignKey("personas.id"), nullable=False, index=True),
        sa.Column("task_type", sa.String(50), nullable=False, index=True),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("system_template", sa.Text, nullable=True),
        sa.Column("user_template", sa.Text, nullable=True),
        sa.Column("variables", sa.String(1024), nullable=True),
        sa.Column("model_config", sa.String(1024), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("performance_score", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("persona_id", "task_type", "version", name="uq_prompt_version"),
    )

    # ── subscriptions ───────────────────────────────────────────────
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("tenant_id", sa.String(32), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("plan_tier", sa.String(50), server_default="free"),
        sa.Column("status", sa.String(20), server_default="trialing"),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payment_provider", sa.String(50), nullable=True),
        sa.Column("provider_subscription_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.UniqueConstraint("tenant_id", name="uq_tenant_subscription"),
    )


def downgrade() -> None:
    op.drop_table("subscriptions")
    op.drop_table("prompts")
    op.drop_table("pipeline_runs")
    op.drop_table("platform_accounts")
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_docs")
    op.drop_table("metrics")
    op.drop_table("content_versions")
    op.drop_table("publications")
    op.drop_table("contents")
    op.drop_table("topics")
    op.drop_table("personas")
    op.drop_table("users")
    op.drop_table("tenants")