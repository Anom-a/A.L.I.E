import ast
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from infrastructure.api.main import create_app
from infrastructure.api.dependencies import get_llm_port, get_search_port
from domain.entities.research_query import ResearchQuery, ResearchStatus
from adapters.controllers import research_controller
from infrastructure.config import ConfigError

# Import fakes
import sys
sys.path.append(".")
from tests.unit.test_research_graph import FakeLLM, FakeSearch


@pytest.fixture
def app():
    """Create a FastAPI app instance with fakes for E2E tests."""
    app = create_app()
    
    def override_get_config():
        from infrastructure.config import AppConfig, LLMConfig, SearchConfig, SemanticScholarConfig, NewsApiConfig
        return AppConfig(
            llm=LLMConfig(api_key="fake", model="fake"),
            search=SearchConfig(api_key="fake"),
            semantic_scholar=SemanticScholarConfig(),
            news_api=NewsApiConfig(api_key="fake"),
        )
        
    def override_get_llm_port():
        return FakeLLM(
            plan_resp={"sub_questions": [{"text": "Q1"}]},
            critique_resps=[{"satisfied": True, "reason": "ok", "missing_aspects": []}],
            synth_resp={
                "title": "API Test Report",
                "sections": [{"title": "Sec 1", "content": "Content", "citation_ids": ["CIT-001"]}]
            }
        )
        
    def override_get_search_port():
        # Empty evidence because FakeSearch usually needs Evidence objects, but we'll let it be empty
        # Wait, if evidence is empty, Synthesis fails! We need to return some evidence.
        from domain.entities.evidence import Evidence, SourceType
        from domain.entities.citation import Citation
        from datetime import datetime, timezone
        ev = Evidence(
            sub_question_id=uuid4(),
            source_type=SourceType.WEB,
            content="API test evidence",
            citation=Citation("http://test.com", "Test", datetime.now(timezone.utc))
        )
        return FakeSearch([ev])
        
    app.dependency_overrides[get_llm_port] = override_get_llm_port
    app.dependency_overrides[get_search_port] = override_get_search_port
    
    from infrastructure.api.dependencies import get_config
    app.dependency_overrides[get_config] = override_get_config
    
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_happy_path(client):
    """1. Happy path: submit job, it runs (synchronously in TestClient), get report."""
    # POST
    resp = client.post("/research", json={"topic": "Test E2E"})
    assert resp.status_code == 202
    data = resp.json()
    job_id = data["job_id"]
    # With TestClient, background tasks finish before this assertion happens!
    # So the status might already be DONE, but the controller returns PENDING initially.
    assert data["status"] == "pending"

    # GET status
    resp2 = client.get(f"/research/{job_id}")
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "done", f"Failed with error: {resp2.json().get('error')}"

    # GET report
    resp3 = client.get(f"/research/{job_id}/report")
    assert resp3.status_code == 200
    report_data = resp3.json()
    assert report_data["query_id"] == job_id
    assert len(report_data["sections"]) == 1
    assert report_data["sections"][0]["title"] == "Sec 1"


def test_unknown_job_id(client):
    """2. Unknown job_id -> 404."""
    bad_id = str(uuid4())
    resp = client.get(f"/research/{bad_id}")
    assert resp.status_code == 404
    
    resp2 = client.get(f"/research/{bad_id}/report")
    assert resp2.status_code == 404


def test_report_requested_before_done(client, app):
    """3. Report requested before done -> 404."""
    # Insert a RUNNING job directly into the repository
    repo = app.dependency_overrides.get(
        research_controller.get_job_repository,
        research_controller.get_job_repository
    )() if research_controller.get_job_repository in app.dependency_overrides else None
    
    if not repo:
        from infrastructure.api.dependencies import get_job_repository
        repo = get_job_repository()
        
    query = ResearchQuery(topic="Pending Job")
    repo.add(query)
    repo.update_status(query.id, ResearchStatus.RUNNING)
    
    resp = client.get(f"/research/{query.id}/report")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Report not ready"


def test_failure_path(client, app):
    """4. Failure path: job ends up FAILED with error message."""
    # Override the use case to raise an error
    from application.use_cases.run_research import RunResearchUseCase
    
    class FailingUseCase(RunResearchUseCase):
        def execute(self, query_id):
            repo = self._repository
            repo.update_status(query_id, ResearchStatus.RUNNING)
            repo.save_error(query_id, "Boom!")
            repo.update_status(query_id, ResearchStatus.FAILED)
            
    # We must patch the dependency
    from infrastructure.api.dependencies import get_job_repository
    repo = get_job_repository()
    
    def override_get_run_research_use_case():
        return FailingUseCase(graph=None, repository=repo)
        
    app.dependency_overrides[research_controller.get_run_research_use_case] = override_get_run_research_use_case
    
    resp = client.post("/research", json={"topic": "Fail me"})
    job_id = resp.json()["job_id"]
    
    resp2 = client.get(f"/research/{job_id}")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["status"] == "failed"
    assert data["error"] == "Boom!"


def test_health_check_valid(client):
    """5a. GET /health with valid config -> 200."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_health_check_invalid(client, app):
    """5b. GET /health with missing config -> 503."""
    def override_get_config():
        raise ConfigError("Missing OPENAI_API_KEY")
        
    from infrastructure.api.dependencies import get_config
    app.dependency_overrides[get_config] = override_get_config
    
    resp = client.get("/health")
    assert resp.status_code == 503
    assert "missing openai_api_key" in resp.json()["detail"].lower()


def test_architecture_controller_imports():
    """6. Architecture check: controller does not import concrete gateways directly."""
    controller_path = Path("adapters/controllers/research_controller.py")
    tree = ast.parse(controller_path.read_text())
    
    forbidden_imports = [
        "adapters.gateways.tavily_gateway",
        "adapters.gateways.ifixit_gateway",
        "adapters.llm.openai_compatible_llm",
        "TavilyGateway",
        "OpenAICompatibleLLM",
    ]
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name not in forbidden_imports, f"Found forbidden import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert not any(f in node.module for f in forbidden_imports), f"Found forbidden from-import: {node.module}"
            for alias in node.names:
                assert alias.name not in forbidden_imports, f"Found forbidden from-import: {alias.name}"
