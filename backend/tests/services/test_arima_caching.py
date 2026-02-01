import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import pandas as pd
import numpy as np
from app.services.forecasting_models.arima_model import ARIMAModel
from app.services.forecasting_engine import ForecastingEngine
from app.services.storage_service import StorageService

# Mock data
@pytest.fixture
def mock_price_history():
    dates = pd.date_range(start="2023-01-01", periods=100, freq="B")
    data = pd.DataFrame({
        "Open": np.random.rand(100) * 100,
        "High": np.random.rand(100) * 100,
        "Low": np.random.rand(100) * 100,
        "Close": np.linspace(100, 150, 100) + np.random.normal(0, 1, 100),
        "Volume": np.random.rand(100) * 1000
    }, index=dates)
    return {"AAPL": data}

@pytest.fixture
def mock_storage_service():
    mock = MagicMock(spec=StorageService)
    mock.get = AsyncMock(return_value=None)
    mock.save = AsyncMock()
    return mock

@pytest.mark.asyncio
async def test_arima_caching_hit(mock_price_history, mock_storage_service, monkeypatch):
    """Test that ARIMA uses cached parameters when available."""
    # Disable FAST_OPTIMIZE to test actual caching behavior
    monkeypatch.setenv("FAST_OPTIMIZE", "false")
    
    model = ARIMAModel()
    model.set_storage_service(mock_storage_service)
    
    # Mock cache hit
    cached_data = {
        "created_at": pd.Timestamp.utcnow().isoformat(),
        "params": [2, 1, 2],
        "ticker": "AAPL",
        "model": "ARIMA"
    }
    mock_storage_service.get.return_value = cached_data
    
    # Mock _auto_tune_arima to ensure it's NOT called
    with patch.object(model, '_auto_tune_arima') as mock_tune:
        await model.forecast(
            tickers=["AAPL"],
            horizon_days=10,
            price_history=mock_price_history,
            auto_tune=True
        )
        
        mock_tune.assert_not_called()
        mock_storage_service.get.assert_called_with("model_params_cache", "arima_params_AAPL")

@pytest.mark.asyncio
async def test_arima_caching_miss(mock_price_history, mock_storage_service, monkeypatch):
    """Test that ARIMA saves parameters to cache after auto-tuning."""
    # Disable FAST_OPTIMIZE to test actual caching behavior
    monkeypatch.setenv("FAST_OPTIMIZE", "false")
    
    model = ARIMAModel()
    model.set_storage_service(mock_storage_service)
    
    # Mock cache miss
    mock_storage_service.get.return_value = None
    
    # Mock _auto_tune_arima to return specific parameters
    with patch.object(model, '_auto_tune_arima', return_value=(1, 1, 1)) as mock_tune:
        await model.forecast(
            tickers=["AAPL"],
            horizon_days=10,
            price_history=mock_price_history,
            auto_tune=True
        )
        
        mock_tune.assert_called_once()
        mock_storage_service.save.assert_called_once()
        
        # Verify save called with correct arguments
        args = mock_storage_service.save.call_args
        assert args[0][0] == "model_params_cache"
        assert args[0][1] == "arima_params_AAPL"
        assert args[0][2]["params"] == [1, 1, 1]

@pytest.mark.asyncio
async def test_forecasting_engine_injection():
    """Test that ForecastingEngine injects storage service into models."""
    mock_storage = MagicMock(spec=StorageService)
    mock_history = MagicMock()
    mock_logger = MagicMock()
    
    engine = ForecastingEngine(
        history_service=mock_history,
        logger=mock_logger,
        storage_service=mock_storage
    )
    
    # Register a new model
    model = ARIMAModel()
    engine.register_model("test_arima", model)
    
    # Check if storage service was injected
    assert model._storage_service == mock_storage
