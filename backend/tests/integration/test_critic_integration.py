"""Integration test for :class:`CritiqueEvidenceUseCase` against the real LLM.

Run with:  pytest -m integration
Skip with: pytest -m "not integration"
"""

from __future__ import annotations

from uuid import uuid4
from datetime import datetime, timezone

import pytest

from adapters.llm.openai_compatible_llm import OpenAICompatibleLLM
from application.use_cases.critique_evidence import CritiqueEvidenceUseCase, CritiqueResult
from domain.entities.citation import Citation
from domain.entities.evidence import Evidence, SourceType
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


def test_critique_evidence_with_real_llm(llm_config: LLMConfig) -> None:
    llm = OpenAICompatibleLLM(
        base_url=llm_config.base_url,
        api_key=llm_config.api_key,
        model=llm_config.model,
    )
    uc = CritiqueEvidenceUseCase(llm=llm)

    sq = SubQuestion(
        research_query_id=uuid4(),
        text="What is the capital of France?",
        category=ToolCategory.GENERAL,
    )

    # 1. Provide sufficient evidence
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
        )
    ]
    
    result_satisfied = uc.execute(sq, ev_sufficient)
    
    assert isinstance(result_satisfied, CritiqueResult)
    assert result_satisfied.satisfied is True
    assert result_satisfied.reason
    assert isinstance(result_satisfied.missing_aspects, list)
    
    # 2. Provide insufficient evidence
    ev_insufficient = [
        Evidence(
            sub_question_id=sq.id,
            content="France is a country in Western Europe. It is known for its wine and cheese.",
            source_type=SourceType.DOCUMENTATION,
            citation=Citation(
                source_name="Wikipedia",
                source_url_or_id="https://en.wikipedia.org/wiki/France",
                retrieved_at=datetime(2026, 9, 11, tzinfo=timezone.utc),
            ),
        )
    ]
    
    result_unsatisfied = uc.execute(sq, ev_insufficient)
    
    assert isinstance(result_unsatisfied, CritiqueResult)
    assert result_unsatisfied.satisfied is False
    assert result_unsatisfied.reason
    assert len(result_unsatisfied.missing_aspects) > 0
    assert "capital" in " ".join(result_unsatisfied.missing_aspects).lower()
