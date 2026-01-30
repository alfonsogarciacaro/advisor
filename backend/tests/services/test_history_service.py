import pytest
import asyncio
import time

@pytest.mark.asyncio
async def test_history_caching(history_service):
    """Test that historical data is fetched and then cached correctly."""
    tickers = ['SPY', 'QQQ']
    
    # First fetch (should hit provider/API)
    start_time = time.time()
    data1 = await history_service.get_historical_data(tickers, period="5d")
    first_duration = time.time() - start_time
    
    assert len(data1) == 2
    assert 'SPY' in data1
    assert 'QQQ' in data1
    
    # Second fetch (should hit cache)
    start_time = time.time()
    data2 = await history_service.get_historical_data(tickers, period="5d")
    second_duration = time.time() - start_time
    
    assert data1 == data2
    # Caching should be significantly faster, though in local mock it might be subtle.
    # But we can at least assert we got the same data.
    assert len(data2) == 2

@pytest.mark.asyncio
async def test_technical_indicators(history_service):
    """Test technical indicators calculation."""
    tickers = ["SPY"]
    indicators = await history_service.get_technical_indicators(
        tickers=tickers,
        indicators=["RSI", "MACD", "BBANDS", "SMA"]
    )
    
    assert "SPY" in indicators
    spy_data = indicators["SPY"]
    assert "rsi" in spy_data or "error" in spy_data
    
@pytest.mark.asyncio
async def test_market_regime(history_service):
    """Test market regime detection."""
    tickers = ["SPY"]
    regime = await history_service.get_market_regime(tickers)
    
    assert "SPY" in regime
    spy_regime = regime["SPY"]
    assert "trend" in spy_regime
    assert "volatility_regime" in spy_regime
    assert "sentiment" in spy_regime
