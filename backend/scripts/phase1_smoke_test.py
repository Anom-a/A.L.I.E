#!/usr/bin/env python3
"""Phase 1 smoke test: prove both adapters can reach their real providers.

Loads configuration, builds the two Phase 1 adapters, makes exactly one call
through each, and prints a compact summary:

    LLM: OK
    Tavily: OK
    Phase 1 smoke test: PASSED

This is a connectivity check, not a research workflow: there is no planning,
routing, or synthesis here. Exits 0 on success, 1 on failure.

Usage (from the backend/ directory):  python scripts/phase1_smoke_test.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

# Allow running this file directly from the backend/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adapters.gateways.tavily_gateway import (  # noqa: E402
    SearchGatewayError,
    TavilyGateway,
)
from adapters.llm.openai_compatible_llm import (  # noqa: E402
    LLMAdapterError,
    OpenAICompatibleLLM,
)
from domain.entities.sub_question import SubQuestion  # noqa: E402
from domain.value_objects.tool_category import ToolCategory  # noqa: E402
from infrastructure.config import (  # noqa: E402
    AppConfig,
    ConfigError,
    load_config,
    load_env_file,
)

PROMPT = "Reply with exactly one word: pong"
QUERY = "What is the capital of France?"


def _check_llm(config: AppConfig) -> tuple[bool, str]:
    """Make one LLM call; return (ok, detail)."""
    try:
        llm = OpenAICompatibleLLM(
            api_key=config.llm.api_key,
            model=config.llm.model,
            base_url=config.llm.base_url,
            timeout_seconds=config.llm.timeout_seconds,
        )
        answer = llm.complete(PROMPT)
    except LLMAdapterError as exc:
        return False, str(exc)
    return True, f"model={config.llm.model}, {len(answer)} chars returned"


def _check_tavily(config: AppConfig) -> tuple[bool, str]:
    """Make one search call; return (ok, detail)."""
    try:
        gateway = TavilyGateway(
            api_key=config.search.api_key,
            max_results=3,
            timeout_seconds=config.search.timeout_seconds,
        )
        evidence = gateway.search(
            SubQuestion(
                research_query_id=uuid4(),
                text=QUERY,
                category=ToolCategory.GENERAL,
            )
        )
    except SearchGatewayError as exc:
        return False, str(exc)
    if not evidence:
        return False, "search succeeded but produced no evidence"
    return True, f"{len(evidence)} evidence item(s), first source: {evidence[0].citation.source_name}"


def main() -> int:
    load_env_file()
    try:
        config = load_config()
    except ConfigError as exc:
        print(f"Config: FAILED ({exc})")
        print("Phase 1 smoke test: FAILED")
        return 1

    print("Config: OK")
    results = []
    for label, check in (("LLM", _check_llm), ("Tavily", _check_tavily)):
        ok, detail = check(config)
        print(f"{label}: {'OK' if ok else 'FAILED'} ({detail})")
        results.append(ok)

    passed = all(results)
    print(f"Phase 1 smoke test: {'PASSED' if passed else 'FAILED'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
