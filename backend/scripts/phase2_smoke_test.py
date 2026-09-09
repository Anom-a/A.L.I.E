#!/usr/bin/env python3
"""Phase 2 smoke test: plan one real topic into sub-questions.

Loads configuration, builds the Phase 1 LLM adapter, injects it into the Phase 2
planner, and prints the questions the model produced:

    Phase 2 Planner
    Topic: How does containerization affect backend deployment?

    1. ...

There is no routing, retrieval, or synthesis here — only decomposition. Tavily
is not called. Exits 0 on success, 1 on failure.

Usage (from the backend/ directory):  python scripts/phase2_smoke_test.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

# Allow running this file directly from the backend/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adapters.llm.openai_compatible_llm import (  # noqa: E402
    OpenAICompatibleLLM,
)
from application.use_cases.plan_sub_questions import (  # noqa: E402
    PlanningError,
    PlanSubQuestionsUseCase,
)
from infrastructure.config import (  # noqa: E402
    ConfigError,
    load_config,
    load_env_file,
)

TOPIC = "How does containerization affect backend deployment?"


def main() -> int:
    load_env_file()
    try:
        config = load_config()
    except ConfigError as exc:
        print(f"Config: FAILED ({exc})")
        print("Phase 2 smoke test: FAILED")
        return 1

    # The composition root: the use case is handed a port, never a provider.
    planner = PlanSubQuestionsUseCase(
        llm=OpenAICompatibleLLM(
            api_key=config.llm.api_key,
            model=config.llm.model,
            base_url=config.llm.base_url,
            timeout_seconds=config.llm.timeout_seconds,
        ),
        max_subquestions=config.planner.max_subquestions,
    )

    print("Phase 2 Planner")
    print(f"Topic: {TOPIC}")
    print()
    try:
        sub_questions = planner.execute(topic=TOPIC, research_query_id=uuid4())
    except PlanningError as exc:
        print(f"Planning: FAILED ({exc})")
        print("Phase 2 smoke test: FAILED")
        return 1

    for position, sub_question in enumerate(sub_questions, start=1):
        print(f"{position}. {sub_question.text}")

    print()
    print(
        f"Phase 2 smoke test: PASSED "
        f"({len(sub_questions)}/{config.planner.max_subquestions} sub-questions, "
        f"model={config.llm.model})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
