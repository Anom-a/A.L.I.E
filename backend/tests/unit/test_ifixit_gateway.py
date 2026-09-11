"""Unit tests for :class:`IFixitGateway`.

These never touch the network: the underlying HTTP client is replaced with a
fake that returns canned payloads shaped like real iFixit API responses.
"""

from __future__ import annotations

import socket
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

import httpx
import pytest

import adapters.gateways.ifixit_gateway as module
from adapters.gateways.ifixit_gateway import IFixitGateway, DEFAULT_BASE_URL
from adapters.gateways.tavily_gateway import SearchGatewayError
from domain.entities.citation import Citation
from domain.entities.evidence import Evidence, SourceType
from domain.entities.sub_question import SubQuestion
from domain.ports.search_tool_port import SearchToolPort
from domain.value_objects.tool_category import ToolCategory

FIXED_NOW = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)


def _ifixit_result(
    url: str, title: str, summary: str, **extra: Any
) -> dict[str, Any]:
    """A single result shaped like iFixit's search API."""
    return {
        "dataType": "guide",
        "url": url,
        "title": title,
        "summary": summary,
        "guideid": 12345,
        **extra,
    }


class _FakeTransport(httpx.BaseTransport):
    """An httpx transport that records calls and returns canned responses."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.payload: Any = {"search": "q", "results": []}
        self.status_code: int = 200
        self.error: Optional[Exception] = None

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        import json

        return httpx.Response(
            status_code=self.status_code,
            json=self.payload,
            request=request,
        )


@pytest.fixture()
def transport() -> _FakeTransport:
    return _FakeTransport()


@pytest.fixture()
def fake_client(transport: _FakeTransport) -> httpx.Client:
    return httpx.Client(transport=transport)


@pytest.fixture()
def sub_question() -> SubQuestion:
    return SubQuestion(
        research_query_id=uuid4(),
        text="How to replace an iPhone battery?",
        category=ToolCategory.REPAIR,
    )


def _build(client: httpx.Client, **overrides: Any) -> IFixitGateway:
    params: dict[str, Any] = {
        "base_url": "https://www.ifixit.com/api/2.0",
        "max_results": 5,
        "timeout_seconds": 7.5,
        "client": client,
        "clock": lambda: FIXED_NOW,
    }
    params.update(overrides)
    return IFixitGateway(**params)


# --- port conformance -------------------------------------------------------


def test_gateway_implements_search_tool_port(fake_client: httpx.Client) -> None:
    assert isinstance(_build(fake_client), SearchToolPort)


# --- valid API response → Evidence -------------------------------------------


def test_valid_response_becomes_evidence(
    transport: _FakeTransport, fake_client: httpx.Client, sub_question: SubQuestion
) -> None:
    transport.payload = {
        "results": [
            _ifixit_result(
                "https://www.ifixit.com/Guide/iPhone+13+Battery+Replacement/145896",
                "iPhone 13 Battery Replacement",
                "iPhone batteries are rated to hold 80% of their capacity...",
            )
        ]
    }
    evidence = _build(fake_client).search(sub_question)

    assert len(evidence) == 1
    item = evidence[0]
    assert isinstance(item, Evidence)
    assert item.content == "iPhone batteries are rated to hold 80% of their capacity..."
    assert item.source_type is SourceType.DOCUMENTATION
    assert item.sub_question_id == sub_question.id


# --- source URL/id is preserved ----------------------------------------------


def test_source_url_is_preserved(
    transport: _FakeTransport, fake_client: httpx.Client, sub_question: SubQuestion
) -> None:
    url = "https://www.ifixit.com/Guide/iPhone+13+Battery+Replacement/145896"
    transport.payload = {
        "results": [_ifixit_result(url, "Title", "Content")]
    }
    citation = _build(fake_client).search(sub_question)[0].citation
    assert citation.source_url_or_id == url


# --- source name is preserved ------------------------------------------------


def test_source_name_is_preserved(
    transport: _FakeTransport, fake_client: httpx.Client, sub_question: SubQuestion
) -> None:
    transport.payload = {
        "results": [
            _ifixit_result(
                "https://www.ifixit.com/Guide/Test/1",
                "iPhone 13 Battery Replacement",
                "Content here",
            )
        ]
    }
    citation = _build(fake_client).search(sub_question)[0].citation
    assert citation.source_name == "iPhone 13 Battery Replacement"


def test_source_name_falls_back_to_url_when_title_is_empty(
    transport: _FakeTransport, fake_client: httpx.Client, sub_question: SubQuestion
) -> None:
    url = "https://www.ifixit.com/Guide/Test/1"
    transport.payload = {
        "results": [_ifixit_result(url, "", "Content")]
    }
    assert _build(fake_client).search(sub_question)[0].citation.source_name == url


# --- retrieved timestamp exists -----------------------------------------------


def test_retrieved_timestamp_exists(
    transport: _FakeTransport, fake_client: httpx.Client, sub_question: SubQuestion
) -> None:
    transport.payload = {
        "results": [_ifixit_result("https://x.com/1", "T", "C")]
    }
    citation = _build(fake_client).search(sub_question)[0].citation
    assert isinstance(citation.retrieved_at, datetime)
    assert citation.retrieved_at == FIXED_NOW


# --- multiple results → multiple Evidence ------------------------------------


def test_multiple_results_become_multiple_evidence_in_order(
    transport: _FakeTransport, fake_client: httpx.Client, sub_question: SubQuestion
) -> None:
    transport.payload = {
        "results": [
            _ifixit_result("https://a.example/1", "A", "content a"),
            _ifixit_result("https://b.example/2", "B", "content b"),
            _ifixit_result("https://c.example/3", "C", "content c"),
        ]
    }
    evidence = _build(fake_client).search(sub_question)

    assert len(evidence) == 3
    assert [e.content for e in evidence] == ["content a", "content b", "content c"]
    assert [e.citation.source_url_or_id for e in evidence] == [
        "https://a.example/1",
        "https://b.example/2",
        "https://c.example/3",
    ]


# --- empty API results → [] --------------------------------------------------


def test_empty_results_return_empty_list(
    transport: _FakeTransport, fake_client: httpx.Client, sub_question: SubQuestion
) -> None:
    transport.payload = {"search": "q", "results": []}
    assert _build(fake_client).search(sub_question) == []


def test_missing_results_key_returns_empty_list(
    transport: _FakeTransport, fake_client: httpx.Client, sub_question: SubQuestion
) -> None:
    transport.payload = {"search": "q"}
    assert _build(fake_client).search(sub_question) == []


# --- API failure → adapter exception -----------------------------------------


def test_api_failure_becomes_search_gateway_error(
    transport: _FakeTransport, fake_client: httpx.Client, sub_question: SubQuestion
) -> None:
    transport.error = httpx.ConnectError("connection refused")
    with pytest.raises(SearchGatewayError, match="iFixit search failed"):
        _build(fake_client).search(sub_question)


def test_http_error_status_becomes_search_gateway_error(
    transport: _FakeTransport, fake_client: httpx.Client, sub_question: SubQuestion
) -> None:
    transport.status_code = 500
    transport.payload = {"error": "Internal Server Error"}
    with pytest.raises(SearchGatewayError, match="iFixit search failed"):
        _build(fake_client).search(sub_question)


# --- no secret is hardcoded --------------------------------------------------


def test_no_secret_is_hardcoded() -> None:
    """The gateway must not contain any hardcoded API key."""
    import inspect

    source = inspect.getsource(module)
    # iFixit's public API doesn't need a key, but the adapter must not embed one.
    assert "api_key" not in source.lower().replace("api_key", "").replace(
        "API_KEY", ""
    ), "Hardcoded API key found in iFixit gateway source"


# --- exactly one external search operation per invocation --------------------


def test_exactly_one_request_per_search(
    transport: _FakeTransport, fake_client: httpx.Client, sub_question: SubQuestion
) -> None:
    transport.payload = {
        "results": [_ifixit_result("https://x.com/1", "T", "C")]
    }
    _build(fake_client).search(sub_question)
    assert len(transport.requests) == 1


# --- input validation --------------------------------------------------------


def test_non_sub_question_input_is_rejected(fake_client: httpx.Client) -> None:
    with pytest.raises(SearchGatewayError):
        _build(fake_client).search("just a string")


# --- configuration validation ------------------------------------------------


@pytest.mark.parametrize(
    "overrides",
    [
        {"base_url": ""},
        {"base_url": "  "},
        {"max_results": 0},
        {"timeout_seconds": 0},
    ],
    ids=["empty-url", "blank-url", "non-positive-results", "non-positive-timeout"],
)
def test_invalid_configuration_is_rejected(
    fake_client: httpx.Client, overrides: dict[str, Any]
) -> None:
    with pytest.raises(SearchGatewayError):
        _build(fake_client, **overrides)


# --- results without usable content are skipped ------------------------------


def test_results_without_usable_content_are_skipped(
    transport: _FakeTransport, fake_client: httpx.Client, sub_question: SubQuestion
) -> None:
    transport.payload = {
        "results": [
            _ifixit_result("https://good.example/1", "Good", "usable content"),
            _ifixit_result("https://no-summary.example/2", "Empty", "   "),
            _ifixit_result("", "No URL", "orphan content"),
            {"url": "https://missing-fields.example/3"},
            "not-a-mapping",
        ]
    }
    evidence = _build(fake_client).search(sub_question)
    assert [e.citation.source_url_or_id for e in evidence] == [
        "https://good.example/1"
    ]


# --- unusable payloads -------------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    [None, "unexpected", {"results": "not-a-list"}],
    ids=["none", "string", "results-not-a-list"],
)
def test_unusable_payload_becomes_adapter_error(
    transport: _FakeTransport,
    fake_client: httpx.Client,
    sub_question: SubQuestion,
    payload: Any,
) -> None:
    transport.payload = payload
    with pytest.raises(SearchGatewayError):
        _build(fake_client).search(sub_question)


# --- evidence ids are stable --------------------------------------------------


def test_evidence_ids_are_stable(
    transport: _FakeTransport, fake_client: httpx.Client, sub_question: SubQuestion
) -> None:
    transport.payload = {
        "results": [_ifixit_result("https://example.com/guide", "T", "content")]
    }
    gateway = _build(fake_client)

    first = gateway.search(sub_question)[0].id
    second = gateway.search(sub_question)[0].id

    assert isinstance(first, UUID)
    assert first == second


# --- no network ---------------------------------------------------------------


def test_no_network_call_is_made(
    transport: _FakeTransport,
    fake_client: httpx.Client,
    sub_question: SubQuestion,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _blocked(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("unit tests must not open a network connection")

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)

    transport.payload = {
        "results": [_ifixit_result("https://example.com/x", "X", "content")]
    }
    assert len(_build(fake_client).search(sub_question)) == 1


# --- default clock produces UTC timestamp ------------------------------------


def test_default_clock_produces_a_utc_timestamp(
    transport: _FakeTransport, fake_client: httpx.Client, sub_question: SubQuestion
) -> None:
    gateway = IFixitGateway(client=fake_client)
    transport.payload = {
        "results": [_ifixit_result("https://example.com/x", "X", "content")]
    }
    retrieved_at = gateway.search(sub_question)[0].citation.retrieved_at
    assert retrieved_at.tzinfo is timezone.utc
