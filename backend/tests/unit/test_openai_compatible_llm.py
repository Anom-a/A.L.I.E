"""Unit tests for :class:`OpenAICompatibleLLM`.

These never touch the network and never build a real SDK client: the module's
``OpenAI`` entry point is replaced with a fake that records how it was
constructed and what requests it received. That is what makes it possible to
assert on the model, base URL, API key and timeout the adapter actually used.
"""

from __future__ import annotations

import socket
from types import SimpleNamespace
from typing import Any, Optional

import pytest

import adapters.llm.openai_compatible_llm as module
from adapters.llm.openai_compatible_llm import LLMAdapterError, OpenAICompatibleLLM
from domain.ports.llm_port import LLMPort


class _ProviderError(Exception):
    """Stands in for an SDK exception; the adapter must never leak it."""


def _response(content: Any) -> SimpleNamespace:
    """Shape-compatible stand-in for a chat-completion response object."""
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


class _FakeCompletions:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.response: Any = _response("hello there")
        self.error: Optional[Exception] = None

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


class _FakeClient:
    def __init__(self, **kwargs: Any) -> None:
        self.init_kwargs = kwargs
        self.completions = _FakeCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


@pytest.fixture
def clients(monkeypatch: pytest.MonkeyPatch) -> list[_FakeClient]:
    """Replace the SDK entry point and record every client the adapter builds."""
    built: list[_FakeClient] = []

    def _factory(**kwargs: Any) -> _FakeClient:
        client = _FakeClient(**kwargs)
        built.append(client)
        return client

    monkeypatch.setattr(module, "OpenAI", _factory)
    return built


def _build(**overrides: Any) -> OpenAICompatibleLLM:
    params: dict[str, Any] = {
        "api_key": "test-key",
        "model": "test-model",
        "base_url": "https://llm.example.invalid/v1",
        "timeout_seconds": 7.5,
    }
    params.update(overrides)
    return OpenAICompatibleLLM(**params)


# --- port conformance -------------------------------------------------------


def test_adapter_implements_llm_port(clients: list[_FakeClient]) -> None:
    assert isinstance(_build(), LLMPort)


# --- configuration is honoured ---------------------------------------------


def test_configured_model_is_sent(clients: list[_FakeClient]) -> None:
    _build(model="mistral-small-latest").complete("hi")
    assert clients[0].completions.calls[0]["model"] == "mistral-small-latest"


def test_configured_base_url_is_respected(clients: list[_FakeClient]) -> None:
    _build(base_url="http://localhost:11434/v1")
    assert clients[0].init_kwargs["base_url"] == "http://localhost:11434/v1"


def test_omitted_base_url_falls_back_to_sdk_default(
    clients: list[_FakeClient],
) -> None:
    # None means "let the SDK use its own default endpoint".
    _build(base_url=None)
    assert clients[0].init_kwargs["base_url"] is None


def test_configured_api_key_is_used(clients: list[_FakeClient]) -> None:
    _build(api_key="sk-configured-value")
    assert clients[0].init_kwargs["api_key"] == "sk-configured-value"


def test_timeout_is_passed_to_client_and_to_each_request(
    clients: list[_FakeClient],
) -> None:
    _build(timeout_seconds=3).complete("hi")
    assert clients[0].init_kwargs["timeout"] == 3.0
    assert clients[0].completions.calls[0]["timeout"] == 3.0


def test_no_sdk_retries_are_configured(clients: list[_FakeClient]) -> None:
    # Phase 1 has no retry policy: one call must mean one request.
    _build()
    assert clients[0].init_kwargs["max_retries"] == 0


def test_prompt_is_sent_as_a_user_message(clients: list[_FakeClient]) -> None:
    _build().complete("what is 2 + 2?")
    assert clients[0].completions.calls[0]["messages"] == [
        {"role": "user", "content": "what is 2 + 2?"}
    ]


def test_injected_client_is_used_as_is(monkeypatch: pytest.MonkeyPatch) -> None:
    def _explode(**_: Any) -> None:
        raise AssertionError("adapter must not build a client when one is injected")

    monkeypatch.setattr(module, "OpenAI", _explode)
    fake = _FakeClient()
    assert OpenAICompatibleLLM(api_key="k", model="m", client=fake).complete("hi")


# --- completion behaviour ---------------------------------------------------


def test_complete_returns_plain_text(clients: list[_FakeClient]) -> None:
    llm = _build()
    clients[0].completions.response = _response("Paris is the capital of France.")
    result = llm.complete("capital of France?")
    assert result == "Paris is the capital of France."
    # Exactly a str: no provider object may cross the port boundary.
    assert type(result) is str


