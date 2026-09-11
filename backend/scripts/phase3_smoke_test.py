#!/usr/bin/env python3
"""Phase 3 smoke test: route sample sub-questions through the two-stage router.

Constructs the keyword classifier and router, creates several sample
SubQuestion objects, routes them, and prints the results.  No external service
is called.

Usage (from the backend/ directory):  python scripts/phase3_smoke_test.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

# Allow running this file directly from the backend/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from application.classifiers.keyword_classifier import (  # noqa: E402
    KeywordSubQuestionClassifier,
)
from application.use_cases.route_tool import (  # noqa: E402
    RouteToolUseCase,
)
from domain.entities.sub_question import SubQuestion  # noqa: E402
from domain.value_objects.tool_category import ToolCategory  # noqa: E402

SAMPLES = [
    "How do I repair an iPhone battery?",
    "What are the best scholarly studies on flaky tests?",
    "What happened in AI news this week?",
    "What are the main causes of database deadlocks?",
]


def main() -> int:
    classifier = KeywordSubQuestionClassifier()
    router = RouteToolUseCase(classifier=classifier)
    research_query_id = uuid4()

    print("Phase 3 Router")
    print()

    all_passed = True
    for text in SAMPLES:
        sq = SubQuestion(
            research_query_id=research_query_id,
            text=text,
            category=ToolCategory.GENERAL,
        )
        try:
            result = router.execute(sq)
        except Exception as exc:
            print(f"Question: {text}")
            print(f"  ERROR: {exc}")
            print()
            all_passed = False
            continue

        print(f"Question: {text}")
        print(f"  Category: {result.category.name}")
        print(f"  Tool: {result.tool_name}")
        print()

    if all_passed:
        print("Phase 3 smoke test: PASSED")
        return 0
    else:
        print("Phase 3 smoke test: FAILED")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
