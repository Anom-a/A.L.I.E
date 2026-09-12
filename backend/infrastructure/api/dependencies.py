"""Dependency injection definitions for the FastAPI application.

This module is the ONLY place where concrete implementations get bound to domain
and application ports. Controllers rely on these dependency providers via Depends().
"""

import os
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request

from infrastructure.config import AppConfig, load_config
from adapters.llm.openai_compatible_llm import OpenAICompatibleLLM
from adapters.gateways.tavily_gateway import TavilyGateway
from adapters.gateways.ifixit_gateway import IFixitGateway
from adapters.gateways.semantic_scholar_gateway import SemanticScholarGateway
from adapters.gateways.news_api_gateway import NewsApiGateway
from adapters.repositories.sql_job_repository import SQLJobRepository
from application.classifiers.keyword_classifier import KeywordSubQuestionClassifier
from application.use_cases.plan_sub_questions import PlanSubQuestionsUseCase
from application.use_cases.route_tool import RouteToolUseCase
from application.use_cases.critique_evidence import CritiqueEvidenceUseCase
from application.use_cases.synthesize_report import SynthesizeReportUseCase
from application.graph.research_graph import ResearchGraph
from application.use_cases.run_research import RunResearchUseCase, ExtendedJobRepositoryPort
from domain.ports.llm_port import LLMPort
from domain.ports.search_tool_port import SearchToolPort


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Load configuration exactly once."""
    # We load from environment. The test suite can monkeypatch os.environ
    # or override the dependency.
    return load_config()


def get_llm_port(config: Annotated[AppConfig, Depends(get_config)]) -> LLMPort:
    """Provide the concrete LLM adapter based on config."""
    return OpenAICompatibleLLM(
        api_key=config.llm.api_key,
        model=config.llm.model,
        base_url=config.llm.base_url,
        timeout_seconds=config.llm.timeout_seconds,
        retry_config=config.retry,
    )


def get_search_port(config: Annotated[AppConfig, Depends(get_config)]) -> SearchToolPort:
    """Provide the primary search gateway (Tavily)."""
    return TavilyGateway(
        api_key=config.search.api_key,
        timeout_seconds=config.search.timeout_seconds,
        retry_config=config.retry,
    )


def get_job_repository(
    request: Request
) -> ExtendedJobRepositoryPort:
    """Provide a SQL job repository tied to the current user if available."""
    # We will grab user_id from request.state if it exists
    user_id = getattr(request.state, "user_id", None)
    return SQLJobRepository(user_id=user_id)


def get_research_graph(
    config: Annotated[AppConfig, Depends(get_config)],
    llm: Annotated[LLMPort, Depends(get_llm_port)],
    search: Annotated[SearchToolPort, Depends(get_search_port)],
) -> ResearchGraph:
    """Wire up the full research graph with concrete components."""
    planner = PlanSubQuestionsUseCase(
        llm=llm,
        max_subquestions=config.planner.max_subquestions,
    )
    router = RouteToolUseCase(KeywordSubQuestionClassifier())
    critic = CritiqueEvidenceUseCase(llm=llm)
    synth = SynthesizeReportUseCase(llm=llm)
    
    # We instantiate iFixit here as fallback; no API key needed
    ifixit = IFixitGateway(
        retry_config=config.retry,
    )
    semantic_scholar = SemanticScholarGateway(
        api_key=config.semantic_scholar.api_key,
        timeout_seconds=config.semantic_scholar.timeout_seconds,
        retry_config=config.retry,
    )
    news_api = NewsApiGateway(
        api_key=config.news_api.api_key,
        base_url=config.news_api.base_url,
        timeout_seconds=config.news_api.timeout_seconds,
        retry_config=config.retry,
    )
    
    return ResearchGraph(
        planner=planner,
        router=router,
        gateways={
            "tavily": search,
            "ifixit": ifixit,
            "semantic_scholar": semantic_scholar,
            "news_api": news_api,
        },
        fallback_gateway=search,  # Tavily is the general-purpose fallback
        critic=critic,
        synthesizer=synth,
        max_loops=config.graph.max_retrieval_loops,
    )


def get_run_research_use_case(
    graph: Annotated[ResearchGraph, Depends(get_research_graph)],
    repo: Annotated[ExtendedJobRepositoryPort, Depends(get_job_repository)],
) -> RunResearchUseCase:
    """Provide the use case that runs the graph and tracks state."""
    return RunResearchUseCase(graph=graph, repository=repo)


def setup_dependencies(app):
    """Wire the dependencies to the controller's stub dependables."""
    # We need to import the stubs from the controller module
    from adapters.controllers import research_controller
    
    app.dependency_overrides[research_controller.get_job_repository] = get_job_repository
    app.dependency_overrides[research_controller.get_run_research_use_case] = get_run_research_use_case
    app.dependency_overrides[research_controller.get_llm_port] = get_llm_port
    app.dependency_overrides[research_controller.get_search_port] = get_search_port
