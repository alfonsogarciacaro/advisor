import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.dependencies import get_news_service, get_agent_service, get_portfolio_optimizer_service, get_storage_service
from unittest.mock import AsyncMock, MagicMock
import uuid
import datetime

# Mock implementations
@pytest.fixture
def mock_news_service():
    service = AsyncMock()
    service.get_latest_news.return_value = [
        {"title": "Test News 1", "summary": "Summary 1", "url": "http://example.com/1"},
        {"title": "Test News 2", "summary": "Summary 2", "url": "http://example.com/2"}
    ]
    return service

@pytest.fixture
def mock_agent_service():
    service = AsyncMock()
    service.create_run.return_value = "test-run-id"
    service.get_run.return_value = {
        "run_id": "test-run-id",
        "status": "completed",
        "agent": "research",
        "result": "Test result"
    }
    service.get_run_logs.return_value = [
        {"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "message": "Log 1"}
    ]
    return service

@pytest.fixture
def mock_portfolio_service():
    service = AsyncMock()
    service.start_optimization.return_value = "test-job-id"
    return service

@pytest.fixture
def mock_storage_service():
    service = AsyncMock()
    service.get.return_value = {
        "job_id": "test-job-id",
        "status": "completed",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "initial_amount": 10000,
        "currency": "USD",
        "optimal_portfolio": [],
        "metrics": {}
    }
    return service

@pytest.fixture
async def client(mock_news_service, mock_agent_service, mock_portfolio_service, mock_storage_service):
    # Override dependencies
    app.dependency_overrides[get_news_service] = lambda: mock_news_service
    app.dependency_overrides[get_agent_service] = lambda: mock_agent_service
    app.dependency_overrides[get_portfolio_optimizer_service] = lambda: mock_portfolio_service
    app.dependency_overrides[get_storage_service] = lambda: mock_storage_service
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    # Clear overrides after test
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_read_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to ETF Portfolio Advisor Backend"}

@pytest.mark.asyncio
async def test_get_news(client, mock_news_service):
    response = await client.get("/api/news")
    assert response.status_code == 200
    assert len(response.json()) == 2
    mock_news_service.get_latest_news.assert_called_once()

@pytest.mark.asyncio
async def test_run_agent(client, mock_agent_service):
    response = await client.post("/api/agents/research/run", json={"input": {"test": "data"}})
    assert response.status_code == 200
    assert response.json() == {"run_id": "test-run-id", "status": "queued"}
    mock_agent_service.create_run.assert_called_once_with("research", {"test": "data"})

@pytest.mark.asyncio
async def test_get_run_status(client, mock_agent_service):
    response = await client.get("/api/agents/runs/test-run-id")
    assert response.status_code == 200
    assert response.json()["run_id"] == "test-run-id"
    mock_agent_service.get_run.assert_called_once_with("test-run-id")

@pytest.mark.asyncio
async def test_get_run_logs(client, mock_agent_service):
    response = await client.get("/api/agents/runs/test-run-id/logs")
    assert response.status_code == 200
    assert len(response.json()) == 1
    mock_agent_service.get_run_logs.assert_called_once_with("test-run-id")

@pytest.mark.asyncio
async def test_optimize_portfolio(client, mock_portfolio_service):
    payload = {
        "amount": 10000,
        "currency": "USD",
        "excluded_tickers": ["BTC-USD"]
    }
    response = await client.post("/api/portfolio/optimize", json=payload)
    assert response.status_code == 200
    assert response.json() == {"job_id": "test-job-id", "status": "queued"}
    mock_portfolio_service.start_optimization.assert_called_once_with(
        amount=10000,
        currency="USD",
        excluded_tickers=["BTC-USD"]
    )

@pytest.mark.asyncio
async def test_get_optimization_status(client, mock_storage_service):
    response = await client.get("/api/portfolio/optimize/test-job-id")
    assert response.status_code == 200
    assert response.json()["job_id"] == "test-job-id"
    mock_storage_service.get.assert_called_once_with("optimization_jobs", "test-job-id")
