from __future__ import annotations

import json
from pathlib import Path

import pytest

from iperson import __version__
from iperson.config import (
    DEFAULT_CONFIG,
    ensure_data_dirs,
    get_data_dir,
    get_output_dir,
    load_config,
)
from iperson.storage import init_db
from iperson.storage.db import get_connection
from iperson.storage.models import (
    AuditReportRecord,
    ContentRecord,
    KbChunkRecord,
    KbDocRecord,
    PersonaRecord,
    PipelineRunRecord,
    PublicationRecord,
)
from iperson.utils.llm import DummyLLM
from iperson.utils.output import (
    create_output_dir,
    write_article,
    write_audit_report,
    write_platform_content,
    write_publish_package,
)


class TestVersion:
    def test_version(self) -> None:
        assert __version__ == "0.4.0"


class TestConfig:
    def test_default_config_structure(self) -> None:
        assert "data_dir" in DEFAULT_CONFIG
        assert "output_dir" in DEFAULT_CONFIG
        assert "llm" in DEFAULT_CONFIG
        assert "db" in DEFAULT_CONFIG

    def test_load_config_defaults(self) -> None:
        config = load_config()
        assert "data_dir" in config
        assert "output_dir" in config
        assert "llm" in config
        assert "db" in config

    def test_get_data_dir(self) -> None:
        data_dir = get_data_dir()
        assert isinstance(data_dir, Path)

    def test_get_output_dir(self) -> None:
        output_dir = get_output_dir()
        assert isinstance(output_dir, Path)

    def test_ensure_data_dirs_creates_directories(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "test_data"
        output_dir = tmp_path / "test_output"
        # The function uses load_config internally, so we need to set env vars
        import os
        os.environ["IPERSON_DATA_DIR"] = str(data_dir)
        os.environ["IPERSON_OUTPUT_DIR"] = str(output_dir)
        try:
            ensure_data_dirs()
            assert data_dir.exists()
            assert output_dir.exists()
        finally:
            del os.environ["IPERSON_DATA_DIR"]
            del os.environ["IPERSON_OUTPUT_DIR"]


class TestStorage:
    def test_init_db_creates_tables(self, tmp_path: Path) -> None:
        import os
        db_path = tmp_path / "test.db"
        os.environ["IPERSON_DB_PATH"] = str(db_path)
        try:
            init_db()

            conn = get_connection()
            try:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                tables = [row["name"] for row in cursor.fetchall()]
                expected = [
                    "audit_reports",
                    "contents",
                    "kb_chunks",
                    "kb_docs",
                    "personas",
                    "pipeline_runs",
                    "publications",
                ]
                for t in expected:
                    assert t in tables, f"Missing table: {t}"
            finally:
                conn.close()
        finally:
            del os.environ["IPERSON_DB_PATH"]

    def test_init_db_idempotent(self, tmp_path: Path) -> None:
        import os
        db_path = tmp_path / "test_idempotent.db"
        os.environ["IPERSON_DB_PATH"] = str(db_path)
        try:
            init_db()
            init_db()  # Should be safe
        finally:
            del os.environ["IPERSON_DB_PATH"]

    def test_content_record_model(self) -> None:
        record = ContentRecord(
            id="test-1",
            topic="Python",
            title="Test Content",
            content_type="article",
            draft_content="Hello world",
        )
        assert record.id == "test-1"
        assert record.title == "Test Content"
        assert record.content_type == "article"
        assert record.draft_content == "Hello world"
        assert record.metadata == {}

    def test_persona_record_model(self) -> None:
        record = PersonaRecord(
            id="persona-1",
            name="Tech Blogger",
            persona_type="writer",
            config={"tone": "professional"},
        )
        assert record.name == "Tech Blogger"
        assert record.config["tone"] == "professional"

    def test_publication_record_model(self) -> None:
        record = PublicationRecord(
            id="pub-1",
            content_id="content-1",
            platform="wechat",
            status="published",
        )
        assert record.platform == "wechat"
        assert record.status == "published"

    def test_kb_doc_record_model(self) -> None:
        record = KbDocRecord(
            id="doc-1",
            title="Python Guide",
            content="# Python",
        )
        assert record.title == "Python Guide"
        assert record.source == ""

    def test_kb_chunk_record_model(self) -> None:
        record = KbChunkRecord(
            id="chunk-1",
            kb_doc_id="doc-1",
            chunk_index=0,
            content="Python is great",
        )
        assert record.chunk_index == 0
        assert record.embedding is None

    def test_audit_report_record_model(self) -> None:
        record = AuditReportRecord(
            id="report-1",
            report_type="quality",
            content="All checks passed",
        )
        assert record.report_type == "quality"

    def test_pipeline_run_record_model(self) -> None:
        record = PipelineRunRecord(
            id="run-1",
            pipeline_name="generate-blog",
            status="running",
        )
        assert record.pipeline_name == "generate-blog"
        assert record.status == "running"


class TestDummyLLM:
    @pytest.mark.asyncio
    async def test_generate_returns_deterministic_response(self, dummy_llm: DummyLLM) -> None:
        from langchain_core.messages import HumanMessage

        result1 = await dummy_llm.ainvoke([HumanMessage(content="Hello")])
        result2 = await dummy_llm.ainvoke([HumanMessage(content="Hello")])
        assert result1.content == result2.content
        assert "Dummy response" in result1.content

    @pytest.mark.asyncio
    async def test_generate_different_prompts_different_responses(self, dummy_llm: DummyLLM) -> None:
        from langchain_core.messages import HumanMessage

        result1 = await dummy_llm.ainvoke([HumanMessage(content="Hello")])
        result2 = await dummy_llm.ainvoke([HumanMessage(content="World")])
        assert result1.content != result2.content

    @pytest.mark.asyncio
    async def test_generate_embedding_returns_1536_dims(self) -> None:
        from iperson.utils.llm import DummyEmbeddings

        emb = DummyEmbeddings()
        result = await emb.aembed_query("test text")
        assert len(result) == 1536

    @pytest.mark.asyncio
    async def test_generate_embedding_deterministic(self) -> None:
        from iperson.utils.llm import DummyEmbeddings

        emb = DummyEmbeddings()
        emb1 = await emb.aembed_query("test text")
        emb2 = await emb.aembed_query("test text")
        assert emb1 == emb2

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self) -> None:
        from iperson.utils.llm import DummyEmbeddings

        emb = DummyEmbeddings()
        result = await emb.aembed_query("")
        assert all(v == 0.0 for v in result)

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self) -> None:
        from iperson.utils.llm import DummyEmbeddings

        emb = DummyEmbeddings()
        texts = ["hello", "world", "test"]
        embs = await emb.aembed_documents(texts)
        assert len(embs) == 3
        assert all(len(e) == 1536 for e in embs)
        assert embs[0] == await emb.aembed_query("hello")


