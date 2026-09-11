"""Integration test for SynthesizeReportUseCase against a real LLM.

Run with:  pytest -m integration
Skip with: pytest -m "not integration"
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from adapters.llm.openai_compatible_llm import OpenAICompatibleLLM
from application.use_cases.synthesize_report import SynthesizeReportUseCase
from domain.entities.citation import Citation
from domain.entities.evidence import Evidence, SourceType
from domain.entities.research_query import ResearchQuery
from domain.entities.sub_question import SubQuestion
from domain.value_objects.tool_category import ToolCategory
from infrastructure.config import ConfigError, LLMConfig, load_env_file, load_llm_config

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def llm_config() -> LLMConfig:
    """Real LLM configuration, or skip the module if it is not available."""
    load_env_file()
    try:
        return load_llm_config()
    except ConfigError as exc:
        pytest.skip(f"LLM credentials not configured: {exc}")


def test_synthesize_report_with_real_llm(llm_config: LLMConfig) -> None:
    llm = OpenAICompatibleLLM(
        base_url=llm_config.base_url,
        api_key=llm_config.api_key,
        model=llm_config.model,
    )
    uc = SynthesizeReportUseCase(llm=llm)

    rq = ResearchQuery(topic="What is the capital of France?")
    sq = SubQuestion(
        research_query_id=rq.id,
        text="What is the capital city?",
        category=ToolCategory.GENERAL,
    )
    
    ev_sufficient = [
        Evidence(
            sub_question_id=sq.id,
            content="Paris is the capital and most populous city of France.",
            source_type=SourceType.DOCUMENTATION,
            citation=Citation(
                source_name="Wikipedia",
                source_url_or_id="https://en.wikipedia.org/wiki/Paris",
                retrieved_at=datetime(2026, 9, 11, tzinfo=timezone.utc),
            ),
        ),
        Evidence(
            sub_question_id=sq.id,
            content="The city is a major railway, highway, and air-transport hub.",
            source_type=SourceType.DOCUMENTATION,
            citation=Citation(
                source_name="Wikipedia (Transport)",
                source_url_or_id="https://en.wikipedia.org/wiki/Paris#Transport",
                retrieved_at=datetime(2026, 9, 11, tzinfo=timezone.utc),
            ),
        )
    ]
    
    report = uc.execute(rq, [sq], ev_sufficient)
    
    assert report.query_id == rq.id
    assert len(report.sections) >= 1
    assert len(report.citations) >= 1
    
    # Check citation integrity (guaranteed by Report domain but let's double check it mapped right)
    known_ids = {c.source_url_or_id for c in report.citations}
    for sec in report.sections:
        assert sec.title
        assert sec.content
        for cid in sec.citation_ids:
            assert cid in known_ids
