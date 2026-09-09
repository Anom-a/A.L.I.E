"""Integration test for the planner against a real LLM endpoint.

This wires the Phase 1 adapter into the Phase 2 use case and makes a genuine,
billable API call, so it is marked ``integration`` and skips itself whenever
``OPENAI_API_KEY`` / ``OPENAI_MODEL_PLANNER`` are absent. A missing credential
must never fail the suite.

Run with:  pytest -m integration
Skip with: pytest -m "not integration"
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from adapters.llm.openai_compatible_llm import OpenAICompatibleLLM
from application.use_cases.plan_sub_questions import PlanSubQuestionsUseCase
from domain.entities.sub_question import SubQuestion, SubQuestionStatus
from domain.value_objects.tool_category import ToolCategory
from infrastructure.config import (
    ConfigError,
    LLMConfig,
    PlannerConfig,
    load_env_file,
    load_llm_config,
    load_planner_config,
)

pytestmark = pytest.mark.integration

TOPIC = "How does containerization affect backend deployment?"


@pytest.fixture(scope="module")
def llm_config() -> LLMConfig:
    """Real LLM configuration, or skip the module if it is not available."""
    load_env_file()
    try:
        return load_llm_config()
    except ConfigError as exc:
        pytest.skip(f"LLM credentials not configured: {exc}")


@pytest.fixture(scope="module")
def planner_config() -> PlannerConfig:
    """The configured bound; falls back to the built-in default."""
    load_env_file()
    return load_planner_config()


def test_planner_decomposes_a_real_topic(
    llm_config: LLMConfig, planner_config: PlannerConfig
) -> None:
    # The composition happens here, outside the use case: it is handed a port.
    llm = OpenAICompatibleLLM(
        api_key=llm_config.api_key,
        model=llm_config.model,
        base_url=llm_config.base_url,
        timeout_seconds=llm_config.timeout_seconds,
    )
    use_case = PlanSubQuestionsUseCase(
        llm=llm,
        max_subquestions=planner_config.max_subquestions,
    )
    research_query_id = uuid4()

    sub_questions = use_case.execute(
        topic=TOPIC, research_query_id=research_query_id
    )

    assert sub_questions, "the planner returned no sub-questions"
    assert len(sub_questions) <= planner_config.max_subquestions
    for sub_question in sub_questions:
        assert isinstance(sub_question, SubQuestion)
        assert sub_question.text.strip()
        assert sub_question.research_query_id == research_query_id
        assert sub_question.category is ToolCategory.GENERAL
        assert sub_question.status is SubQuestionStatus.PENDING