class TestOutput:
    def test_create_output_dir(self, tmp_path: Path) -> None:
        import os
        os.environ["IPERSON_OUTPUT_DIR"] = str(tmp_path / "output")
        try:
            path = create_output_dir("Test Topic")
            assert path.exists()
            assert path.parent == tmp_path / "output"
            assert path.name.endswith("-test-topic")
            # Should contain timestamp prefix (format: YYYYMMDD_HHMMSS)
            parts = path.name.split("-")
            assert parts[0].replace("_", "").isdigit()
        finally:
            del os.environ["IPERSON_OUTPUT_DIR"]

    def test_write_article(self, tmp_path: Path) -> None:
        import os
        os.environ["IPERSON_OUTPUT_DIR"] = str(tmp_path / "output")
        try:
            out_dir = create_output_dir("test-topic")
            path = write_article(out_dir, "# Hello\n\nThis is a test.")
            assert path.exists()
            content = path.read_text(encoding="utf-8")
            assert "# Hello" in content
            assert path.name == "article.md"
        finally:
            del os.environ["IPERSON_OUTPUT_DIR"]

    def test_write_audit_report(self, tmp_path: Path) -> None:
        import os
        os.environ["IPERSON_OUTPUT_DIR"] = str(tmp_path / "output")
        try:
            out_dir = create_output_dir("test-topic")
            report = {"score": 95, "summary": "All good"}
            path = write_audit_report(out_dir, report)
            assert path.exists()
            loaded = json.loads(path.read_text(encoding="utf-8"))
            assert loaded["score"] == 95
            assert loaded["summary"] == "All good"
        finally:
            del os.environ["IPERSON_OUTPUT_DIR"]

    def test_write_publish_package(self, tmp_path: Path) -> None:
        import os
        os.environ["IPERSON_OUTPUT_DIR"] = str(tmp_path / "output")
        try:
            out_dir = create_output_dir("test-topic")
            data = {"title": "Test Post", "content": "# Test", "platform": "wechat"}
            path = write_publish_package(out_dir, data)
            assert path.exists()
            loaded = json.loads(path.read_text(encoding="utf-8"))
            assert loaded["title"] == "Test Post"
        finally:
            del os.environ["IPERSON_OUTPUT_DIR"]

    def test_write_platform_content(self, tmp_path: Path) -> None:
        import os
        os.environ["IPERSON_OUTPUT_DIR"] = str(tmp_path / "output")
        try:
            out_dir = create_output_dir("test-topic")
            path = write_platform_content(out_dir, "wechat", "WeChat post content")
            assert path.exists()
            assert "wechat" in str(path)
            content = path.read_text(encoding="utf-8")
            assert content == "WeChat post content"
        finally:
            del os.environ["IPERSON_OUTPUT_DIR"]


class TestFixtures:
    def test_sample_kb_text(self, sample_kb_text: str) -> None:
        assert "Python" in sample_kb_text
        assert "Key Features" in sample_kb_text

    def test_sample_persona_yaml(self, sample_persona_yaml: str) -> None:
        assert "tech-blogger" in sample_persona_yaml
        assert "writer" in sample_persona_yaml

    def test_sample_recipe_yaml(self, sample_recipe_yaml: str) -> None:
        assert "generate-blog-post" in sample_recipe_yaml
        assert "kb_search" in sample_recipe_yaml

    def test_content_id_fixture(self, content_id: str) -> None:
        assert content_id == "test-content-001"