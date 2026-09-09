"""Integration test for :class:`TavilyGateway` against the real Tavily API.

This makes a genuine, quota-consuming API call, so it is marked ``integration``
and is skipped whenever ``TAVILY_API_KEY`` is absent. A missing credential must
never fail the suite.

Run with:  pytest -m integration
Skip with: pytest -m "not integration"
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from adapters.gateways.tavily_gateway import TavilyGateway
from domain.entities.evidence import Evidence, SourceType
from domain.entities.sub_question import SubQuestion
from domain.value_objects.tool_category import ToolCategory
from infrastructure.config import (
    ConfigError,
    SearchConfig,
    load_env_file,
    load_search_config,
)

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def search_config() -> SearchConfig:
    """Real search configuration, or skip the module if it is not available."""
    load_env_file()
    try:
        return load_search_config()
    except ConfigError as exc:
        pytest.skip(f"Tavily credentials not configured: {exc}")


def test_search_returns_evidence_with_citations(search_config: SearchConfig) -> None:
    # One small factual query with few results: enough to prove the translation
    # boundary works end to end without a research-sized request.
    gateway = TavilyGateway(
        api_key=search_config.api_key,
        max_results=3,
        timeout_seconds=search_config.timeout_seconds,
    )
    sub_question = SubQuestion(
        research_query_id=uuid4(),
        text="What is the capital of France?",
        category=ToolCategory.GENERAL,
    )

    evidence = gateway.search(sub_question)

    assert evidence, "Tavily returned no usable results for a simple factual query"
    for item in evidence:
        # Only domain objects come back: the Tavily payload stayed in the adapter.
        assert isinstance(item, Evidence)
        assert item.source_type is SourceType.WEB
        assert item.sub_question_id == sub_question.id
        assert item.content.strip()
        # URL, name and retrieval time survived the conversion into a Citation.
        assert item.citation.source_url_or_id.startswith("http")
        assert item.citation.source_name.strip()
        assert item.citation.retrieved_at.tzinfo is not None
