# Research Agent — Backend (A.L.I.E.)

A research-agent system that decomposes a research request into sub-questions,
gathers evidence from tools with provenance, and synthesises a cited report.

This directory is the **backend**, built with **Clean Architecture**. It is
currently at **Phase 0 — Skeleton & Domain Model**.

> **Phase 0 performs no external API calls.** There is no network I/O, no LLM
> call, no database access, and no environment-variable loading anywhere in this
> phase. The domain layer is pure, standard-library-only Python.

---

## Phase 0 scope

Phase 0 establishes the innermost layer of the architecture and its safety net:

- **Domain entities** — the core business objects and their invariants.
- **Domain value objects** — small, immutable, self-validating values.
- **Domain ports** — `typing.Protocol` interfaces the outer layers will implement later (dependency inversion).
- **A domain exception strategy** — domain-specific errors instead of leaked framework exceptions.
- **Unit tests** — behaviour and invariant tests for every domain component, plus architecture tests that fail if the domain ever imports a framework.
- **Minimal project/test scaffolding** — `requirements.txt`, `pytest.ini`, `.coveragerc`, `.gitignore`, `.env.example`.

Nothing from a later phase (LLM adapters, gateways, use cases, routing, the REST
API, LangGraph, persistence) is implemented here.

## Clean Architecture dependency rule

Dependencies point **inward only**:

```
Frameworks & Drivers   (FastAPI, LangGraph, OpenAI SDK, DB drivers)   ← later
        ↓
Interface Adapters     (controllers, gateways, repositories)         ← later
        ↓
Application            (use cases, orchestration)                     ← later
        ↓
Domain                 (entities, value objects, ports)   ← THIS PHASE
```

The **Domain** layer at the centre knows nothing about the layers around it. It
depends only on the Python standard library. Outer layers depend on the domain
through the **ports** (Protocol interfaces) defined here, so concrete
implementations can be injected later without the domain ever importing them.
This rule is enforced automatically by
[`tests/unit/test_domain_imports.py`](tests/unit/test_domain_imports.py), which
fails the build if any module under `domain/` imports a non-standard-library
package.

## Directory structure

```
backend/
├── domain/
│   ├── __init__.py
│   ├── exceptions.py            # DomainError, InvalidDomainValue
│   ├── entities/
│   │   ├── research_query.py    # ResearchQuery + ResearchStatus
│   │   ├── sub_question.py      # SubQuestion + SubQuestionStatus
│   │   ├── evidence.py          # Evidence + SourceType
│   │   ├── citation.py          # Citation
│   │   ├── report.py            # Report + ReportSection
│   │   └── tool_call_attempt.py # ToolCallAttempt
│   ├── value_objects/
│   │   ├── tool_category.py     # ToolCategory
│   │   └── confidence.py        # Confidence
│   └── ports/
│       ├── llm_port.py               # LLMPort
│       ├── search_tool_port.py       # SearchToolPort
│       └── job_repository_port.py    # ResearchJobRepositoryPort
├── tests/
│   └── unit/                    # one test module per domain component + arch tests
├── requirements.txt             # pytest, pytest-cov (dev/test only)
├── pytest.ini
├── .coveragerc
├── .gitignore
├── .env.example
└── README.md
```

## Domain entities

| Entity            | Purpose                                                        | Key invariants |
|-------------------|----------------------------------------------------------------|----------------|
| `ResearchQuery`   | The original user research request (root of a job).            | `topic` non-empty; always has `id`, `created_at`, and a valid `ResearchStatus`. |
| `SubQuestion`     | One decomposed research question.                              | `text` non-empty; `category` is a `ToolCategory`; valid identifiers and status. |
| `ToolCallAttempt` | Audit record of one attempt to use one tool for one sub-question. | `tool_name` non-empty; `sub_question_id` present; booleans are booleans; has a `timestamp`. |
| `Evidence`        | Retrieved content with provenance.                             | `content` non-empty; a `Citation` is required; valid `source_type`. |
| `Citation`        | Provenance for evidence (and later report claims).             | `source_url_or_id` and `source_name` non-empty; has `retrieved_at`. |
| `Report`          | The final synthesised result.                                  | **At least one citation**; sections may only reference citations the report holds. |

Supporting types: `ResearchStatus`, `SubQuestionStatus`, `SourceType` (enums)
and `ReportSection` (a framework-independent section = title + prose + citation
references).

Value objects: `ToolCategory` (`REPAIR`, `ACADEMIC`, `NEWS`, `GENERAL`) and
`Confidence` (a score constrained to `[0.0, 1.0]`).

All entities and value objects are immutable (frozen) dataclasses that validate
their invariants on construction and raise `InvalidDomainValue` (a subclass of
`DomainError`) when violated.

## Domain ports

Defined with `typing.Protocol`; **not implemented** in Phase 0. They speak only
in standard-library and domain types — never provider SDK types.

| Port                          | Conceptual contract |
|-------------------------------|---------------------|
| `LLMPort`                     | `complete(prompt) -> str`; `complete_structured(prompt, schema) -> mapping` |
| `SearchToolPort`              | `search(sub_question) -> list[Evidence]` |
| `ResearchJobRepositoryPort`   | `add(query)`; `get(query_id) -> ResearchQuery | None`; `update_status(query_id, status)` |

## Getting started

Requires **Python 3.12+**. From this `backend/` directory:

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. Install development dependencies
pip install -r requirements.txt

# 3. Run the tests
pytest

# 4. Run the tests with coverage of the domain layer
pytest --cov=domain --cov-report=term-missing
```

## Not implemented yet (future phases)

The following are intentionally **out of scope for Phase 0** and will arrive in
later phases as outer layers that depend inward on the domain:

- LLM adapter (OpenAI-compatible client behind `LLMPort`)
- Web search gateway (behind `SearchToolPort`)
- Specialised research gateways (repair / academic / news)
- Planner (query → sub-questions)
- Router (sub-question → tool category → gateway)
- Critic (evidence evaluation / confidence)
- Synthesizer (evidence → cited `Report`)
- LangGraph orchestration
- Async REST API (FastAPI) and job persistence (behind `ResearchJobRepositoryPort`)
- Configuration / environment loading
