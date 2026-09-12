"""Integration test for :class:`NewsApiGateway` against the real NewsAPI.ai.

This makes a genuine API call, so it is marked ``integration`` and is skipped
if no API key is provided in the environment.

Run with:  pytest -m integration
Skip with: pytest -m "not integration"
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

from adapters.gateways.news_api_gateway import NewsApiGateway
from domain.entities.evidence import Evidence, SourceType
from domain.entities.sub_question import SubQuestion
from domain.value_objects.tool_category import ToolCategory

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def news_api_gateway() -> NewsApiGateway:
    """Build a real NewsAPI gateway; skip if the API key is missing or API is unreachable."""
    api_key = os.environ.get("NEWS_API_KEY", "").strip()
    if not api_key or api_key == "your-news-api-key-here":
        pytest.skip("NEWS_API_KEY is not set or is the default placeholder")

    import httpx

    try:
        # Quick connectivity probe
        httpx.get(
            "https://newsapi.org/v2/everything?q=test&pageSize=1",
            headers={"X-Api-Key": api_key},
            timeout=10,
        ).raise_for_status()
    except Exception as exc:
        pytest.skip(f"NewsAPI not reachable or key rejected: {exc}")

    return NewsApiGateway(api_key=api_key, max_results=3, timeout_seconds=15)


def test_search_returns_evidence_with_citations(
    news_api_gateway: NewsApiGateway,
) -> None:
    sub_question = SubQuestion(
        research_query_id=uuid4(),
        text="artificial intelligence latest news",
        category=ToolCategory.NEWS,
    )

    evidence = news_api_gateway.search(sub_question)

    assert evidence, "NewsAPI returned no usable results for a news query"
    for item in evidence:
        assert isinstance(item, Evidence)
        assert item.source_type is SourceType.DOCUMENTATION
        assert item.sub_question_id == sub_question.id
        assert item.content.strip()
        assert item.citation.source_url_or_id.startswith("http")
        assert item.citation.source_name.strip()
        assert item.citation.retrieved_at.tzinfo is not None
