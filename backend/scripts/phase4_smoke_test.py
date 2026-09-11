#!/usr/bin/env python3
"""Phase 4 smoke test: retrieve evidence for a repair question.

Uses the real Phase 3 router, Phase 1 Tavily gateway, and Phase 4 iFixit
gateway to exercise the full retrieval + fallback pipeline.  Performs one or
two controlled API calls.

Usage (from the backend/ directory):  python scripts/phase4_smoke_test.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

# Allow running this file directly from the backend/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adapters.gateways.ifixit_gateway import IFixitGateway  # noqa: E402
from adapters.gateways.tavily_gateway import TavilyGateway  # noqa: E402
from application.classifiers.keyword_classifier import (  # noqa: E402
    KeywordSubQuestionClassifier,
)
from application.use_cases.retrieve_evidence import (  # noqa: E402
    RetrievalError,
    RetrieveEvidenceUseCase,
)
from application.use_cases.route_tool import RouteToolUseCase  # noqa: E402
from domain.entities.sub_question import SubQuestion  # noqa: E402
from domain.value_objects.tool_category import ToolCategory  # noqa: E402
from infrastructure.config import (  # noqa: E402
    ConfigError,
    load_config,
    load_env_file,
)


def main() -> int:
    load_env_file()
    try:
        config = load_config()
    except ConfigError as exc:
        print(f"Config: FAILED ({exc})")
        print("Phase 4 smoke test: FAILED")
        return 1

    # --- Build components ---
    classifier = KeywordSubQuestionClassifier()
    router = RouteToolUseCase(classifier=classifier)

    ifixit_gateway = IFixitGateway(
        timeout_seconds=config.search.timeout_seconds,
    )
    tavily_gateway = TavilyGateway(
        api_key=config.search.api_key,
        timeout_seconds=config.search.timeout_seconds,
    )

    use_case = RetrieveEvidenceUseCase(
        router=router,
        gateways={
            "ifixit": ifixit_gateway,
            "tavily": tavily_gateway,
        },
        fallback_gateway=tavily_gateway,
    )

    print("Phase 4 Retrieval")
    print()

    # --- Example 1: repair question → should route to iFixit ---
    research_id = uuid4()
    sq = SubQuestion(
        research_query_id=research_id,
        text="iPhone 13 battery replacement",
        category=ToolCategory.GENERAL,
    )

    # Temporary: print actual exceptions raised by the gateway
    original_search = ifixit_gateway.search
    def debug_search(*args, **kwargs):
        try:
            return original_search(*args, **kwargs)
        except Exception as e:
            print(f"DEBUG: ifixit gateway failed with: {e}")
            raise
    ifixit_gateway.search = debug_search

    try:
        result = use_case.execute(sq)
    except RetrievalError as exc:
        print(f"Retrieval: FAILED ({exc})")
        print("Phase 4 smoke test: FAILED")
        return 1

    print(f"Primary tool: {result.primary_tool}")
    print(f"Primary result: {'OK' if result.attempts[0].succeeded else 'FAILED'}")
    if result.fallback_used:
        print(f"Fallback: {result.attempts[-1].tool_name}")
        print(
            f"Fallback result: {'OK' if result.attempts[-1].succeeded else 'FAILED'}"
        )
    else:
        print("Fallback used: NO")
    print(f"Resolved: {'YES' if result.resolved else 'NO'}")
    print(f"Evidence items: {len(result.evidence)}")
    print(f"Total attempts: {len(result.attempts)}")

    if result.evidence:
        print()
        print(f"First evidence: {result.evidence[0].content[:100]}...")

    print()
    if result.resolved:
        print("Phase 4 smoke test: PASSED")
        return 0
    else:
        print("Phase 4 smoke test: FAILED (unresolved)")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
