"""LLMPort: the contract the domain expects of a language model.

Defined here so the domain can depend on an *abstraction* of an LLM while the
concrete client (OpenAI-compatible or otherwise) lives in an outer layer and is
injected later. The signatures use only plain Python types: no OpenAI client
types, no LangChain/LangGraph types, no provider-specific response objects. A
future adapter is responsible for translating provider responses into these
plain types.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class LLMPort(Protocol):
    """Abstraction over a text-completion model.

    Implementations live in an outer layer. Phase 0 defines the shape only.
    """

    def complete(self, prompt: str) -> str:
        """Return a free-form text completion for ``prompt``."""
        ...

    def complete_structured(
        self, prompt: str, schema: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        """Return a structured completion conforming to ``schema``.

        ``schema`` is a plain, framework-agnostic description of the desired
        shape (e.g. a JSON-schema-like mapping); the return value is a plain
        mapping. Concrete adapters decide how to enforce the schema.
        """
        ...
