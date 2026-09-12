"""Tests for HTTP retry policies."""

import time
from unittest.mock import MagicMock

import httpx
import pytest

from adapters.retry_policy import with_retries
from infrastructure.config import RetryConfig


def test_with_retries_success_on_first_try():
    """Test that a successful call returns immediately without retrying."""
    config = RetryConfig(max_http_retries=2)
    mock_sleep = MagicMock()
    
    @with_retries(config, "test_op", sleep_fn=mock_sleep)
    def my_func():
        return "success"
        
    result = my_func()
    
    assert result == "success"
    mock_sleep.assert_not_called()


def test_with_retries_transient_error_eventual_success():
    """Test that transient errors are retried until success."""
    config = RetryConfig(max_http_retries=3, retry_backoff_seconds=0.1)
    mock_sleep = MagicMock()
    
    attempts = 0
    
    @with_retries(config, "test_op", sleep_fn=mock_sleep)
    def my_func():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise httpx.TimeoutException("Timeout")
        return "success"
        
    result = my_func()
    
    assert result == "success"
    assert attempts == 3
    assert mock_sleep.call_count == 2
    # First backoff 0.1, second backoff 0.2
    assert mock_sleep.call_args_list[0][0][0] == 0.1
    assert mock_sleep.call_args_list[1][0][0] == 0.2


def test_with_retries_transient_error_exhausted():
    """Test that transient errors raise after max_http_retries is reached."""
    config = RetryConfig(max_http_retries=2, retry_backoff_seconds=0.1)
    mock_sleep = MagicMock()
    
    attempts = 0
    
    @with_retries(config, "test_op", sleep_fn=mock_sleep)
    def my_func():
        nonlocal attempts
        attempts += 1
        raise httpx.NetworkError("Network down")
        
    with pytest.raises(httpx.NetworkError):
        my_func()
        
    # attempt 1 fails, sleeps. attempt 2 fails, sleeps. attempt 3 fails, raises.
    assert attempts == 3
    assert mock_sleep.call_count == 2


def test_with_retries_permanent_error_no_retry():
    """Test that permanent errors (e.g. 403 Forbidden) are not retried."""
    config = RetryConfig(max_http_retries=2)
    mock_sleep = MagicMock()
    
    attempts = 0
    
    @with_retries(config, "test_op", sleep_fn=mock_sleep)
    def my_func():
        nonlocal attempts
        attempts += 1
        response = httpx.Response(403)
        request = httpx.Request("GET", "https://test")
        raise httpx.HTTPStatusError("Forbidden", request=request, response=response)
        
    with pytest.raises(httpx.HTTPStatusError):
        my_func()
        
    assert attempts == 1
    mock_sleep.assert_not_called()


def test_with_retries_rate_limit_uses_header():
    """Test that 429 Rate Limit uses Retry-After header if present."""
    config = RetryConfig(max_http_retries=2, rate_limit_backoff_seconds=2.0)
    mock_sleep = MagicMock()
    
    attempts = 0
    
    @with_retries(config, "test_op", sleep_fn=mock_sleep)
    def my_func():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            response = httpx.Response(429, headers={"Retry-After": "1.5"})
            request = httpx.Request("GET", "https://test")
            raise httpx.HTTPStatusError("Rate Limit", request=request, response=response)
        return "success"
        
    result = my_func()
    
    assert result == "success"
    assert attempts == 2
    mock_sleep.assert_called_once_with(1.5)


def test_with_retries_unexpected_exception():
    """Test that unexpected exceptions bypass retries."""
    config = RetryConfig(max_http_retries=2)
    mock_sleep = MagicMock()
    
    attempts = 0
    
    @with_retries(config, "test_op", sleep_fn=mock_sleep)
    def my_func():
        nonlocal attempts
        attempts += 1
        raise ValueError("Bad internal state")
        
    with pytest.raises(ValueError):
        my_func()
        
    assert attempts == 1
    mock_sleep.assert_not_called()
