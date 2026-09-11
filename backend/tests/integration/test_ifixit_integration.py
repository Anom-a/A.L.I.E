"""Integration test for :class:`IFixitGateway` against the real iFixit API.

This makes a genuine API call, so it is marked ``integration`` and is skipped
whenever the iFixit API is unreachable.  The iFixit public API does not require
an API key, so the skip condition is based on a quick connectivity check.

Run with:  pytest -m integration
Skip with: pytest -m "not integration"
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from adapters.gateways.ifixit_gateway import IFixitGateway
from domain.entities.evidence import Evidence, SourceType
from domain.entities.sub_question import SubQuestion
from domain.value_objects.tool_category import ToolCategory

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def ifixit_gateway() -> IFixitGateway:
    """Build a real iFixit gateway; skip if the API is unreachable."""
    import httpx

    try:
        # Quick connectivity probe — no full search.
        httpx.get(
            "https://www.ifixit.com/api/2.0/search/test?limit=1",
            timeout=10,
        ).raise_for_status()
    except Exception as exc:
        pytest.skip(f"iFixit API not reachable: {exc}")

    return IFixitGateway(max_results=3, timeout_seconds=15)


def test_search_returns_evidence_with_citations(
    ifixit_gateway: IFixitGateway,
) -> None:
    sub_question = SubQuestion(
        research_query_id=uuid4(),
        text="iPhone battery replacement",
        category=ToolCategory.REPAIR,
    )

    evidence = ifixit_gateway.search(sub_question)

    assert evidence, "iFixit returned no usable results for a repair query"
    for item in evidence:
        assert isinstance(item, Evidence)
        assert item.source_type is SourceType.DOCUMENTATION
        assert item.sub_question_id == sub_question.id
        assert item.content.strip()
        assert item.citation.source_url_or_id.startswith("http")
        assert item.citation.source_name.strip()
        assert item.citation.retrieved_at.tzinfo is not None
