"""iFixit implementation of the domain's :class:`SearchToolPort`.

A pure translation boundary:

    iFixit API response  ->  domain Citation  ->  domain Evidence

It takes a domain :class:`SubQuestion` in and hands domain :class:`Evidence`
back; no iFixit payload, HTTP detail, or exception escapes this module.  There
is no retry, fallback, routing, or re-ranking here — one sub-question means
exactly one iFixit request, and iFixit's own result order is preserved.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Optional, Sequence
from uuid import NAMESPACE_URL, uuid5

import httpx

from domain.entities.citation import Citation
from domain.entities.evidence import Evidence, SourceType
from domain.entities.sub_question import SubQuestion

from adapters.exceptions import SearchGatewayError

#: Default base URL for the iFixit public API v2.0.
DEFAULT_BASE_URL: str = "https://www.ifixit.com/api/2.0"
#: How many results to request in a single search.
DEFAULT_MAX_RESULTS: int = 5
#: Timeout in seconds for a single search request.
DEFAULT_TIMEOUT_SECONDS: float = 20.0


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IFixitGateway:
    """:class:`SearchToolPort` backed by the iFixit public search API."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        max_results: int = DEFAULT_MAX_RESULTS,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        client: Optional[httpx.Client] = None,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        """Configure the gateway.

        Args:
            base_url: Root URL for the iFixit API (no trailing slash).
            max_results: Results requested per search.
            timeout_seconds: Upper bound for the single search request.
            client: Pre-built :class:`httpx.Client`, used instead of
                constructing one.  Exists for testing and for callers that
                manage the client themselves.
            clock: Source of the retrieval timestamp recorded in citations.
        """
        if not base_url or not base_url.strip():
            raise SearchGatewayError("base_url must not be empty")
        if max_results <= 0:
            raise SearchGatewayError("max_results must be greater than 0")
        if timeout_seconds <= 0:
            raise SearchGatewayError("timeout_seconds must be greater than 0")

        self._base_url = base_url.rstrip("/")
        self._max_results = int(max_results)
        self._timeout_seconds = float(timeout_seconds)
        self._clock = clock if clock is not None else _utc_now
        self._client = client if client is not None else httpx.Client(
            timeout=self._timeout_seconds,
        )

    def search(self, sub_question: SubQuestion) -> list[Evidence]:
        """Run one iFixit search for ``sub_question`` and return domain evidence."""
        if not isinstance(sub_question, SubQuestion):
            raise SearchGatewayError(
                f"search() expects a SubQuestion, got {type(sub_question).__name__}"
            )
        payload = self._request(sub_question.text)
        return self._to_evidence(sub_question, payload)

    def _request(self, query: str) -> Any:
        """Issue the single search request, wrapping any provider failure."""
        try:
            response = self._client.get(
                f"{self._base_url}/search/{query}",
                params={"limit": self._max_results},
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001 - deliberate boundary
            raise SearchGatewayError(
                f"iFixit search failed: {type(exc).__name__}: {exc}"
            ) from exc

    def _to_evidence(
        self, sub_question: SubQuestion, payload: Any
    ) -> list[Evidence]:
        """Translate an iFixit payload into domain objects.

        The payload stops here: only :class:`Evidence` leaves the adapter.
        """
        if not isinstance(payload, Mapping):
            raise SearchGatewayError(
                f"iFixit returned an unexpected payload of type {type(payload).__name__}"
            )
        results = payload.get("results")
        if results is None:
            return []
        if not isinstance(results, Sequence) or isinstance(results, (str, bytes)):
            raise SearchGatewayError("iFixit 'results' was not a list")

        retrieved_at = self._clock()

        evidence: list[Evidence] = []
        for result in results:
            if not isinstance(result, Mapping):
                continue
            url = str(result.get("url") or "").strip()
            title = str(result.get("title") or "").strip()
            # iFixit guides have "summary" rather than "content".
            content = str(result.get("summary") or "").strip()
            if not url or not content:
                continue
            evidence.append(
                Evidence(
                    id=_evidence_id(sub_question, url),
                    sub_question_id=sub_question.id,
                    source_type=SourceType.DOCUMENTATION,
                    content=content,
                    citation=Citation(
                        source_url_or_id=url,
                        source_name=title or url,
                        retrieved_at=retrieved_at,
                    ),
                )
            )
        return evidence


def _evidence_id(sub_question: SubQuestion, url: str):
    """Derive a stable evidence id from the sub-question and the source URL.

    UUIDv5 is deterministic, so re-running the same search for the same
    sub-question yields the same ids for the same sources.
    """
    return uuid5(NAMESPACE_URL, f"{sub_question.id}|{url}")
