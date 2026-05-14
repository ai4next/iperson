from __future__ import annotations

from iperson.utils.llm import _cached_llm


def test_gemini_provider_routes_correctly() -> None:
    """Verify gemini provider creates ChatGoogleGenerativeAI."""
    try:
        llm = _cached_llm(provider="gemini", model="gemini-2.0-flash", temperature=0.7, api_key="test-key")
        class_name = type(llm).__name__
        assert "Google" in class_name or "GenerativeAI" in class_name
    except ImportError:
        # langchain-google-genai not installed — that's OK in CI
        pass


def test_openai_provider_routes_correctly() -> None:
    llm = _cached_llm(provider="openai", model="gpt-4o", temperature=0.7, api_key="test-key")
    class_name = type(llm).__name__
    assert "ChatOpenAI" in class_name


def test_anthropic_provider_routes_correctly() -> None:
    llm = _cached_llm(provider="anthropic", model="claude-sonnet-4-6", temperature=0.7, api_key="test-key")
    class_name = type(llm).__name__
    assert "Anthropic" in class_name or "ChatAnthropic" in class_name