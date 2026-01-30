import pytest
import datetime
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.dependencies import (
    get_storage_service
)
from app.infrastructure.storage.firestore_storage import FirestoreStorage
import uuid

# Environment variables are loaded automatically from .env.test via conftest.py

# For emulator we just use "test-project"
# For simplicity, we assume the emulator is ephemeral or we tolerate data.

@pytest.fixture
def storage():
    # Helper to access storage directly for seeing data
    return FirestoreStorage()

@pytest.fixture
async def client(storage):
    # Override Auth to bypass real JWT requirement for integration tests
    from app.core.dependencies import get_current_user
    from app.models.auth import User
    app.dependency_overrides[get_current_user] = lambda: User(username="test-user", role="user")
    
    # Ensure real storage is used (though it would default to it anyway)
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


# ==================== Strategy Templates Tests ====================

@pytest.mark.asyncio
async def test_list_strategies(client):
    """Test listing all strategy templates"""
    response = await client.get("/api/strategies")
    assert response.status_code == 200
    strategies = response.json()
    assert len(strategies) > 0, "Should have at least one strategy"

    # Verify each strategy has required fields
    for strategy in strategies:
        assert "strategy_id" in strategy
        assert "name" in strategy
        assert "description" in strategy
        assert "risk_level" in strategy
        assert "constraints" in strategy

@pytest.mark.asyncio
async def test_list_strategies_filter_by_risk(client):
    """Test filtering strategies by risk level"""
    # Test conservative filter
    response = await client.get("/api/strategies?risk_level=conservative")
    assert response.status_code == 200
    conservative_strategies = response.json()
    assert len(conservative_strategies) > 0

    # All returned strategies should be conservative
    for strategy in conservative_strategies:
        assert strategy["risk_level"] == "conservative"

    # Test aggressive filter
    response = await client.get("/api/strategies?risk_level=aggressive")
    assert response.status_code == 200
    aggressive_strategies = response.json()
    assert len(aggressive_strategies) > 0

    # All returned strategies should be aggressive
    for strategy in aggressive_strategies:
        assert strategy["risk_level"] == "aggressive"

@pytest.mark.asyncio
async def test_get_strategy_by_id(client):
    """Test getting a specific strategy template"""
    # First get all strategies to find a valid ID
    list_response = await client.get("/api/strategies")
    strategies = list_response.json()
    if strategies:
        strategy_id = strategies[0]["strategy_id"]

        # Get specific strategy
        response = await client.get(f"/api/strategies/{strategy_id}")
        assert response.status_code == 200
        strategy = response.json()
        assert strategy["strategy_id"] == strategy_id
        assert "name" in strategy
        assert "constraints" in strategy

    # Test 404 for non-existent strategy
    response = await client.get("/api/strategies/nonexistent_strategy")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_tax_settings(client):
    """Test getting tax settings for different account types"""
    response = await client.get("/api/config/tax-settings")
    assert response.status_code == 200
    tax_settings = response.json()

    # Verify structure
    assert "short_term_capital_gains_rate" in tax_settings
    assert "long_term_capital_gains_rate" in tax_settings
    assert "account_types" in tax_settings

    # Verify account types exist
    account_types = tax_settings["account_types"]
    assert "taxable" in account_types
    assert "nisa_growth" in account_types
    assert "nisa_general" in account_types


# ==================== Historical Backtesting Tests ====================

