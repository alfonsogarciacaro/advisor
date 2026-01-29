import pytest
import os
import datetime
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.dependencies import (
    get_news_service,
    get_storage_service
)
# We will use real services for everything except News (external API) and LLM (external API)
# LLM service automatically falls back to Mock if no API key is present, which we ensure in client fixture.
from app.services.news_service import NewsService
from app.services.news.mock_news_provider import MockNewsProvider
from app.infrastructure.storage.firestore_storage import FirestoreStorage
import uuid

# Set environment variables for testing BEFORE any imports/fixtures that might use them
os.environ["GCP_PROJECT_ID"] = "test-project"
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
# Ensure no external API keys are set so LLMService uses MockLLMProvider
if "GEMINI_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]
if "OPENAI_API_KEY" in os.environ:
    del os.environ["OPENAI_API_KEY"]

# Helper to create a unique project id per test run if we wanted, 
# but for emulator we can just use "test-project" and maybe clear data.
# For simplicity, we assume the emulator is ephemeral or we tolerate data.
# Ideally, we should delete data after tests, but let's stick to the plan.

@pytest.fixture
def storage():
    # Helper to access storage directly for seeing data
    return FirestoreStorage()

@pytest.fixture
async def client(storage):
    # Set environment variables for testing
    
    def override_get_news_service():
        # Re-create dependencies
        try:
            # logger = app.dependency_overrides.get("get_logger", lambda: None)()
            # Just use StdLogger directly or None to avoid complexity if get_logger isn't overridden yet
            from app.infrastructure.logging.std_logger import StdLogger
            logger = StdLogger()
            provider = MockNewsProvider()
            return NewsService(provider=provider, storage=storage, logger=logger, ttl_hours=12)
        except Exception as e:
            raise

    app.dependency_overrides[get_news_service] = override_get_news_service
    
    # Ensure real storage is used
    app.dependency_overrides[get_storage_service] = lambda: storage

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    except Exception as e:
        raise

    # Cleanup overrides
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_read_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to ETF Portfolio Advisor Backend"}

@pytest.mark.asyncio
async def test_get_news(client):
    # This tests the real NewsService flow:
    # 1. Checks cache (Firestore) -> Empty first time
    # 2. Calls Provider (MockNewsProvider)
    # 3. Saves to cache
    # 4. Returns news
    
    response = await client.get("/api/news")
    assert response.status_code == 200
    news = response.json()
    assert len(news) == 3 # MockNewsProvider returns 3 items
    assert news[0]["title"] == "Stock Market Reaches New All-Time High"

    # Second call should hit cache (verified by coverage or logs usually, 
    # but here just ensuring it still works)
    response_2 = await client.get("/api/news")
    assert response_2.status_code == 200
    assert response_2.json() == news

@pytest.mark.asyncio
async def test_run_agent(client):
    # This calls real AgentService -> runs in background
    # Tests that the endpoint accepts the request and queues it.
    response = await client.post("/api/agents/research/run", json={"input": {"query": "Test query"}})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert "run_id" in data

@pytest.mark.asyncio
async def test_get_run_status(client, storage):
    # Seed a run
    run_id = str(uuid.uuid4())
    await storage.save("agent_runs", run_id, {
        "run_id": run_id,  # Add run_id to document body
        "agent": "research",
        "status": "completed",
        "result": "Test Result"
    })
    
    response = await client.get(f"/api/agents/runs/{run_id}")
    assert response.status_code == 200
    assert response.json()["run_id"] == run_id
    assert response.json()["status"] == "completed"

@pytest.mark.asyncio
async def test_get_run_logs(client, storage):
    # Seed logs
    run_id = str(uuid.uuid4())
    log_entry = {
        "run_id": run_id,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "level": "INFO",
        "message": "Test Log"
    }
    # Storage.list typically filters. 
    # FirestoreStorage.list takes 'filters'.
    # We need to save it such that list can find it.
    # The collection for logs is "agent_logs" (based on AgentService.get_run_logs)
    await storage.save("agent_logs", str(uuid.uuid4()), log_entry)
    
    response = await client.get(f"/api/agents/runs/{run_id}/logs")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 1
    assert logs[0]["message"] == "Test Log"

