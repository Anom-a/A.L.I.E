# Research Agent — Backend (A.L.I.E.)

A research-agent system that decomposes a research request into sub-questions,
gathers evidence from tools with provenance, and synthesises a cited report.

This directory is the **backend**, built with **Clean Architecture**. It is
currently at **Phase 2 — Planner Use Case**.

> **Phase 2 adds the first use case**: `PlanSubQuestionsUseCase` turns one
> research topic into a bounded list of domain `SubQuestion` objects through the
> `LLMPort`. It proves the application layer can drive the Phase 0 port and the
> Phase 1 adapter without knowing either provider exists. There is still no
> routing, retrieval, criticism, synthesis, orchestration, API, or persistence.

---

## Phase status

| Phase | Scope | State |
|-------|-------|-------|
| **0-6**| Domain, Adapters, Planner, Router, Retrieve, Critique, Synthesize | ✅ done |
| **7** | LangGraph orchestration (ResearchGraph) | ✅ done |
| **8** | API, persistence | ✅ done |

### Phase 1 scope

- **`OpenAICompatibleLLM`** — implements `LLMPort` on top of the official
  OpenAI Python client, against *any* OpenAI-compatible base URL.
- **`TavilyGateway`** — implements `SearchToolPort` on top of `TavilyClient`,
  translating search results into domain `Evidence` + `Citation`.
- **`infrastructure/config.py`** — the single place that reads environment
  variables / `.env`.
- **Unit tests** that never touch the network, **integration tests** that do but
  skip themselves when credentials are absent, and a **smoke test** script.

### Phase 2 scope

- **`PlanSubQuestionsUseCase`** — the first application-layer use case: one
  research topic in, a bounded list of `SubQuestion` entities out.
- **`MAX_SUBQUESTIONS`** — the one new configuration value, injected into the
  use case as a plain integer.
- **Unit tests** driven by a fake `LLMPort`, an optional **integration test**
  against a real endpoint, and `scripts/phase2_smoke_test.py`.

The planner only *decomposes*. It does not classify, route, retrieve, criticise
or synthesise, and it never calls Tavily. Nothing from a later phase (router,
critic, synthesiser, LangGraph, FastAPI, persistence) is implemented here.

## Clean Architecture dependency rule

Dependencies point **inward only**:

```
Frameworks & Drivers   (infrastructure/config.py — env & .env)      ← Phase 1
        ↓
Interface Adapters     (OpenAICompatibleLLM, TavilyGateway)         ← Phase 1
        ↓
Application            (PlanSubQuestionsUseCase)                    ← PHASE 2
        ↓
Domain                 (entities, value objects, ports)              ← Phase 0
```

The **Domain** layer at the centre knows nothing about the layers around it and
depends only on the Python standard library. The adapters implement the domain's
**ports** structurally (`typing.Protocol` — no base class to inherit), so the
domain never imports them.

Two consequences are worth stating explicitly, because both are enforced by
tests in [`tests/unit/test_domain_imports.py`](tests/unit/test_domain_imports.py):

- The **OpenAI and Tavily SDKs appear in exactly two files** — the two adapters.
  No provider object, payload, or exception type crosses back into the domain.
- **Adapters never read the environment.** They receive plain values through
  their constructors; only `infrastructure/config.py` touches `os.environ` or
  `.env`. That is also why the adapters do not import `infrastructure` — the
  arrow would point outward.
- **The application layer imports the domain and nothing else** — no SDK, no
  framework, no adapter module, no `os`, no `dotenv`. `PlanSubQuestionsUseCase`
  depends on `LLMPort`; the concrete adapter and the sub-question limit are both
  injected by the composition root (a script, and later the API layer).

## Directory structure

