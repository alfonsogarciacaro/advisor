"""
Tests for CurrencyService

Tests FX rate fetching, caching, and currency conversion.
Uses real yfinance for data and Firestore emulator for caching.
"""

import pytest
import os
import pandas as pd
from datetime import datetime, timedelta
from app.services.currency_service import CurrencyService
from app.infrastructure.storage.firestore_storage import FirestoreStorage
from app.services.logger_service import LoggerService
from app.infrastructure.logging.std_logger import StdLogger


@pytest.fixture
def storage():
    return FirestoreStorage()


@pytest.fixture
def logger():
    return StdLogger()


@pytest.fixture
def currency_service(storage, logger):
    return CurrencyService(storage_service=storage, logger_service=logger)


@pytest.mark.asyncio
async def test_get_current_rate_usd_to_jpy(currency_service):
    """Test fetching current USD to JPY rate"""
    rate = await currency_service.get_current_rate("USD", "JPY")

    # USD/JPY should be between 100 and 200 (reasonable range)
    assert 100 < rate < 200, f"USD/JPY rate {rate} is outside reasonable range"


@pytest.mark.asyncio
async def test_get_current_rate_same_currency(currency_service):
    """Test that same currency returns rate of 1.0"""
    rate = await currency_service.get_current_rate("USD", "USD")
    assert rate == 1.0

    rate_jpy = await currency_service.get_current_rate("JPY", "JPY")
    assert rate_jpy == 1.0


@pytest.mark.asyncio
async def test_get_current_rate_caching(currency_service):
    """Test that FX rates are cached"""
    # First call - fetches from yfinance
    rate1 = await currency_service.get_current_rate("USD", "JPY")

    # Second call - should hit cache
    rate2 = await currency_service.get_current_rate("USD", "JPY")

    assert rate1 == rate2, "Cached rate should match original rate"


@pytest.mark.asyncio
async def test_get_historical_rates(currency_service):
    """Test fetching historical FX rates"""
    # Get historical data for a short period
    start_date = "2024-01-01"
    end_date = "2024-01-31"

    df = await currency_service.get_historical_rates("USD", "JPY", start_date, end_date)

    # Verify DataFrame structure
    assert isinstance(df, pd.DataFrame), "Should return a DataFrame"
    assert "date" in df.columns, "Should have date column"
    assert "rate" in df.columns, "Should have rate column"
    assert len(df) > 0, "Should have data points"


@pytest.mark.asyncio
async def test_get_historical_rates_same_currency(currency_service):
    """Test historical rates for same currency returns 1.0"""
    start_date = "2024-01-01"
    end_date = "2024-01-31"

    df = await currency_service.get_historical_rates("USD", "USD", start_date, end_date)

    assert len(df) > 0, "Should have data points"
    assert all(df["rate"] == 1.0), "All rates should be 1.0 for same currency"


@pytest.mark.asyncio
async def test_convert_currency(currency_service):
    """Test currency conversion"""
    amount = 1000
    rate = 150.0  # Assume USD/JPY rate

    converted = currency_service.convert_currency(amount, "USD", "JPY", rate)
    assert converted == 150000, f"Expected 150000 JPY, got {converted}"

    # Same currency should return same amount
    same = currency_service.convert_currency(amount, "USD", "USD", 1.0)
    assert same == amount


@pytest.mark.asyncio
async def test_calculate_fx_returns(currency_service):
    """Test FX return calculation"""
    # Create sample FX data
    fx_data = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=5),
        "rate": [150.0, 151.0, 149.0, 152.0, 153.0]
    })

    returns = currency_service.calculate_fx_returns(fx_data)

    # Returns should be a Series
    assert isinstance(returns, pd.Series), "Should return a Series"
    assert len(returns) == 5, "Should have same length as input"

    # First return should be 0 (no previous day)
    assert returns.iloc[0] == 0, "First return should be 0"

    # Other returns should be non-zero (rates changed)
    assert returns.iloc[1] != 0, "Second return should be non-zero"


@pytest.mark.asyncio
async def test_get_currency_symbol(currency_service):
    """Test getting currency symbols"""
    assert currency_service.get_currency_symbol("JPY") == "¥"
    assert currency_service.get_currency_symbol("USD") == "$"
    assert currency_service.get_currency_symbol("EUR") == "€"
    assert currency_service.get_currency_symbol("GBP") == "£"


@pytest.mark.asyncio
async def test_get_etf_native_currency(currency_service):
    """Test determining ETF native currency from market"""
    us_currency = await currency_service.get_etf_native_currency("SPY", "US")
    assert us_currency == "USD"

    jp_currency = await currency_service.get_etf_native_currency("1306.T", "JP")
    assert jp_currency == "JPY"


@pytest.mark.asyncio
async def test_convert_amount_to_base(currency_service):
    """Test converting amount to base currency"""
    # Convert USD to JPY base
    amount = 100
    converted = await currency_service.convert_amount_to_base(amount, "USD", "JPY")

    # Should be roughly 100 * current USD/JPY rate
    assert converted > 10000, "USD should convert to much larger JPY amount"
    assert converted < 20000, "USD should convert to reasonable JPY amount"


@pytest.mark.asyncio
async def test_unsupported_fx_pair(currency_service):
    """Test that unsupported FX pairs raise ValueError"""
    with pytest.raises(ValueError, match="Unsupported FX pair"):
        await currency_service.get_current_rate("XXX", "YYY")


@pytest.mark.asyncio
async def test_fetch_and_convert_current_prices(currency_service):
    """Test fetching and converting ETF prices to base currency"""
    tickers = [("SPY", "US"), ("VTI", "US")]

    prices = await currency_service.fetch_and_convert_current_prices(tickers, "JPY")

    # Should have prices for both tickers
    assert "SPY" in prices, "Should have SPY price"
    assert "VTI" in prices, "Should have VTI price"

    # Prices should be positive
    assert prices["SPY"] > 0, "SPY price should be positive"
    assert prices["VTI"] > 0, "VTI price should be positive"

    # JPY prices should be larger than USD prices (roughly 100x)
    assert prices["SPY"] > 100, "SPY price in JPY should be > 100"


@pytest.mark.asyncio
async def test_historical_rate_caching(currency_service, storage):
    """Test that historical rates are cached"""
    start_date = "2024-01-01"
    end_date = "2024-01-10"

    # First call
    df1 = await currency_service.get_historical_rates("USD", "JPY", start_date, end_date)

    # Check that it was cached
    cache_key = f"historical_USD_JPY_{start_date}_{end_date}"
    cached = await storage.get("fx_cache", cache_key)

    assert cached is not None, "Historical rates should be cached"
    assert "data" in cached, "Cached data should have 'data' field"
    assert "updated_at" in cached, "Cached data should have timestamp"

    # Second call should use cache
    df2 = await currency_service.get_historical_rates("USD", "JPY", start_date, end_date)

    # DataFrames should be equal
    assert len(df1) == len(df2), "Cached data should match original"


@pytest.mark.asyncio
async def test_inverse_rate_calculation(currency_service):
    """Test that inverse rates are calculated correctly"""
    rate1 = await currency_service.get_current_rate("JPY", "USD")

    # JPY/USD should be roughly 1 / (USD/JPY)
    # We can't test exact equality because rates might change between calls
    # but we can verify it's a small positive number
    assert 0 < rate1 < 0.01, "JPY/USD rate should be small positive number"