@pytest.mark.asyncio
async def test_optimize_portfolio(client):
    # Real PortfolioOptimizerService
    payload = {
        "amount": 10000,
        "currency": "USD",
        "excluded_tickers": ["BTC-USD"]
    }
    response = await client.post("/api/portfolio/optimize", json=payload)
    assert response.status_code == 200
    # Should return a job_id and status queued/started
    data = response.json()
    assert "job_id" in data
    assert data["status"] in ["queued", "running", "completed"] 

@pytest.mark.asyncio
async def test_get_optimization_status(client, storage):
    # Seed a job
    job_id = "test-job-id"
    await storage.save("optimization_jobs", job_id, {
        "job_id": job_id,
        "status": "completed",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "initial_amount": 10000,
        "currency": "USD",
        "optimal_portfolio": []
    })
    
    response = await client.get(f"/api/portfolio/optimize/{job_id}")
    assert response.status_code == 200
    assert response.json()["job_id"] == job_id
    assert response.json()["status"] == "completed"

# ==================== Plan Management Tests ====================

@pytest.mark.asyncio
async def test_create_and_get_plan(client):
    # Real PlanService
    payload = {
        "name": "Integration Test Plan",
        "description": "Unittest plan",
        "risk_preference": "moderate",
        "initial_amount": 100000,
        "currency": "JPY",
        "user_id": "default"
    }
    # Create
    response = await client.post("/api/plans", json=payload)
    assert response.status_code == 200
    data = response.json()
    plan_id = data["plan_id"]
    assert data["status"] == "created"
    
    # Get
    response_get = await client.get(f"/api/plans/{plan_id}")
    assert response_get.status_code == 200
    plan = response_get.json()
    assert plan["plan_id"] == plan_id
    assert plan["name"] == "Integration Test Plan"

@pytest.mark.asyncio
async def test_list_plans(client, storage):
    # Helper to clear plans or ensures we filter by user_id
    user_id = f"user_{uuid.uuid4()}" # Use unique user to avoid noise
    
    payload = {"name": "Plan A", "user_id": user_id}
    await client.post("/api/plans", json=payload)
    
    payload2 = {"name": "Plan B", "user_id": user_id}
    await client.post("/api/plans", json=payload2)
    
    response = await client.get(f"/api/plans?user_id={user_id}")
    assert response.status_code == 200
    plans = response.json()
    assert len(plans) >= 2
    assert any(p["name"] == "Plan A" for p in plans)
    assert any(p["name"] == "Plan B" for p in plans)

@pytest.mark.asyncio
async def test_update_plan(client):
    # Create first
    resp = await client.post("/api/plans", json={"name": "Original"})
    plan_id = resp.json()["plan_id"]
    
    # Update
    payload = {"name": "Updated Name", "notes": "Updated Notes"}
    response = await client.put(f"/api/plans/{plan_id}", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "updated"
    
    # Verify
    resp_get = await client.get(f"/api/plans/{plan_id}")
    assert resp_get.json()["name"] == "Updated Name"
    assert resp_get.json()["notes"] == "Updated Notes"

@pytest.mark.asyncio
async def test_delete_plan(client):
    # Create
    resp = await client.post("/api/plans", json={"name": "To Delete", "user_id": "default"})
    plan_id = resp.json()["plan_id"]
    
    # Delete
    response = await client.delete(f"/api/plans/{plan_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    
    # Verify Gone
    resp_get = await client.get(f"/api/plans/{plan_id}")
    assert resp_get.status_code == 404

@pytest.mark.asyncio
async def test_run_research_on_plan(client, storage):
    # 1. Create Plan
    resp = await client.post("/api/plans", json={"name": "Research Plan"})
    plan_id = resp.json()["plan_id"]
    
    # 2. Run Research (Calls real ResearchAgent -> LLMService -> MockLLMProvider)
    payload = {"query": "Analyze Tech Sector"}
    response = await client.post(f"/api/plans/{plan_id}/research", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert "summary" in data
    
    # 3. Verify Plan has research history
    resp_get = await client.get(f"/api/plans/{plan_id}")
    plan = resp_get.json()
    assert len(plan.get("research_history", [])) == 1
    assert plan["research_history"][0]["query"] == "Analyze Tech Sector"