```
backend/
├── domain/                            # Phase 0 — pure stdlib Python
│   ├── exceptions.py                  # DomainError, InvalidDomainValue
│   ├── entities/                      # ResearchQuery, SubQuestion, Evidence,
│   │                                  # Citation, Report, ToolCallAttempt
│   ├── value_objects/                 # ToolCategory, Confidence
│   └── ports/                         # LLMPort, SearchToolPort,
│                                      # ResearchJobRepositoryPort
├── application/                       # Phase 2 — domain-only dependencies
│   └── use_cases/
│       └── plan_sub_questions.py      # PlanSubQuestionsUseCase, PlanningError
├── adapters/                          # Phase 1 — the only place SDKs live
│   ├── llm/
│   │   └── openai_compatible_llm.py   # OpenAICompatibleLLM  -> LLMPort
│   └── gateways/
│       └── tavily_gateway.py          # TavilyGateway        -> SearchToolPort
├── infrastructure/
│   └── config.py                      # the only reader of env / .env
├── scripts/
│   ├── phase1_smoke_test.py           # one real call through each adapter
│   └── phase2_smoke_test.py           # one real topic through the planner
├── tests/
│   ├── unit/                          # no network, ever
│   └── integration/                   # real APIs; skipped without credentials
├── requirements.txt
├── pytest.ini                         # pythonpath, markers
├── .coveragerc
├── .env.example                       # placeholders only — never real secrets
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
and `ReportSection`. Value objects: `ToolCategory` (`REPAIR`, `ACADEMIC`,
`NEWS`, `GENERAL`) and `Confidence` (a score constrained to `[0.0, 1.0]`).

All entities and value objects are immutable (frozen) dataclasses that validate
their invariants on construction and raise `InvalidDomainValue`.

## Domain ports and their Phase 1 implementations

| Port                        | Contract                                                                 | Phase 1 implementation |
|-----------------------------|--------------------------------------------------------------------------|------------------------|
| `LLMPort`                   | `complete(prompt) -> str`; `complete_structured(prompt, schema) -> mapping` | `OpenAICompatibleLLM`  |
| `SearchToolPort`            | `search(sub_question) -> list[Evidence]`                                  | `TavilyGateway`        |
| `ResearchJobRepositoryPort` | `add`, `get`, `update_status`                                             | — (later phase)        |

### `OpenAICompatibleLLM`

```python
from adapters.llm.openai_compatible_llm import OpenAICompatibleLLM

llm = OpenAICompatibleLLM(
    api_key=config.llm.api_key,
    model=config.llm.model,
    base_url=config.llm.base_url,      # None -> the SDK's own default endpoint
    timeout_seconds=config.llm.timeout_seconds,
)

text = llm.complete("Summarise this in one sentence: ...")          # -> str
data = llm.complete_structured("...", {"type": "object", ...})      # -> dict
```

- The provider is **not hardcoded**: point `base_url` at OpenAI, OpenRouter,
  Groq, Together, or a local vLLM / Ollama / llama.cpp server.
- `complete_structured` passes the supplied schema through as a `json_schema`
  response format and decodes the JSON object into plain Python types.
- Every provider failure — SDK error, timeout, malformed or empty response,
  non-JSON structured output — is raised as **`LLMAdapterError`**.
- The SDK's built-in retries are switched **off**: Phase 1 has no retry policy,
  so one call means exactly one request and the timeout is a real upper bound.

### `TavilyGateway`

```python
from adapters.gateways.tavily_gateway import TavilyGateway

gateway = TavilyGateway(
    api_key=config.search.api_key,
    max_results=5,
    timeout_seconds=config.search.timeout_seconds,
)
evidence = gateway.search(sub_question)     # -> list[Evidence]
```

It is a straightforward translation boundary — **Tavily response → `Citation` →
`Evidence`** — with no retries, fallback, routing, or re-ranking. Tavily's own
result order is preserved.

- Each result becomes one `Evidence` with `source_type=SourceType.WEB`, carrying
  a `Citation` that preserves the source **URL**, its **name** (the result title,
  falling back to the host) and the **retrieval timestamp** (UTC, shared by every
  result of the one request).
- Evidence IDs are **stable**: a UUIDv5 derived from the sub-question id and the
  source URL, so re-running a search yields the same ids for the same sources.
- Results with no URL or no content are skipped — the domain forbids empty
  values, and such a result carries no usable provenance.
- Every provider failure is raised as **`SearchGatewayError`**.

## Application layer

### `PlanSubQuestionsUseCase`

The planner: one research topic in, a bounded list of `SubQuestion` entities out.

```python
from application.use_cases.plan_sub_questions import PlanSubQuestionsUseCase

