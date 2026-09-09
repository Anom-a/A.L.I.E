"""Tests for the domain ports (Protocol interfaces).

These verify the *contract*: that each port is a Protocol exposing the expected
method names and parameters. We intentionally do not build fake adapters — the
ports have no behaviour to exercise in Phase 0. A single minimal structural
check per port confirms the runtime_checkable contract is usable for dependency
inversion in later phases.
"""

from __future__ import annotations

import inspect

from domain.ports.job_repository_port import ResearchJobRepositoryPort
from domain.ports.llm_port import LLMPort
from domain.ports.search_tool_port import SearchToolPort


def _params(func: object) -> list[str]:
    return [p for p in inspect.signature(func).parameters if p != "self"]  # type: ignore[arg-type]


def test_ports_are_protocols() -> None:
    for port in (LLMPort, SearchToolPort, ResearchJobRepositoryPort):
        assert getattr(port, "_is_protocol", False) is True


def test_ports_are_runtime_checkable() -> None:
    for port in (LLMPort, SearchToolPort, ResearchJobRepositoryPort):
        assert getattr(port, "_is_runtime_protocol", False) is True


def test_llm_port_signature() -> None:
    assert hasattr(LLMPort, "complete")
    assert hasattr(LLMPort, "complete_structured")
    assert _params(LLMPort.complete) == ["prompt"]
    assert _params(LLMPort.complete_structured) == ["prompt", "schema"]


def test_search_tool_port_signature() -> None:
    assert hasattr(SearchToolPort, "search")
    assert _params(SearchToolPort.search) == ["sub_question"]


def test_job_repository_port_signature() -> None:
    assert hasattr(ResearchJobRepositoryPort, "add")
    assert hasattr(ResearchJobRepositoryPort, "get")
    assert hasattr(ResearchJobRepositoryPort, "update_status")
    assert _params(ResearchJobRepositoryPort.add) == ["query"]
    assert _params(ResearchJobRepositoryPort.get) == ["query_id"]
    assert _params(ResearchJobRepositoryPort.update_status) == ["query_id", "status"]


def test_llm_port_structural_conformance() -> None:
    class _Conforming:
        def complete(self, prompt: str) -> str:
            return ""

        def complete_structured(self, prompt: str, schema: dict) -> dict:
            return {}

    class _NotConforming:
        pass

    assert isinstance(_Conforming(), LLMPort)
    assert not isinstance(_NotConforming(), LLMPort)


def test_search_tool_port_structural_conformance() -> None:
    class _Conforming:
        def search(self, sub_question: object) -> list:
            return []

    assert isinstance(_Conforming(), SearchToolPort)
    assert not isinstance(object(), SearchToolPort)


def test_job_repository_port_structural_conformance() -> None:
    class _Conforming:
        def add(self, query: object) -> None: ...
        def get(self, query_id: object) -> object: ...
        def update_status(self, query_id: object, status: object) -> None: ...

    assert isinstance(_Conforming(), ResearchJobRepositoryPort)
    assert not isinstance(object(), ResearchJobRepositoryPort)
