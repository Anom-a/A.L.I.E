"""HTTP retry policies and rate-limit handling for external gateways.

This module provides a pure-function approach to wrapping HTTP operations
with bounded exponential backoff, rate-limit backoffs, and structured logging.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, TypeVar

import httpx
import requests

from infrastructure.config import RetryConfig

T = TypeVar("T")

logger = logging.getLogger("adapters")


def with_retries(
    config: RetryConfig,
    operation_name: str,
    job_id: str = "unknown",
    sub_question_id: str = "unknown",
    tool: str = "unknown",
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Callable[[Callable[[], T]], T]:
    """Return a decorator that executes a callable with retries.

    Handles transient httpx errors (Timeouts, Network errors, 5xx) and
    rate limits (429). Permanent errors (400, 401, 403, 404, etc.) are
    raised immediately without retry.
    """

    def decorator(func: Callable[[], T]) -> Callable[[], T]:
        def wrapper() -> T:
            attempt = 1
            max_attempts = config.max_http_retries + 1
            
            while attempt <= max_attempts:
                start_time = time.monotonic()
            error_category = "none"
            http_status = None
            succeeded = False
            
            try:
                result = func()
                succeeded = True
                
                # Log success
                latency_ms = int((time.monotonic() - start_time) * 1000)
                logger.info(
                    f"{tool} operation succeeded",
                    extra={
                        "job_id": str(job_id),
                        "sub_question_id": str(sub_question_id),
                        "tool": tool,
                        "operation": operation_name,
                        "succeeded": True,
                        "fallback_used": False,
                        "latency_ms": latency_ms,
                        "attempt": attempt,
                        "error_category": error_category,
                        "http_status": http_status,
                    },
                )
                return result

            except Exception as exc:
                # Duck-type HTTP exceptions (httpx, requests, openai)
                http_status = None
                headers = {}
                is_timeout = False
                is_network_error = False
                is_http_status_error = False
                
                # Check for OpenAI, HTTPX, Requests status errors
                if hasattr(exc, "response") and hasattr(exc.response, "status_code"):
                    http_status = exc.response.status_code
                    headers = getattr(exc.response, "headers", {})
                    is_http_status_error = True
                elif hasattr(exc, "status_code"):
                    http_status = getattr(exc, "status_code")
                    headers = getattr(exc, "headers", {})
                    is_http_status_error = True
                    
                # Check for timeouts and network errors
                exc_type_name = type(exc).__name__.lower()
                if "timeout" in exc_type_name:
                    is_timeout = True
                elif "network" in exc_type_name or "connection" in exc_type_name or "connecterror" in exc_type_name:
                    is_network_error = True

                if is_http_status_error and http_status is not None:
                    # 429 Rate Limit
                    if http_status == 429:
                        error_category = "rate_limit"
                        if attempt >= max_attempts:
                            _log_failure(
                                start_time, tool, operation_name, job_id,
                                sub_question_id, attempt, error_category, http_status
                            )
                            raise
                            
                        retry_after = headers.get("Retry-After")
                        delay = config.rate_limit_backoff_seconds
                        
                        if retry_after is not None:
                            try:
                                parsed = float(retry_after)
                                if 0 <= parsed <= config.max_retry_backoff_seconds * 2:
                                    delay = parsed
                            except ValueError:
                                pass
                                
                        _log_failure(
                            start_time, tool, operation_name, job_id,
                            sub_question_id, attempt, error_category, http_status
                        )
                        sleep_fn(delay)
                        
                    # 5xx Server Error
                    elif http_status >= 500:
                        error_category = "server_error"
                        if attempt >= max_attempts:
                            _log_failure(
                                start_time, tool, operation_name, job_id,
                                sub_question_id, attempt, error_category, http_status
                            )
                            raise
                            
                        delay = min(
                            config.retry_backoff_seconds * (2 ** (attempt - 1)),
                            config.max_retry_backoff_seconds
                        )
                        _log_failure(
                            start_time, tool, operation_name, job_id,
                            sub_question_id, attempt, error_category, http_status
                        )
                        sleep_fn(delay)
                        
                    # Permanent Error (4xx other than 429)
                    else:
                        error_category = "permanent_error"
                        _log_failure(
                            start_time, tool, operation_name, job_id,
                            sub_question_id, attempt, error_category, http_status
                        )
                        raise

                elif is_timeout or is_network_error:
                    error_category = "timeout" if is_timeout else "network_error"
                    if attempt >= max_attempts:
                        _log_failure(
                            start_time, tool, operation_name, job_id,
                            sub_question_id, attempt, error_category, http_status
                        )
                        raise
                        
                    delay = min(
                        config.retry_backoff_seconds * (2 ** (attempt - 1)),
                        config.max_retry_backoff_seconds
                    )
                    _log_failure(
                        start_time, tool, operation_name, job_id,
                        sub_question_id, attempt, error_category, http_status
                    )
                    sleep_fn(delay)
                    
                else:
                    # Unexpected exceptions
                    error_category = "unexpected_error"
                    _log_failure(
                        start_time, tool, operation_name, job_id,
                        sub_question_id, attempt, error_category, http_status
                    )
                    raise
                
            attempt += 1

            raise RuntimeError("Unreachable")
            
        return wrapper
        
    return decorator


def _log_failure(
    start_time: float,
    tool: str,
    operation_name: str,
    job_id: str,
    sub_question_id: str,
    attempt: int,
    error_category: str,
    http_status: int | None,
) -> None:
    latency_ms = int((time.monotonic() - start_time) * 1000)
    logger.warning(
        f"{tool} operation failed",
        extra={
            "job_id": str(job_id),
            "sub_question_id": str(sub_question_id),
            "tool": tool,
            "operation": operation_name,
            "succeeded": False,
            "fallback_used": False,
            "latency_ms": latency_ms,
            "attempt": attempt,
            "error_category": error_category,
            "http_status": http_status,
        },
    )
