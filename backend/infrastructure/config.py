"""Process configuration for the outermost (frameworks & drivers) layer.

Configuration is read here and *only* here. Adapters receive plain values
through their constructors, so nothing inner than this module ever touches
``os.environ`` or a ``.env`` file — that keeps the domain and the adapters
independent of how the process happens to be configured.

The approach is deliberately small: frozen dataclasses plus a few loader
functions. No settings framework, no validation library, no global singleton.

Local development uses a ``.env`` file loaded through ``python-dotenv``; real
environment variables always win over the file, so deployments can just set
variables. ``.env`` is git-ignored and must never be committed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Mapping, Optional

from dotenv import load_dotenv

#: Fallback when ``REQUEST_TIMEOUT_SECONDS`` is not set.
DEFAULT_REQUEST_TIMEOUT_SECONDS: float = 20.0

#: Fallback when ``MAX_SUBQUESTIONS`` is not set.
DEFAULT_MAX_SUBQUESTIONS: int = 5

ENV_OPENAI_API_KEY = "OPENAI_API_KEY"
ENV_OPENAI_BASE_URL = "OPENAI_BASE_URL"
ENV_OPENAI_MODEL_PLANNER = "OPENAI_MODEL_PLANNER"
ENV_TAVILY_API_KEY = "TAVILY_API_KEY"
ENV_REQUEST_TIMEOUT_SECONDS = "REQUEST_TIMEOUT_SECONDS"
ENV_MAX_SUBQUESTIONS = "MAX_SUBQUESTIONS"
ENV_MAX_RETRIEVAL_LOOPS = "MAX_RETRIEVAL_LOOPS"

#: Fallback when ``MAX_RETRIEVAL_LOOPS`` is not set.
DEFAULT_MAX_RETRIEVAL_LOOPS: int = 3


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or malformed.

    Deliberately not a ``DomainError``: a misconfigured process is an
    infrastructure problem, not a violated business rule.
    """


@dataclass(frozen=True)
class LLMConfig:
    """Everything needed to talk to an OpenAI-compatible endpoint."""

    api_key: str
    model: str
    base_url: Optional[str] = None
    timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS


@dataclass(frozen=True)
class SearchConfig:
    """Everything needed to talk to the web-search provider."""

    api_key: str
    timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS


@dataclass(frozen=True)
class PlannerConfig:
    """Bounds the planning use case; injected into it as a plain value."""

    max_subquestions: int = DEFAULT_MAX_SUBQUESTIONS


@dataclass(frozen=True)
class GraphConfig:
    """Bounds the research graph loops; injected into it as a plain value."""

    max_retrieval_loops: int = DEFAULT_MAX_RETRIEVAL_LOOPS


@dataclass(frozen=True)
class AppConfig:
    """All configuration the process needs so far."""

    llm: LLMConfig
    search: SearchConfig
    planner: PlannerConfig = field(default_factory=PlannerConfig)
    graph: GraphConfig = field(default_factory=GraphConfig)


def load_env_file(path: Optional[str] = None) -> None:
    """Load a local ``.env`` into the process environment, if one exists.

    Existing environment variables are never overwritten, so an explicitly
    exported variable always beats the file. Safe to call more than once, and a
    no-op when no ``.env`` is present (as in CI).
    """
    load_dotenv(dotenv_path=path, override=False)


def _source(env: Optional[Mapping[str, str]]) -> Mapping[str, str]:
    return os.environ if env is None else env


def _optional(env: Mapping[str, str], name: str) -> Optional[str]:
    value = env.get(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _required(env: Mapping[str, str], name: str) -> str:
    value = _optional(env, name)
    if value is None:
        raise ConfigError(f"required environment variable {name} is not set")
    return value


def _timeout_seconds(env: Mapping[str, str]) -> float:
    raw = _optional(env, ENV_REQUEST_TIMEOUT_SECONDS)
    if raw is None:
        return DEFAULT_REQUEST_TIMEOUT_SECONDS
    try:
        value = float(raw)
    except ValueError as exc:
        raise ConfigError(
            f"{ENV_REQUEST_TIMEOUT_SECONDS} must be a number, got {raw!r}"
        ) from exc
    if value <= 0:
        raise ConfigError(
            f"{ENV_REQUEST_TIMEOUT_SECONDS} must be greater than 0, got {value}"
        )
    return value


def _max_subquestions(env: Mapping[str, str]) -> int:
    raw = _optional(env, ENV_MAX_SUBQUESTIONS)
    if raw is None:
        return DEFAULT_MAX_SUBQUESTIONS
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(
            f"{ENV_MAX_SUBQUESTIONS} must be an integer, got {raw!r}"
        ) from exc
    if value < 1:
        raise ConfigError(
            f"{ENV_MAX_SUBQUESTIONS} must be at least 1, got {value}"
        )
    return value


def _max_retrieval_loops(env: Mapping[str, str]) -> int:
    raw = _optional(env, ENV_MAX_RETRIEVAL_LOOPS)
    if raw is None:
        return DEFAULT_MAX_RETRIEVAL_LOOPS
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(
            f"{ENV_MAX_RETRIEVAL_LOOPS} must be an integer, got {raw!r}"
        ) from exc
    if value < 0:
        raise ConfigError(
            f"{ENV_MAX_RETRIEVAL_LOOPS} must be at least 0, got {value}"
        )
    return value


def load_llm_config(env: Optional[Mapping[str, str]] = None) -> LLMConfig:
    """Build :class:`LLMConfig` from ``env`` (defaults to ``os.environ``).

    ``OPENAI_BASE_URL`` is optional: leaving it unset means "use the OpenAI
    client's own default endpoint", while setting it points the same adapter at
    any OpenAI-compatible server.
    """
    source = _source(env)
    return LLMConfig(
        api_key=_required(source, ENV_OPENAI_API_KEY),
        model=_required(source, ENV_OPENAI_MODEL_PLANNER),
        base_url=_optional(source, ENV_OPENAI_BASE_URL),
        timeout_seconds=_timeout_seconds(source),
    )


def load_search_config(env: Optional[Mapping[str, str]] = None) -> SearchConfig:
    """Build :class:`SearchConfig` from ``env`` (defaults to ``os.environ``)."""
    source = _source(env)
    return SearchConfig(
        api_key=_required(source, ENV_TAVILY_API_KEY),
        timeout_seconds=_timeout_seconds(source),
    )


def load_planner_config(env: Optional[Mapping[str, str]] = None) -> PlannerConfig:
    """Build :class:`PlannerConfig` from ``env`` (defaults to ``os.environ``).

    ``MAX_SUBQUESTIONS`` is optional: omitting it uses
    :data:`DEFAULT_MAX_SUBQUESTIONS`.
    """
    source = _source(env)
    return PlannerConfig(max_subquestions=_max_subquestions(source))


def load_graph_config(env: Optional[Mapping[str, str]] = None) -> GraphConfig:
    """Build :class:`GraphConfig` from ``env`` (defaults to ``os.environ``)."""
    source = _source(env)
    return GraphConfig(max_retrieval_loops=_max_retrieval_loops(source))


def load_config(env: Optional[Mapping[str, str]] = None) -> AppConfig:
    """Build the full :class:`AppConfig`; raises :class:`ConfigError` if incomplete."""
    source = _source(env)
    return AppConfig(
        llm=load_llm_config(source),
        search=load_search_config(source),
        planner=load_planner_config(source),
        graph=load_graph_config(source),
    )
