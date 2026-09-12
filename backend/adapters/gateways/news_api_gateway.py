"""NewsAPI implementation of the domain's :class:`SearchToolPort`.

A pure translation boundary:

    NewsAPI response  ->  domain Citation  ->  domain Evidence
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

#: Default base URL for NewsAPI.
DEFAULT_BASE_URL: str = "https://newsapi.org/v2"
#: How many results to request in a single search.
DEFAULT_MAX_RESULTS: int = 5
#: Timeout in seconds for a single search request.
DEFAULT_TIMEOUT_SECONDS: float = 20.0


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NewsApiGateway:
    """:class:`SearchToolPort` backed by NewsAPI.ai."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        max_results: int = DEFAULT_MAX_RESULTS,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        client: Optional[httpx.Client] = None,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        """Configure the gateway.

        Args:
            api_key: Required API key for NewsAPI.
            base_url: Root URL for the API (no trailing slash).
            max_results: Results requested per search.
            timeout_seconds: Upper bound for the single search request.
            client: Pre-built :class:`httpx.Client`, used instead of
                constructing one.
            clock: Source of the retrieval timestamp recorded in citations.
        """
        if not api_key or not api_key.strip():
            raise SearchGatewayError("api_key must not be empty")
        if not base_url or not base_url.strip():
            raise SearchGatewayError("base_url must not be empty")
        if max_results <= 0:
            raise SearchGatewayError("max_results must be greater than 0")
        if timeout_seconds <= 0:
            raise SearchGatewayError("timeout_seconds must be greater than 0")

        self._api_key = api_key.strip()
        self._base_url = base_url.rstrip("/")
        self._max_results = int(max_results)
        self._timeout_seconds = float(timeout_seconds)
        self._clock = clock if clock is not None else _utc_now

        self._client = client if client is not None else httpx.Client(
            headers={"X-Api-Key": self._api_key},
            timeout=self._timeout_seconds,
        )

    def search(self, sub_question: SubQuestion) -> list[Evidence]:
        """Run one NewsAPI search for ``sub_question`` and return domain evidence."""
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
                f"{self._base_url}/everything",
                headers={"X-Api-Key": self._api_key},
                params={
                    "q": query,
                    "pageSize": self._max_results,
                    "language": "en",
                    "sortBy": "relevancy",
                },
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001 - deliberate boundary
            raise SearchGatewayError(
                f"NewsAPI search failed: {type(exc).__name__}: {exc}"
            ) from exc

    def _to_evidence(
        self, sub_question: SubQuestion, payload: Any
    ) -> list[Evidence]:
        """Translate a NewsAPI payload into domain objects."""
        if not isinstance(payload, Mapping):
            raise SearchGatewayError(
                f"NewsAPI returned an unexpected payload of type {type(payload).__name__}"
            )
        results = payload.get("articles")
        if results is None:
            return []
        if not isinstance(results, Sequence) or isinstance(results, (str, bytes)):
            raise SearchGatewayError("NewsAPI 'articles' was not a list")

        retrieved_at = self._clock()
        evidence: list[Evidence] = []
        
        for result in results:
            if not isinstance(result, Mapping):
                continue
            
            url = str(result.get("url") or "").strip()
            
            source_dict = result.get("source") or {}
            source_name = "Unknown News Source"
            if isinstance(source_dict, Mapping):
                source_name = str(source_dict.get("name") or "").strip() or source_name
                
            title = str(result.get("title") or "").strip()
            description = str(result.get("description") or "").strip()
            content = str(result.get("content") or "").strip()
            published_at = str(result.get("publishedAt") or "").strip()
            
            if not url:
                continue
                
            # Prefer content, fallback to description, fallback to title
            final_content = content or description or title
            if not final_content:
                continue
                
            if published_at:
                final_content = f"Published: {published_at}\n\n{final_content}"
                source_name = f"{source_name} ({published_at[:10]})"
                
            evidence.append(
                Evidence(
                    id=_evidence_id(sub_question, url),
                    sub_question_id=sub_question.id,
                    source_type=SourceType.DOCUMENTATION,
                    content=final_content,
                    citation=Citation(
                        source_url_or_id=url,
                        source_name=source_name,
                        retrieved_at=retrieved_at,
                    ),
                )
            )
        return evidence


def _evidence_id(sub_question: SubQuestion, url: str):
    """Derive a stable evidence id from the sub-question and the source URL."""
    return uuid5(NAMESPACE_URL, f"{sub_question.id}|{url}")