def test_complete_makes_exactly_one_request(clients: list[_FakeClient]) -> None:
    _build().complete("hi")
    assert len(clients[0].completions.calls) == 1


def test_complete_structured_returns_structured_data(
    clients: list[_FakeClient],
) -> None:
    llm = _build()
    clients[0].completions.response = _response('{"answer": "42", "confident": true}')
    result = llm.complete_structured("the answer?", {"type": "object"})
    assert result == {"answer": "42", "confident": True}
    assert type(result) is dict


def test_complete_structured_sends_the_supplied_schema(
    clients: list[_FakeClient],
) -> None:
    llm = _build()
    schema = {"title": "Plan", "type": "object", "properties": {"a": {"type": "string"}}}
    clients[0].completions.response = _response('{"a": "b"}')
    llm.complete_structured("prompt", schema)

    response_format = clients[0].completions.calls[0]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["schema"] == schema
    assert response_format["json_schema"]["name"] == "Plan"


def test_complete_does_not_request_a_response_format(
    clients: list[_FakeClient],
) -> None:
    _build().complete("plain text please")
    assert "response_format" not in clients[0].completions.calls[0]


# --- failure translation ----------------------------------------------------


def test_provider_failure_becomes_adapter_error(clients: list[_FakeClient]) -> None:
    llm = _build()
    clients[0].completions.error = _ProviderError("upstream is on fire")
    with pytest.raises(LLMAdapterError) as excinfo:
        llm.complete("hi")
    # The original cause is preserved for logging, but not raised to callers.
    assert isinstance(excinfo.value.__cause__, _ProviderError)


def test_structured_provider_failure_becomes_adapter_error(
    clients: list[_FakeClient],
) -> None:
    llm = _build()
    clients[0].completions.error = _ProviderError("upstream is on fire")
    with pytest.raises(LLMAdapterError):
        llm.complete_structured("hi", {"type": "object"})


@pytest.mark.parametrize(
    "response",
    [
        SimpleNamespace(choices=[]),
        _response(None),
        _response("   "),
        SimpleNamespace(),
    ],
    ids=["no-choices", "null-content", "blank-content", "malformed"],
)
def test_unusable_response_becomes_adapter_error(
    clients: list[_FakeClient], response: Any
) -> None:
    llm = _build()
    clients[0].completions.response = response
    with pytest.raises(LLMAdapterError):
        llm.complete("hi")


def test_non_json_structured_response_becomes_adapter_error(
    clients: list[_FakeClient],
) -> None:
    llm = _build()
    clients[0].completions.response = _response("sorry, I cannot do that")
    with pytest.raises(LLMAdapterError):
        llm.complete_structured("hi", {"type": "object"})


def test_non_object_structured_response_becomes_adapter_error(
    clients: list[_FakeClient],
) -> None:
    llm = _build()
    clients[0].completions.response = _response("[1, 2, 3]")
    with pytest.raises(LLMAdapterError):
        llm.complete_structured("hi", {"type": "object"})


@pytest.mark.parametrize(
    "overrides",
    [{"api_key": ""}, {"api_key": "   "}, {"model": ""}, {"timeout_seconds": 0}],
    ids=["empty-key", "blank-key", "empty-model", "non-positive-timeout"],
)
def test_invalid_configuration_is_rejected(
    clients: list[_FakeClient], overrides: dict[str, Any]
) -> None:
    with pytest.raises(LLMAdapterError):
        _build(**overrides)


@pytest.mark.parametrize("prompt", ["", "   ", None], ids=["empty", "blank", "none"])
def test_invalid_prompt_is_rejected(
    clients: list[_FakeClient], prompt: Any
) -> None:
    with pytest.raises(LLMAdapterError):
        _build().complete(prompt)


@pytest.mark.parametrize("schema", [{}, None, "not-a-mapping"], ids=["empty", "none", "str"])
def test_invalid_schema_is_rejected(
    clients: list[_FakeClient], schema: Any
) -> None:
    with pytest.raises(LLMAdapterError):
        _build().complete_structured("hi", schema)


# --- no network -------------------------------------------------------------


def test_no_network_call_is_made(
    clients: list[_FakeClient], monkeypatch: pytest.MonkeyPatch
) -> None:
    def _blocked(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("unit tests must not open a network connection")

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    assert _build().complete("hi") == "hello there"
