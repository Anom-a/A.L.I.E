#!/usr/bin/env python3
"""Smoke test for Phase 8 FastAPI Service.

Boots the FastAPI app using TestClient, overrides dependencies with Fakes,
submits a research query, and verifies the full HTTP request/response cycle.
"""

import sys
import time
from uuid import uuid4
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from infrastructure.api.main import create_app
from infrastructure.api.dependencies import get_llm_port, get_search_port, get_config
from infrastructure.config import AppConfig, LLMConfig, SearchConfig
from domain.entities.evidence import Evidence, SourceType
from domain.entities.citation import Citation

# Import fakes from tests
sys.path.append(".")
from tests.unit.test_research_graph import FakeLLM, FakeSearch

def main():
    print("Setting up Phase 8 Smoke Test...")
    
    app = create_app()
    
    def override_get_config():
        return AppConfig(
            llm=LLMConfig(api_key="fake", model="fake"),
            search=SearchConfig(api_key="fake")
        )
        
    def override_get_llm_port():
        return FakeLLM(
            plan_resp={"sub_questions": [{"text": "Smoke Test Q1"}]},
            critique_resps=[{"satisfied": True, "reason": "Looks good", "missing_aspects": []}],
            synth_resp={
                "title": "Smoke Test Report",
                "sections": [
                    {
                        "title": "Result",
                        "content": "The system works.",
                        "citation_ids": ["CIT-001"]
                    }
                ]
            }
        )
        
    def override_get_search_port():
        ev = Evidence(
            sub_question_id=uuid4(),
            source_type=SourceType.WEB,
            content="Some evidence",
            citation=Citation("https://fake.com", "Fake Source", datetime.now(timezone.utc))
        )
        return FakeSearch([ev])
        
    app.dependency_overrides[get_config] = override_get_config
    app.dependency_overrides[get_llm_port] = override_get_llm_port
    app.dependency_overrides[get_search_port] = override_get_search_port
    
    client = TestClient(app)
    
    print("\n1. Health Check")
    resp = client.get("/health")
    if resp.status_code != 200:
        print(f"ERROR: Health check failed: {resp.text}")
        sys.exit(1)
    print("   -> OK")
    
    print("\n2. Submit Research Job")
    resp = client.post("/research", json={"topic": "Integration Test"})
    if resp.status_code != 202:
        print(f"ERROR: Job submission failed: {resp.text}")
        sys.exit(1)
    
    job_id = resp.json()["job_id"]
    print(f"   -> Job submitted successfully. ID: {job_id}")
    
    print("\n3. Poll Job Status")
    # In TestClient, background tasks are executed synchronously before post() returns.
    # So it should already be DONE.
    resp = client.get(f"/research/{job_id}")
    status = resp.json().get("status")
    print(f"   -> Status: {status}")
    if status != "done":
        print(f"ERROR: Expected status 'done', got '{status}'. Error: {resp.json().get('error')}")
        sys.exit(1)
        
    print("\n4. Fetch Report")
    resp = client.get(f"/research/{job_id}/report")
    if resp.status_code != 200:
        print(f"ERROR: Failed to fetch report: {resp.text}")
        sys.exit(1)
        
    report = resp.json()
    print(f"   -> Report fetched successfully. Title: {report.get('sections', [{}])[0].get('title')}")
    print(f"   -> Content: {report.get('sections', [{}])[0].get('content')}")
    
    print("\nSUCCESS: Phase 8 smoke test passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
