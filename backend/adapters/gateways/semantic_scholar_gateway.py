"""Semantic Scholar implementation of the domain's :class:`SearchToolPort`.

A pure translation boundary:

    Semantic Scholar API response  ->  domain Citation  ->  domain Evidence

It takes a domain :class:`SubQuestion` in and hands domain :class:`Evidence`
back; no Semantic Scholar payload, HTTP detail, or exception escapes this module.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Optional, Sequence
from uuid import NAMESPACE_URL, uuid5

import httpx

from domain.entities.citation import Citation
from domain.entities.evidence import Evidence, SourceType
from domain.entities.sub_question import SubQuestion
from adapters.retry_policy import with_retries
from infrastructure.config import RetryConfig

from adapters.exceptions import SearchGatewayError

#: Default base URL for the Semantic Scholar Graph API.
DEFAULT_BASE_URL: str = "https://api.semanticscholar.org/graph/v1"
#: How many results to request in a single search.
DEFAULT_MAX_RESULTS: int = 5
#: Timeout in seconds for a single search request.
DEFAULT_TIMEOUT_SECONDS: float = 20.0


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SemanticScholarGateway:
    """:class:`SearchToolPort` backed by the Semantic Scholar Graph API."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        max_results: int = DEFAULT_MAX_RESULTS,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        retry_config: Optional[RetryConfig] = None,
        client: Optional[httpx.Client] = None,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        """Configure the gateway.

        Args:
            api_key: Optional API key for higher rate limits.
            base_url: Root URL for the API (no trailing slash).
            max_results: Results requested per search.
            timeout_seconds: Upper bound for the single search request.
            client: Pre-built :class:`httpx.Client`, used instead of
                constructing one.
            clock: Source of the retrieval timestamp recorded in citations.
        """
        if not base_url or not base_url.strip():
            raise SearchGatewayError("base_url must not be empty")
        if max_results <= 0:
            raise SearchGatewayError("max_results must be greater than 0")
        if timeout_seconds <= 0:
            raise SearchGatewayError("timeout_seconds must be greater than 0")

        self._api_key = api_key.strip() if api_key else None
        self._base_url = base_url.rstrip("/")
        self._max_results = int(max_results)
        self._timeout_seconds = float(timeout_seconds)
        self._clock = clock if clock is not None else _utc_now
        self._retry_config = retry_config or RetryConfig()

        headers = {}
        if self._api_key:
            headers["x-api-key"] = self._api_key

        self._client = client if client is not None else httpx.Client(
            headers=headers,
            timeout=self._timeout_seconds,
        )

    def search(self, sub_question: SubQuestion) -> list[Evidence]:
        """Run one Semantic Scholar search for ``sub_question`` and return domain evidence."""
        if not isinstance(sub_question, SubQuestion):
            raise SearchGatewayError(
                f"search() expects a SubQuestion, got {type(sub_question).__name__}"
            )
        payload = self._request(sub_question)
        return self._to_evidence(sub_question, payload)

    def _request(self, sub_question: SubQuestion) -> Any:
        """Issue the single search request, wrapping any provider failure."""
        @with_retries(
            config=self._retry_config,
            operation_name="search",
            job_id=str(sub_question.research_query_id),
            sub_question_id=str(sub_question.id),
            tool="semantic_scholar",
        )
        def _do_search():
            headers = {}
            if self._api_key:
                headers["x-api-key"] = self._api_key
            
            response = self._client.get(
                f"{self._base_url}/paper/search",
                headers=headers,
                params={
                    "query": sub_question.text,
                    "limit": self._max_results,
                    "fields": "title,url,abstract",
                },
            )
            response.raise_for_status()
            return response.json()

        try:
            return _do_search()
        except Exception as exc:  # noqa: BLE001 - deliberate boundary
            raise SearchGatewayError(
                f"Semantic Scholar search failed: {type(exc).__name__}: {exc}"
            ) from exc

    def _to_evidence(
        self, sub_question: SubQuestion, payload: Any
    ) -> list[Evidence]:
        """Translate a Semantic Scholar payload into domain objects."""
        if not isinstance(payload, Mapping):
            raise SearchGatewayError(
                f"Semantic Scholar returned an unexpected payload of type {type(payload).__name__}"
            )
        results = payload.get("data")
        if results is None:
            return []
        if not isinstance(results, Sequence) or isinstance(results, (str, bytes)):
            raise SearchGatewayError("Semantic Scholar 'data' was not a list")

        retrieved_at = self._clock()
        evidence: list[Evidence] = []
        
        for result in results:
            if not isinstance(result, Mapping):
                continue
            
            paper_id = str(result.get("paperId") or "").strip()
            url = str(result.get("url") or "").strip()
            if not url and paper_id:
                url = f"https://www.semanticscholar.org/paper/{paper_id}"
                
            title = str(result.get("title") or "").strip()
            abstract = str(result.get("abstract") or "").strip()
            
            if not url or not abstract:
                continue
                
            evidence.append(
                Evidence(
                    id=_evidence_id(sub_question, url),
                    sub_question_id=sub_question.id,
                    source_type=SourceType.DOCUMENTATION,
                    content=abstract,
                    citation=Citation(
                        source_url_or_id=url,
                        source_name="Semantic Scholar",
                        retrieved_at=retrieved_at,
                    ),
                )
            )
        return evidence


def _evidence_id(sub_question: SubQuestion, url: str):
    """Derive a stable evidence id from the sub-question and the source URL."""
    return uuid5(NAMESPACE_URL, f"{sub_question.id}|{url}")
