import pytest
import pandas as pd
import numpy as np
from app.services.forecasting_models.arima_model import ARIMAModel
from app.services.forecasting_models.gbm_model import GBMModel

@pytest.mark.asyncio
async def test_arima_irregular_data_warning_handling():
    """
    Test that ARIMAModel handles irregular data (missing dates) without crashing.
    This replicates the scenario in reproduce_arima_warning.py.
    """
    # Create dummy data with date index but no frequency (missing gaps)
    dates = pd.date_range(start="2023-01-01", periods=300, freq='D')
    dates = dates.drop(dates[50:60]) # Drop some dates to simulate irregular data
    
    data = pd.DataFrame({
        "Close": np.random.lognormal(mean=0, sigma=0.1, size=len(dates)) * 100
    }, index=dates)
    
    model = ARIMAModel()
    
    # Run forecast
    # We want to ensure it completes without raising an unhandled exception
    results = await model.forecast(
        tickers=["TEST"],
        horizon_days=5,
        price_history={"TEST": data}
    )
    
    assert "TEST" in results
    # It might return an error if data is too irregular for ARIMA, 
    # but it shouldn't crash the engine.
    if "error" not in results["TEST"]:
        assert "terminal" in results["TEST"]
        assert "mean" in results["TEST"]["terminal"]

@pytest.mark.asyncio
async def test_gbm_model():
    """Test functionality of Geometric Brownian Motion model."""
    dates = pd.date_range(start="2023-01-01", periods=300, freq='D')
    data = pd.DataFrame({
        "Close": np.random.lognormal(mean=0, sigma=0.01, size=len(dates)) * 100
    }, index=dates)
    
    model = GBMModel()
    results = await model.forecast(
        tickers=["TEST"],
        horizon_days=10,
        price_history={"TEST": data},
        simulations=500
    )
    
    assert "TEST" in results
    assert "terminal" in results["TEST"]
    assert "mean" in results["TEST"]["terminal"]
    assert results["TEST"]["simulations"] == 500
