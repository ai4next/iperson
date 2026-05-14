from __future__ import annotations

from pathlib import Path

import pytest

from iperson.config import DEFAULT_CONFIG
from iperson.utils.llm import DummyLLM


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory for testing."""
    data_dir = tmp_path / ".iperson" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def sample_kb_text() -> str:
    """Sample knowledge base text for testing."""
    return """# Introduction to Python

Python is a high-level, interpreted programming language known for its readability and versatility.

## Key Features

1. Dynamic typing
2. Automatic memory management
3. Extensive standard library

## Use Cases

Python is widely used in web development, data science, artificial intelligence, and automation.
"""


@pytest.fixture
def sample_persona_yaml() -> str:
    """Sample persona YAML configuration for testing."""
    return """name: tech-blogger
persona_type: writer
config:
  tone: professional
  expertise_level: advanced
  preferred_topics:
    - python
    - machine-learning
    - system-design
  writing_style: analytical
"""


@pytest.fixture
def sample_recipe_yaml() -> str:
    """Sample recipe YAML configuration for testing."""
    return """name: generate-blog-post
description: Generate a blog post from knowledge base content
steps:
  - name: retrieve-context
    type: kb_search
    params:
      query: "{topic}"
      top_k: 5

  - name: generate-draft
    type: llm_generate
    params:
      prompt_template: "Write a blog post about {topic} based on the context."
      model: gpt-4o
"""


@pytest.fixture
def dummy_llm() -> DummyLLM:
    """Fixture providing a DummyLLM instance."""
    return DummyLLM()


@pytest.fixture
def content_id() -> str:
    """Fixture providing a deterministic content ID."""
    return "test-content-001"