import pytest
from app.services.forecasting_engine import ForecastingEngine
from app.services.config_service import ConfigService

@pytest.fixture
def forecasting_engine(history_service, logger, storage):
    config_service = ConfigService(storage_service=storage)
    return ForecastingEngine(history_service, logger, config_service, storage)

@pytest.mark.asyncio
async def test_baseline_forecast_ensemble(forecasting_engine):
    """Test that the ensemble forecast works with multiple models."""
    tickers = ["SPY", "QQQ"]
    
    results = await forecasting_engine.run_forecast_suite(
        tickers=tickers,
        horizon="3mo",
        models=["gbm"], # GBM is usually the fastest/default
        simulations=100
    )
    
    assert "ensemble" in results
    assert "SPY" in results["ensemble"]
    assert "QQQ" in results["ensemble"]
    
    spy_forecast = results["ensemble"]["SPY"]
    assert "return_metrics" in spy_forecast
    assert "mean_return" in spy_forecast["return_metrics"]

@pytest.mark.asyncio
async def test_specific_model_forecast(forecasting_engine):
    """Test running a specific forecasting model (GBM)."""
    tickers = ["SPY"]
    
    results = await forecasting_engine.run_specific_model(
        model_name="gbm",
        tickers=tickers,
        horizon_days=30,
        simulations=100
    )
    
    assert "SPY" in results
    spy_res = results["SPY"]
    assert "terminal" in spy_res
    assert "mean" in spy_res["terminal"]
    assert "return_metrics" in spy_res
    assert "prob_positive_return" in spy_res["return_metrics"]
