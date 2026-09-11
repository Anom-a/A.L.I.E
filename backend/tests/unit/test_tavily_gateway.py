"""Unit tests for :class:`TavilyGateway`.

These never touch the network and never build a real ``TavilyClient``: the
module's client entry point is replaced with a fake that records how it was
constructed and what it was asked to search, and returns canned payloads shaped
like real Tavily responses.
"""

from __future__ import annotations

import socket
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

import pytest

import adapters.gateways.tavily_gateway as module
from adapters.gateways.tavily_gateway import TavilyGateway
from adapters.exceptions import SearchGatewayError
from domain.entities.citation import Citation
from domain.entities.evidence import Evidence, SourceType
from domain.entities.sub_question import SubQuestion
from domain.ports.search_tool_port import SearchToolPort
from domain.value_objects.tool_category import ToolCategory

FIXED_NOW = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)


class _ProviderError(Exception):
    """Stands in for a Tavily SDK exception; the adapter must never leak it."""


def _result(url: str, title: str, content: str, **extra: Any) -> dict[str, Any]:
    """A single result shaped like Tavily's, including fields we ignore."""
    return {"url": url, "title": title, "content": content, "score": 0.9, **extra}


class _FakeClient:
    def __init__(self, **kwargs: Any) -> None:
        self.init_kwargs = kwargs
        self.calls: list[dict[str, Any]] = []
        self.payload: Any = {"query": "q", "results": []}
        self.error: Optional[Exception] = None

    def search(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.payload


@pytest.fixture
def clients(monkeypatch: pytest.MonkeyPatch) -> list[_FakeClient]:
    """Replace the SDK entry point and record every client the gateway builds."""
    built: list[_FakeClient] = []

    def _factory(**kwargs: Any) -> _FakeClient:
        client = _FakeClient(**kwargs)
        built.append(client)
        return client

    monkeypatch.setattr(module, "TavilyClient", _factory)
    return built


@pytest.fixture
def sub_question() -> SubQuestion:
    return SubQuestion(
        research_query_id=uuid4(),
        text="What is the capital of France?",
        category=ToolCategory.GENERAL,
    )


def _build(**overrides: Any) -> TavilyGateway:
    params: dict[str, Any] = {
        "api_key": "tvly-test-key",
        "max_results": 5,
        "timeout_seconds": 7.5,
        "clock": lambda: FIXED_NOW,
    }
    params.update(overrides)
    return TavilyGateway(**params)


# --- port conformance -------------------------------------------------------


def test_gateway_implements_search_tool_port(clients: list[_FakeClient]) -> None:
    assert isinstance(_build(), SearchToolPort)


# --- configuration is honoured ---------------------------------------------


def test_configured_api_key_is_used(clients: list[_FakeClient]) -> None:
    _build(api_key="tvly-configured-value")
    assert clients[0].init_kwargs["api_key"] == "tvly-configured-value"


def test_correct_query_is_sent(
    clients: list[_FakeClient], sub_question: SubQuestion
) -> None:
    _build().search(sub_question)
    assert clients[0].calls[0]["query"] == "What is the capital of France?"


def test_max_results_and_timeout_are_sent(
    clients: list[_FakeClient], sub_question: SubQuestion
) -> None:
    _build(max_results=3, timeout_seconds=4).search(sub_question)
    call = clients[0].calls[0]
    assert call["max_results"] == 3
    assert call["timeout"] == 4.0


def test_search_makes_exactly_one_request(
    clients: list[_FakeClient], sub_question: SubQuestion
) -> None:
    # No retries, no fallback: one sub-question is one Tavily request.
    _build().search(sub_question)
    assert len(clients[0].calls) == 1


def test_injected_client_is_used_as_is(
    monkeypatch: pytest.MonkeyPatch, sub_question: SubQuestion
) -> None:
    def _explode(**_: Any) -> None:
        raise AssertionError("gateway must not build a client when one is injected")

    monkeypatch.setattr(module, "TavilyClient", _explode)
    fake = _FakeClient()
    assert TavilyGateway(api_key="k", client=fake).search(sub_question) == []


# --- translation to the domain ---------------------------------------------


def test_result_is_converted_to_evidence(
    clients: list[_FakeClient], sub_question: SubQuestion
) -> None:
    gateway = _build()
    clients[0].payload = {
        "results": [
            _result(
                "https://example.com/paris",
                "Paris — Britannica",
                "Paris is the capital of France.",
            )
        ]
    }
    evidence = gateway.search(sub_question)

    assert len(evidence) == 1
    item = evidence[0]
    assert isinstance(item, Evidence)
    assert item.content == "Paris is the capital of France."
    assert item.source_type is SourceType.WEB
    assert item.sub_question_id == sub_question.id


def test_citation_information_is_preserved(
    clients: list[_FakeClient], sub_question: SubQuestion
) -> None:
    gateway = _build()
    clients[0].payload = {
        "results": [
            _result(
                "https://example.com/paris",
                "Paris — Britannica",
                "Paris is the capital of France.",
            )
        ]
    }
    citation = gateway.search(sub_question)[0].citation

    assert isinstance(citation, Citation)
    assert citation.source_url_or_id == "https://example.com/paris"
    assert citation.source_name == "Paris — Britannica"
    assert citation.retrieved_at == FIXED_NOW


def test_source_name_falls_back_to_host_when_title_is_missing(
    clients: list[_FakeClient], sub_question: SubQuestion
) -> None:
    gateway = _build()
    clients[0].payload = {"results": [_result("https://example.com/x", "", "some text")]}
    assert gateway.search(sub_question)[0].citation.source_name == "example.com"


def test_multiple_results_become_multiple_evidence_in_order(
    clients: list[_FakeClient], sub_question: SubQuestion
) -> None:
    gateway = _build()
    clients[0].payload = {
        "results": [
            _result("https://a.example/1", "A", "content a"),
            _result("https://b.example/2", "B", "content b"),
            _result("https://c.example/3", "C", "content c"),
        ]
    }
    evidence = gateway.search(sub_question)

    assert len(evidence) == 3
    # Tavily's own ordering is preserved; the gateway does not re-rank.
    assert [e.content for e in evidence] == ["content a", "content b", "content c"]
    assert [e.citation.source_url_or_id for e in evidence] == [
        "https://a.example/1",
        "https://b.example/2",
        "https://c.example/3",
    ]


def test_empty_results_produce_an_empty_list(
    clients: list[_FakeClient], sub_question: SubQuestion
) -> None:
    gateway = _build()
    clients[0].payload = {"query": "q", "results": []}
    assert gateway.search(sub_question) == []


def test_missing_results_key_produces_an_empty_list(
    clients: list[_FakeClient], sub_question: SubQuestion
) -> None:
    gateway = _build()
    clients[0].payload = {"query": "q"}
    assert gateway.search(sub_question) == []


def test_evidence_ids_are_stable_across_searches(
    clients: list[_FakeClient], sub_question: SubQuestion
) -> None:
    payload = {"results": [_result("https://example.com/paris", "P", "content")]}
    gateway = _build()
    clients[0].payload = payload

    first = gateway.search(sub_question)[0].id
    second = gateway.search(sub_question)[0].id

    assert isinstance(first, UUID)
    assert first == second


def test_evidence_ids_differ_per_source_and_per_sub_question(
    clients: list[_FakeClient], sub_question: SubQuestion
) -> None:
    gateway = _build()
    clients[0].payload = {
        "results": [
            _result("https://a.example/1", "A", "content a"),
            _result("https://b.example/2", "B", "content b"),
        ]
    }
    ids = [e.id for e in gateway.search(sub_question)]
    assert ids[0] != ids[1]

    other = SubQuestion(
        research_query_id=sub_question.research_query_id,
        text="A different question?",
        category=ToolCategory.GENERAL,
    )
    assert gateway.search(other)[0].id != ids[0]


def test_results_without_usable_content_or_url_are_skipped(
    clients: list[_FakeClient], sub_question: SubQuestion
) -> None:
    gateway = _build()
    clients[0].payload = {
        "results": [
            _result("https://good.example/1", "Good", "usable content"),
            _result("https://no-content.example/2", "Empty", "   "),
            _result("", "No URL", "orphan content"),
            {"url": "https://missing-fields.example/3"},
            "not-a-mapping",
        ]
    }
    evidence = gateway.search(sub_question)
    assert [e.citation.source_url_or_id for e in evidence] == ["https://good.example/1"]


def test_no_tavily_payload_escapes_the_adapter(
    clients: list[_FakeClient], sub_question: SubQuestion
) -> None:
    gateway = _build()
    clients[0].payload = {
        "results": [_result("https://example.com/x", "X", "content", raw_content="raw")],
        "response_time": 1.23,
    }
    assert all(type(item) is Evidence for item in gateway.search(sub_question))


# --- failure translation ----------------------------------------------------


def test_tavily_failure_becomes_adapter_error(
    clients: list[_FakeClient], sub_question: SubQuestion
) -> None:
    gateway = _build()
    clients[0].error = _ProviderError("usage limit exceeded")
    with pytest.raises(SearchGatewayError) as excinfo:
        gateway.search(sub_question)
    # The original cause is preserved for logging, but not raised to callers.
    assert isinstance(excinfo.value.__cause__, _ProviderError)


@pytest.mark.parametrize(
    "payload",
    [None, "unexpected", {"results": "not-a-list"}],
    ids=["none", "string", "results-not-a-list"],
)
def test_unusable_payload_becomes_adapter_error(
    clients: list[_FakeClient], sub_question: SubQuestion, payload: Any
) -> None:
    gateway = _build()
    clients[0].payload = payload
    with pytest.raises(SearchGatewayError):
        gateway.search(sub_question)


def test_non_sub_question_input_is_rejected(clients: list[_FakeClient]) -> None:
    with pytest.raises(SearchGatewayError):
        _build().search("just a string")


@pytest.mark.parametrize(
    "overrides",
    [{"api_key": ""}, {"api_key": "  "}, {"max_results": 0}, {"timeout_seconds": 0}],
    ids=["empty-key", "blank-key", "non-positive-results", "non-positive-timeout"],
)
def test_invalid_configuration_is_rejected(
    clients: list[_FakeClient], overrides: dict[str, Any]
) -> None:
    with pytest.raises(SearchGatewayError):
        _build(**overrides)


# --- no network -------------------------------------------------------------


def test_no_network_call_is_made(
    clients: list[_FakeClient],
    sub_question: SubQuestion,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _blocked(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("unit tests must not open a network connection")

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)

    gateway = _build()
    clients[0].payload = {"results": [_result("https://example.com/x", "X", "content")]}
    assert len(gateway.search(sub_question)) == 1


def test_default_clock_produces_a_utc_timestamp(
    clients: list[_FakeClient], sub_question: SubQuestion
) -> None:
    gateway = TavilyGateway(api_key="k")
    clients[0].payload = {"results": [_result("https://example.com/x", "X", "content")]}
    retrieved_at = gateway.search(sub_question)[0].citation.retrieved_at
    assert retrieved_at.tzinfo is timezone.utc


def test_source_name_falls_back_to_the_url_when_the_host_cannot_be_parsed(
    clients: list[_FakeClient], sub_question: SubQuestion
) -> None:
    # A URL urlparse() rejects (malformed IPv6) must not blow up the search:
    # with no title and no parseable host, the URL itself names the source.
    gateway = _build()
    clients[0].payload = {"results": [_result("http://[::1/bad", "", "some text")]}
    assert gateway.search(sub_question)[0].citation.source_name == "http://[::1/bad"