planner = PlanSubQuestionsUseCase(
    llm=llm,                                       # any LLMPort
    max_subquestions=config.planner.max_subquestions,
)
sub_questions = planner.execute(
    topic="How does containerization affect backend deployment?",
    research_query_id=research_query.id,
)                                                  # -> list[SubQuestion]
```

- It holds a **port, not a client**. The adapter and the limit are injected, so
  the use case never learns which provider answers, never reads configuration,
  and never opens a socket itself.
- It asks `complete_structured` for one small schema —
  `{"sub_questions": [{"text": ...}]}` — and nothing more. The prompt lives in
  the use case (the domain has no prompts) and asks only for **decomposition**:
  no tool selection, no category, no ranking.
- Every planned `SubQuestion` is created with `ToolCategory.GENERAL` and the
  domain's default status (`PENDING`). Classification and routing belong to a
  later phase, which will replace the category.
- **Model output is never trusted.** The response must be a mapping holding a
  `sub_questions` *list* of objects with non-empty `text`; anything else is
  rejected. Texts are trimmed and whitespace-collapsed, duplicates (ignoring
  case and spacing) are dropped keeping the first occurrence, and the result is
  truncated last — so the cap always applies to *usable* questions and the
  return value is never longer than `max_subquestions`.
- Failures are `PlanningError`s, split three ways so a caller can tell them
  apart: **`InvalidPlanningRequest`** (bad topic, id, or bound),
  **`MalformedPlanError`** (the model answered with something unusable), and
  **`LLMUnavailableError`** (the call itself failed — the adapter's own
  exception is kept as the `__cause__` but never escapes).

## Configuration

`infrastructure/config.py` is the only module that reads configuration. It uses
frozen dataclasses and a few loader functions — no settings framework, no global
singleton. Missing or malformed values raise `ConfigError`.

| Variable                  | Required | Purpose |
|---------------------------|----------|---------|
| `OPENAI_API_KEY`          | yes      | Credential for the OpenAI-compatible endpoint. |
| `OPENAI_BASE_URL`         | no       | The endpoint. Omit to use the OpenAI client's default. |
| `OPENAI_MODEL_PLANNER`    | yes      | Model identifier to request. |
| `TAVILY_API_KEY`          | yes      | Credential for Tavily. |
| `REQUEST_TIMEOUT_SECONDS` | no       | Per-request timeout; defaults to `20`. |
| `MAX_SUBQUESTIONS`        | no       | Upper bound on planned sub-questions; defaults to `5`. |

Local development uses a `.env` file loaded through `python-dotenv`. Real
environment variables always win over the file, so deployments can simply export
them.

> **`.env` is git-ignored and must never be committed.** `.env.example` contains
> placeholders only. No credential appears anywhere in the source.

## Getting started

Requires **Python 3.12+**. From this `backend/` directory:

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your local configuration and fill in real values
cp .env.example .env
```

## Testing

```bash
# Everything that needs no credentials (unit tests + architecture tests).
# This is the bar CI must clear:
pytest -m "not integration"

# The whole suite. Integration tests skip themselves when keys are absent,
# so a missing credential never fails the run:
pytest

# Coverage of the inner layers:
pytest --cov=domain --cov=application --cov-report=term-missing -m "not integration"

# Real API calls (requires credentials in .env or the environment):
pytest -m integration
```

**Unit tests never touch the network.** The OpenAI and Tavily client entry
points are replaced with fakes that record how they were constructed and what
they were asked, which is how the tests assert that the configured model, base
URL, API key and timeout are the ones actually used.

### Smoke test

One real call through each adapter, printing a compact summary:

```bash
python scripts/phase1_smoke_test.py
```

```
Config: OK
LLM: OK (model=..., 4 chars returned)
Tavily: OK (3 evidence item(s), first source: ...)
Phase 1 smoke test: PASSED
```

It exits `1` and prints `FAILED` if configuration is incomplete or either
provider call fails. It is a connectivity check, not a research workflow.

One real planning run, printing the decomposition:

```bash
python scripts/phase2_smoke_test.py
```

```
Phase 2 Planner
Topic: How does containerization affect backend deployment?

1. How does containerization influence the scalability of backend services …
2. …

Phase 2 smoke test: PASSED (5/5 sub-questions, model=…)
```

The questions are model-generated, so they differ from run to run. Tavily is not
called and no research is performed.

## Not implemented yet (future phases)

Intentionally **out of scope** until later phases:

- Specialised research gateways (repair / academic / news)
- Category classification (planned sub-questions all start as `GENERAL`)
- Router (sub-question → tool category → gateway) and fallback search
- Critic (evidence evaluation / confidence)
- Synthesizer (evidence → cited `Report`)
- LangGraph orchestration of the use cases
- Async REST API (FastAPI), job persistence (behind `ResearchJobRepositoryPort`), Redis, auth
- Retry / backoff policies
