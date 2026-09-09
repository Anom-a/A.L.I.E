"""Integration test for :class:`OpenAICompatibleLLM` against a real endpoint.

This makes a genuine, billable API call, so it is marked ``integration`` and is
skipped whenever ``OPENAI_API_KEY`` / ``OPENAI_MODEL_PLANNER`` are absent. A
missing credential must never fail the suite.

Run with:  pytest -m integration
Skip with: pytest -m "not integration"
"""

from __future__ import annotations

import pytest

from adapters.llm.openai_compatible_llm import OpenAICompatibleLLM
from infrastructure.config import (
    ConfigError,
    LLMConfig,
    load_env_file,
    load_llm_config,
)

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def llm_config() -> LLMConfig:
    """Real LLM configuration, or skip the module if it is not available."""
    load_env_file()
    try:
        return load_llm_config()
    except ConfigError as exc:
        pytest.skip(f"LLM credentials not configured: {exc}")


def test_completion_returns_non_empty_text(llm_config: LLMConfig) -> None:
    # One tiny, deterministic prompt: enough to prove the wiring works without
    # spending real money on a research-sized request.
    llm = OpenAICompatibleLLM(
        api_key=llm_config.api_key,
        model=llm_config.model,
        base_url=llm_config.base_url,
        timeout_seconds=llm_config.timeout_seconds,
    )

    answer = llm.complete("Reply with exactly one word: pong")

    assert isinstance(answer, str)
    assert answer.strip(), "the provider returned an empty completion"
