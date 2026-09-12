"""Integration test for :class:`SemanticScholarGateway` against the real Semantic Scholar Graph API.

This makes a genuine API call, so it is marked ``integration`` and is skipped
whenever the Semantic Scholar API is unreachable. Semantic Scholar public API does not require
an API key, so the skip condition is based on a quick connectivity check.

Run with:  pytest -m integration
Skip with: pytest -m "not integration"
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

from adapters.gateways.semantic_scholar_gateway import SemanticScholarGateway
from domain.entities.evidence import Evidence, SourceType
from domain.entities.sub_question import SubQuestion
from domain.value_objects.tool_category import ToolCategory

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def semantic_scholar_gateway() -> SemanticScholarGateway:
    """Build a real Semantic Scholar gateway; skip if the API is unreachable."""
    import httpx

    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "").strip() or None

    try:
        # Quick connectivity probe
        headers = {}
        if api_key:
            headers["x-api-key"] = api_key
            
        httpx.get(
            "https://api.semanticscholar.org/graph/v1/paper/search?query=test&limit=1",
            headers=headers,
            timeout=10,
        ).raise_for_status()
    except Exception as exc:
        pytest.skip(f"Semantic Scholar API not reachable: {exc}")

    return SemanticScholarGateway(api_key=api_key, max_results=3, timeout_seconds=15)


def test_search_returns_evidence_with_citations(
    semantic_scholar_gateway: SemanticScholarGateway,
) -> None:
    sub_question = SubQuestion(
        research_query_id=uuid4(),
        text="transformers attention mechanism",
        category=ToolCategory.ACADEMIC,
    )

    evidence = semantic_scholar_gateway.search(sub_question)

    assert evidence, "Semantic Scholar returned no usable results for an academic query"
    for item in evidence:
        assert isinstance(item, Evidence)
        assert item.source_type is SourceType.DOCUMENTATION
        assert item.sub_question_id == sub_question.id
        assert item.content.strip()
        assert item.citation.source_url_or_id.startswith("http")
        assert item.citation.source_name == "Semantic Scholar"
        assert item.citation.retrieved_at.tzinfo is not None
