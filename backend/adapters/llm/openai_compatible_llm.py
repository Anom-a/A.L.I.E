"""OpenAI-compatible implementation of the domain's :class:`LLMPort`.

This module is the *only* place in the codebase that knows the OpenAI SDK
exists. It accepts plain configuration values through its constructor (never
reading the environment itself), and returns plain ``str``/``dict`` values, so
no provider object, exception, or type ever crosses back into the domain.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping, Optional

from openai import OpenAI

from adapters.retry_policy import with_retries
from infrastructure.config import RetryConfig

#: Used when the caller does not supply a timeout.
DEFAULT_TIMEOUT_SECONDS: float = 20.0

# Phase 1 has no retry policy, so the SDK's built-in retries are switched off:
# one call to `complete()` means exactly one request, and the configured
# timeout is the real upper bound on how long it can take.
_MAX_RETRIES = 0

_UNSAFE_SCHEMA_NAME = re.compile(r"[^A-Za-z0-9_-]")


class LLMAdapterError(RuntimeError):
    """Raised when the provider fails or returns an unusable response.

    Every provider-side failure is translated into this adapter-level error so
    callers never have to catch (or import) an SDK exception type.
    """


class OpenAICompatibleLLM:
    """:class:`LLMPort` backed by any OpenAI-compatible chat-completions API.

    The provider is not hardcoded: point ``base_url`` at OpenAI, a local
    llama.cpp/vLLM/Ollama server, OpenRouter, Groq, … and supply the matching
    ``model``. Both come from configuration.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: Optional[str] = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        retry_config: Optional[RetryConfig] = None,
        client: Optional[Any] = None,
    ) -> None:
        """Configure the adapter.

        Args:
            api_key: Credential for the endpoint. Comes from configuration.
            model: Model identifier to request. Comes from configuration.
            base_url: OpenAI-compatible endpoint; ``None`` uses the SDK default.
            timeout_seconds: Upper bound for a single request.
            client: Pre-built client, used instead of constructing one. Exists
                for testing and for callers that manage the client themselves.
        """
        if not api_key or not api_key.strip():
            raise LLMAdapterError("api_key must not be empty")
        if not model or not model.strip():
            raise LLMAdapterError("model must not be empty")
        if timeout_seconds <= 0:
            raise LLMAdapterError("timeout_seconds must be greater than 0")

        self._model = model
        self._timeout_seconds = float(timeout_seconds)
        self._retry_config = retry_config or RetryConfig()
        # The key is handed straight to the client and never stored on self.
        self._client = (
            client
            if client is not None
            else OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=self._timeout_seconds,
                max_retries=_MAX_RETRIES,
            )
        )

    def complete(self, prompt: str) -> str:
        """Return a free-form text completion for ``prompt``."""
        response = self._create(prompt)
        return self._text_of(response)

    def complete_structured(
        self, prompt: str, schema: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        """Return a completion parsed into a plain ``dict`` following ``schema``.

        ``schema`` is a JSON-Schema-like mapping. It is passed to the provider
        as a ``json_schema`` response format and the returned JSON object is
        decoded into ordinary Python types.
        """
        if not isinstance(schema, Mapping) or not schema:
            raise LLMAdapterError("schema must be a non-empty mapping")

        # Many OpenAI-compatible proxies (like Novita) do not support the
        # structured outputs feature (`response_format={"type": "json_schema"}`).
        # Therefore, we inject the schema requirement directly into the prompt.
        augmented_prompt = (
            f"{prompt}\n\n"
            f"IMPORTANT: You must return ONLY a JSON object that perfectly matches "
            f"the following JSON Schema. Do not include any conversational text "
            f"before or after the JSON.\n"
            f"CRITICAL: Do NOT wrap the JSON in any root-level keys based on the schema's title. "
            f"Your output should start immediately with the keys defined in the schema's properties.\n\n"
            f"{json.dumps(dict(schema), indent=2)}"
        )

        response = self._create(augmented_prompt)
        text = self._text_of(response)
        # Strip markdown fences if the model included them
        clean_text = text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        
        try:
            data = json.loads(clean_text)
        except ValueError as exc:
            import logging
            logging.getLogger("application").error(f"LLM structured response was not valid JSON. Response text: {text!r}")
            raise LLMAdapterError(
                f"LLM structured response was not valid JSON. Response text: {text!r}"
            ) from exc
        if not isinstance(data, dict):
            raise LLMAdapterError(
                f"LLM structured response was not a JSON object, got {type(data).__name__}"
            )
        return data

    def _create(self, prompt: str, **extra: Any) -> Any:
        """Issue one chat-completion request, wrapping any provider failure."""
        if not isinstance(prompt, str) or not prompt.strip():
            raise LLMAdapterError("prompt must be a non-empty string")
            
        @with_retries(
            config=self._retry_config,
            operation_name="chat_completion",
            tool="openai",
        )
        def _do_create():
            return self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                timeout=self._timeout_seconds,
                **extra,
            )
            
        try:
            return _do_create()
        except Exception as exc:  # noqa: BLE001 - deliberate boundary
            # Broad on purpose: this is the translation boundary. Whatever the
            # SDK or transport raises, callers only ever see LLMAdapterError.
            raise LLMAdapterError(
                f"LLM request failed: {type(exc).__name__}: {exc}"
            ) from exc

    @staticmethod
    def _text_of(response: Any) -> str:
        """Pull the plain text out of a provider response object.

        The response object itself stops here — only ``str`` leaves the adapter.
        """
        choices = getattr(response, "choices", None)
        if not choices:
            raise LLMAdapterError("LLM response contained no choices")
        content = getattr(getattr(choices[0], "message", None), "content", None)
        if not isinstance(content, str) or not content.strip():
            raise LLMAdapterError("LLM response contained no text content")
        return content


def _schema_name(schema: Mapping[str, Any]) -> str:
    """Derive a provider-safe name for the response format from ``schema``."""
    raw = str(schema.get("title") or "response")
    cleaned = _UNSAFE_SCHEMA_NAME.sub("_", raw).strip("_")
    return cleaned or "response"
