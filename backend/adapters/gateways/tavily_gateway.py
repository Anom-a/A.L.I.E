"""Tavily implementation of the domain's :class:`SearchToolPort`.

A pure translation boundary:

    Tavily response  ->  domain Citation  ->  domain Evidence

It takes a domain :class:`SubQuestion` in and hands domain :class:`Evidence`
back; no Tavily payload, client, or exception escapes this module. There is no
retry, fallback, routing, or re-ranking here — one sub-question means exactly
one Tavily request, and Tavily's own result order is preserved.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Optional, Sequence
from urllib.parse import urlparse
from uuid import NAMESPACE_URL, uuid5

from tavily import TavilyClient

from adapters.exceptions import SearchGatewayError
from domain.entities.citation import Citation
from domain.entities.evidence import Evidence, SourceType
from domain.entities.sub_question import SubQuestion
from domain.ports.search_tool_port import SearchToolPort

#: Used when the caller does not supply a timeout.
DEFAULT_TIMEOUT_SECONDS: float = 20.0
#: How many results to ask Tavily for in a single search.
DEFAULT_MAX_RESULTS: int = 5


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TavilyGateway:
    """:class:`SearchToolPort` backed by the Tavily web-search API."""

    def __init__(
        self,
        *,
        api_key: str,
        max_results: int = DEFAULT_MAX_RESULTS,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        client: Optional[Any] = None,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        """Configure the gateway.

        Args:
            api_key: Tavily credential. Comes from configuration.
            max_results: Results requested per search.
            timeout_seconds: Upper bound for the single search request.
            client: Pre-built client, used instead of constructing one. Exists
                for testing and for callers that manage the client themselves.
            clock: Source of the retrieval timestamp recorded in citations.
        """
        if not api_key or not api_key.strip():
            raise SearchGatewayError("api_key must not be empty")
        if max_results <= 0:
            raise SearchGatewayError("max_results must be greater than 0")
        if timeout_seconds <= 0:
            raise SearchGatewayError("timeout_seconds must be greater than 0")

        self._max_results = int(max_results)
        self._timeout_seconds = float(timeout_seconds)
        self._clock = clock if clock is not None else _utc_now
        # The key is handed straight to the client and never stored on self.
        self._client = client if client is not None else TavilyClient(api_key=api_key)

    def search(self, sub_question: SubQuestion) -> list[Evidence]:
        """Run one Tavily search for ``sub_question`` and return domain evidence."""
        if not isinstance(sub_question, SubQuestion):
            raise SearchGatewayError(
                f"search() expects a SubQuestion, got {type(sub_question).__name__}"
            )
        payload = self._request(sub_question.text)
        return self._to_evidence(sub_question, payload)

    def _request(self, query: str) -> Any:
        """Issue the single search request, wrapping any provider failure."""
        try:
            return self._client.search(
                query=query,
                max_results=self._max_results,
                timeout=self._timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001 - deliberate boundary
            # Broad on purpose: this is the translation boundary. Whatever the
            # SDK or transport raises, callers only ever see SearchGatewayError.
            raise SearchGatewayError(
                f"Tavily search failed: {type(exc).__name__}: {exc}"
            ) from exc

    def _to_evidence(
        self, sub_question: SubQuestion, payload: Any
    ) -> list[Evidence]:
        """Translate a Tavily payload into domain objects.

        The payload stops here: only :class:`Evidence` leaves the adapter.
        """
        if not isinstance(payload, Mapping):
            raise SearchGatewayError(
                f"Tavily returned an unexpected payload of type {type(payload).__name__}"
            )
        results = payload.get("results")
        if results is None:
            return []
        if not isinstance(results, Sequence) or isinstance(results, (str, bytes)):
            raise SearchGatewayError("Tavily 'results' was not a list")

        # One request, one retrieval moment: every citation shares it.
        retrieved_at = self._clock()

        evidence: list[Evidence] = []
        for result in results:
            if not isinstance(result, Mapping):
                continue
            url = str(result.get("url") or "").strip()
            content = str(result.get("content") or "").strip()
            # The domain forbids empty content/URLs; a result missing either
            # carries no usable provenance, so it is dropped rather than
            # allowed to fail the whole search.
            if not url or not content:
                continue
            title = str(result.get("title") or "").strip()
            evidence.append(
                Evidence(
                    id=_evidence_id(sub_question, url),
                    sub_question_id=sub_question.id,
                    source_type=SourceType.WEB,
                    content=content,
                    citation=Citation(
                        source_url_or_id=url,
                        source_name=title or _host_of(url) or url,
                        retrieved_at=retrieved_at,
                    ),
                )
            )
        return evidence


def _evidence_id(sub_question: SubQuestion, url: str):
    """Derive a stable evidence id from the sub-question and the source URL.

    UUIDv5 is deterministic, so re-running the same search for the same
    sub-question yields the same ids for the same sources instead of a fresh
    random id each time.
    """
    return uuid5(NAMESPACE_URL, f"{sub_question.id}|{url}")


def _host_of(url: str) -> str:
    """Return the host of ``url``, used as a fallback source name."""
    try:
        return urlparse(url).netloc
    except ValueError:
        return ""