@pytest.mark.asyncio
async def test_optimize_with_historical_date(client):
    """Test optimization with historical date for backtesting"""
    payload = {
        "amount": 10000,
        "currency": "USD",
        "historical_date": "2020-01-01",
        "account_type": "taxable"
    }
    response = await client.post("/api/portfolio/optimize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] in ["queued", "running", "completed"]

@pytest.mark.asyncio
async def test_optimize_with_strategy_template(client):
    """Test optimization with strategy template"""
    payload = {
        "amount": 10000,
        "currency": "USD",
        "use_strategy": "conservative_income",
        "historical_date": "2022-01-01",
        "account_type": "nisa_growth"
    }
    response = await client.post("/api/portfolio/optimize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data

@pytest.mark.asyncio
async def test_optimization_with_backtest_result(client, storage):
    """Test that optimization with historical date returns backtest result"""
    # Create a mock optimization job with backtest result
    job_id = "test-backtest-job"
    mock_job = {
        "job_id": job_id,
        "status": "completed",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "initial_amount": 10000,
        "currency": "USD",
        "optimal_portfolio": [],
        "backtest_result": {
            "trajectory": [
                {"date": "2020-01-01", "value": 10000},
                {"date": "2021-01-01", "value": 11000}
            ],
            "benchmark_trajectory": [
                {"date": "2020-01-01", "value": 10000},
                {"date": "2021-01-01", "value": 10500}
            ],
            "metrics": {
                "total_return": 0.10,
                "final_value": 11000,
                "volatility": 0.15,
                "sharpe_ratio": 0.67,
                "max_drawdown": -0.05,
                "recovery_days": 180,
                "cagr": 0.10
            },
            "start_date": "2020-01-01",
            "end_date": "2021-01-01",
            "account_type": "taxable",
            "capital_gains_tax": 200.0
        }
    }

    await storage.save("optimization_jobs", job_id, mock_job)

    # Get optimization status
    response = await client.get(f"/api/portfolio/optimize/{job_id}")
    assert response.status_code == 200
    result = response.json()

    # Verify backtest result is included
    assert "backtest_result" in result
    assert result["backtest_result"] is not None
    assert "trajectory" in result["backtest_result"]
    assert "metrics" in result["backtest_result"]

    # Verify key metrics
    metrics = result["backtest_result"]["metrics"]
    assert "total_return" in metrics
    assert "max_drawdown" in metrics
    assert "sharpe_ratio" in metrics

@pytest.mark.asyncio
async def test_different_account_types_backtest(client):
    """Test backtesting with different account types"""
    account_types = ["taxable", "nisa_growth", "nisa_general"]

    for account_type in account_types:
        payload = {
            "amount": 10000,
            "currency": "USD",
            "historical_date": "2020-01-01",
            "account_type": account_type
        }
        response = await client.post("/api/portfolio/optimize", json=payload)
        assert response.status_code == 200, f"Failed for account_type: {account_type}"
        data = response.json()
        assert "job_id" in data


# ==================== Portfolio Management Tests ====================

@pytest.mark.asyncio
async def test_validate_portfolio_holdings_valid(client, storage):
    """Test portfolio validation with valid holdings"""
    # Create a plan
    resp = await client.post("/api/plans", json={"name": "Validation Test Plan"})
    plan_id = resp.json()["plan_id"]

    # Valid holdings - under limits
    holdings = [
        {"ticker": "SPY", "account_type": "taxable", "monetary_value": 500000},
        {"ticker": "VTI", "account_type": "nisa_growth", "monetary_value": 1000000}
    ]

    response = await client.post(
        f"/api/portfolio/validate",
        json={"plan_id": plan_id, "holdings": holdings}
    )

    assert response.status_code == 200
    result = response.json()
    assert result["valid"] is True
    assert len(result["errors"]) == 0


@pytest.mark.asyncio
async def test_validate_portfolio_holdings_over_limit(client, storage):
    """Test portfolio validation detects limit violations"""
    # Create a plan
    resp = await client.post("/api/plans", json={"name": "Over Limit Test Plan"})
    plan_id = resp.json()["plan_id"]

    # Holdings over NISA Growth limit (¥1.8M/year)
    holdings = [
        {"ticker": "SPY", "account_type": "nisa_growth", "monetary_value": 2000000}
    ]

    response = await client.post(
        f"/api/portfolio/validate",
        json={"plan_id": plan_id, "holdings": holdings}
    )

    assert response.status_code == 200
    result = response.json()
    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert "exceed annual limit" in result["errors"][0]["message"]


@pytest.mark.asyncio
async def test_validate_portfolio_nonexistent_plan(client):
    """Test validation with non-existent plan"""
    holdings = [
        {"ticker": "SPY", "account_type": "taxable", "monetary_value": 500000}
    ]

    response = await client.post(
        f"/api/portfolio/validate",
        json={"plan_id": "nonexistent-plan-id", "holdings": holdings}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_available_etfs(client, storage):
    """Test getting available ETFs with prices in base currency"""
    # Create a plan (will have base_currency = JPY by default)
    resp = await client.post("/api/plans", json={"name": "ETF Test Plan"})
    plan_id = resp.json()["plan_id"]

    response = await client.get(f"/api/portfolio/etfs/available?plan_id={plan_id}")

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "etfs" in data
    assert "account_limits" in data
    assert "base_currency" in data
    assert data["base_currency"] == "JPY"

    # Verify ETF list
    etfs = data["etfs"]
    assert len(etfs) > 0

    # Check first ETF structure
    first_etf = etfs[0]
    assert "symbol" in first_etf
    assert "name" in first_etf
    assert "market" in first_etf
    assert "native_currency" in first_etf
    assert "current_price_base" in first_etf

    # Price should be positive
    assert first_etf["current_price_base"] > 0


@pytest.mark.asyncio
async def test_get_available_etfs_nonexistent_plan(client):
    """Test getting ETFs for non-existent plan"""
    response = await client.get("/api/portfolio/etfs/available?plan_id=nonexistent-plan-id")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_plan_portfolio(client, storage):
    """Test updating plan's initial portfolio"""
    # Create a plan
    resp = await client.post("/api/plans", json={"name": "Portfolio Update Test"})
    plan_id = resp.json()["plan_id"]

    # Update portfolio
    holdings = [
        {"ticker": "SPY", "account_type": "taxable", "monetary_value": 500000},
        {"ticker": "VTI", "account_type": "nisa_growth", "monetary_value": 1000000}
    ]

    response = await client.put(
        f"/api/plans/{plan_id}/portfolio",
        json={"initial_portfolio": holdings}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["plan_id"] == plan_id
    assert data["status"] == "updated"

    # Verify the plan was updated
    resp_get = await client.get(f"/api/plans/{plan_id}")
    plan = resp_get.json()

    assert "initial_portfolio" in plan
    assert len(plan["initial_portfolio"]) == 2


@pytest.mark.asyncio
async def test_update_plan_portfolio_empty(client, storage):
    """Test updating plan with empty portfolio"""
    # Create a plan with some holdings
    holdings = [
        {"ticker": "SPY", "account_type": "taxable", "monetary_value": 500000}
    ]

    resp = await client.post("/api/plans", json={
        "name": "Empty Portfolio Test",
        "initial_portfolio": holdings
    })
    plan_id = resp.json()["plan_id"]

    # Verify initial portfolio exists
    resp_get = await client.get(f"/api/plans/{plan_id}")
    plan = resp_get.json()
    assert len(plan.get("initial_portfolio", [])) > 0

    # Clear portfolio
    response = await client.put(
        f"/api/plans/{plan_id}/portfolio",
        json={"initial_portfolio": []}
    )

    assert response.status_code == 200

    # Verify portfolio was cleared
    resp_get = await client.get(f"/api/plans/{plan_id}")
    plan = resp_get.json()
    assert plan.get("initial_portfolio") == []


@pytest.mark.asyncio
async def test_update_plan_portfolio_nonexistent_plan(client):
    """Test updating portfolio for non-existent plan"""
    holdings = [
        {"ticker": "SPY", "account_type": "taxable", "monetary_value": 500000}
    ]

    response = await client.put(
        "/api/plans/nonexistent-plan-id/portfolio",
        json={"initial_portfolio": holdings}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_plan_has_base_currency(client):
    """Test that plans have base_currency field"""
    # Create a plan
    resp = await client.post("/api/plans", json={"name": "Base Currency Test"})
    plan_id = resp.json()["plan_id"]

    # Get the plan
    response = await client.get(f"/api/plans/{plan_id}")
    assert response.status_code == 200

    plan = response.json()
    assert "base_currency" in plan
    # Default should be JPY
    assert plan["base_currency"] == "JPY"


@pytest.mark.asyncio
async def test_multi_account_portfolio_validation(client, storage):
    """Test validation across multiple account types"""
    # Create a plan
    resp = await client.post("/api/plans", json={"name": "Multi Account Test"})
    plan_id = resp.json()["plan_id"]

    # Holdings across multiple accounts
    holdings = [
        {"ticker": "SPY", "account_type": "taxable", "monetary_value": 2000000},
        {"ticker": "VTI", "account_type": "nisa_growth", "monetary_value": 900000},
        {"ticker": "AGG", "account_type": "nisa_general", "monetary_value": 1000000}
    ]

    response = await client.post(
        f"/api/portfolio/validate",
        json={"plan_id": plan_id, "holdings": holdings}
    )

    assert response.status_code == 200
    result = response.json()

    # Should be valid (all under limits)
    assert result["valid"] is True
    assert len(result["errors"]) == 0


@pytest.mark.asyncio
async def test_account_limits_in_etf_response(client, storage):
    """Test that ETF availability response includes account limits"""
    # Create a plan
    resp = await client.post("/api/plans", json={"name": "Account Limits Test"})
    plan_id = resp.json()["plan_id"]

    # Add some holdings to the plan
    holdings = [
        {"ticker": "SPY", "account_type": "nisa_growth", "monetary_value": 500000}
    ]

    await client.put(
        f"/api/plans/{plan_id}/portfolio",
        json={"initial_portfolio": holdings}
    )

    # Get available ETFs
    response = await client.get(f"/api/portfolio/etfs/available?plan_id={plan_id}")
    assert response.status_code == 200

    data = response.json()
    account_limits = data["account_limits"]

    # Check that limits exist
    assert "nisa_growth" in account_limits

    nisa_growth = account_limits["nisa_growth"]
    assert "annual_limit" in nisa_growth
    assert "used_space" in nisa_growth
    assert "available_space" in nisa_growth

    # Verify calculations
    assert nisa_growth["annual_limit"] > 0
    assert nisa_growth["used_space"] == 500000  # What we just added
    assert nisa_growth["available_space"] == nisa_growth["annual_limit"] - 500000
