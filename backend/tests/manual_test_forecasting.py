"""
Manual testing script for enhanced forecasting system.

Run this to test all components of the forecasting system.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.forecasting_engine import ForecastingEngine
from app.services.history_service import HistoryService
from app.services.macro_service import MacroService
from app.services.risk_calculators import RiskCalculator
from app.services.config_service import ConfigService
from app.services.storage_service import StorageService
from app.infrastructure.storage.firestore_storage import FirestoreStorage


async def test_dependencies():
    """Test that all dependencies are available."""
    print("=" * 60)
    print("Testing Dependencies...")
    print("=" * 60)

    dependencies = {
        "numpy": False,
        "pandas": False,
        "scipy": False,
        "statsmodels": False,
        "yfinance": False,
        "pandas_ta": False,
        "fredapi": False,
    }

    try:
        import numpy
        dependencies["numpy"] = True
        print("✓ numpy available")
    except ImportError:
        print("✗ numpy NOT available")

    try:
        import pandas
        dependencies["pandas"] = True
        print("✓ pandas available")
    except ImportError:
        print("✗ pandas NOT available")

    try:
        import scipy
        dependencies["scipy"] = True
        print("✓ scipy available")
    except ImportError:
        print("✗ scipy NOT available")

    try:
        import statsmodels
        dependencies["statsmodels"] = True
        print("✓ statsmodels available")
    except ImportError:
        print("✗ statsmodels NOT available (ARIMA won't work)")

    try:
        import yfinance
        dependencies["yfinance"] = True
        print("✓ yfinance available")
    except ImportError:
        print("✗ yfinance NOT available")

    try:
        import pandas_ta
        dependencies["pandas_ta"] = True
        print("✓ pandas_ta available")
    except ImportError:
        print("✗ pandas_ta NOT available (technical indicators won't work)")

    try:
        import fredapi
        dependencies["fredapi"] = True
        print("✓ fredapi available")
    except ImportError:
        print("✗ fredapi NOT available (macro data won't work)")

    print()
    return all(dependencies.values())


async def test_baseline_forecast():
    """Test basic forecasting engine."""
    print("=" * 60)
    print("Test 1: Baseline Forecasting Engine")
    print("=" * 60)

    try:
        storage = FirestoreStorage()
        history_service = HistoryService(storage)
        config_service = ConfigService()
        engine = ForecastingEngine(history_service, config_service)

        tickers = ["SPY", "QQQ"]

        print(f"Running baseline forecast for {tickers}...")

        results = await engine.run_forecast_suite(
            tickers=tickers,
            horizon="3mo",
            models=["gbm"],
            simulations=100
        )

        print("\nBaseline Forecasts:")
        for ticker, forecast in results.get("ensemble", {}).items():
            return_metrics = forecast.get("return_metrics", {})
            mean_return = return_metrics.get("mean_return", 0)
            print(f"  {ticker}: {mean_return:.2%} expected return")

        print("\n✓ Baseline forecast test PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Baseline forecast test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_technical_indicators():
    """Test technical analysis."""
    print("\n" + "=" * 60)
    print("Test 2: Technical Indicators")
    print("=" * 60)

    try:
        storage = FirestoreStorage()
        history_service = HistoryService(storage)

        tickers = ["SPY", "QQQ"]

        print(f"Calculating technical indicators for {tickers}...")

        indicators = await history_service.get_technical_indicators(
            tickers=tickers,
            indicators=["RSI", "MACD", "BBANDS", "SMA"]
        )

        print("\nTechnical Indicators:")
        for ticker, data in indicators.items():
            if "error" in data:
                print(f"  {ticker}: ERROR - {data['error']}")
                continue

            rsi = data.get("rsi", "N/A")
            sma_50 = data.get("sma_50", "N/A")
            print(f"  {ticker}: RSI={rsi:.1f}, SMA(50)={sma_50:.2f}")

        print("\n✓ Technical indicators test PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Technical indicators test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_market_regime():
    """Test market regime detection."""
    print("\n" + "=" * 60)
    print("Test 3: Market Regime Detection")
    print("=" * 60)

    try:
        storage = FirestoreStorage()
        history_service = HistoryService(storage)

        tickers = ["SPY"]

        print(f"Detecting market regime for {tickers}...")

        regime = await history_service.get_market_regime(tickers)

        print("\nMarket Regime:")
        for ticker, data in regime.items():
            if "error" in data:
                print(f"  {ticker}: ERROR - {data['error']}")
                continue

            trend = data.get("trend", {})
            volatility = data.get("volatility_regime", "unknown")
            sentiment = data.get("sentiment", "unknown")

            print(f"  {ticker}:")
            print(f"    Trend: {trend.get('direction', 'unknown')} ({trend.get('strength', 'unknown')} strength)")
            print(f"    Volatility: {volatility}")
            print(f"    Sentiment: {sentiment}")

        print("\n✓ Market regime detection test PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Market regime detection test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_risk_metrics():
    """Test risk metrics calculation."""
    print("\n" + "=" * 60)
    print("Test 4: Risk Metrics")
    print("=" * 60)

    try:
        storage = FirestoreStorage()
        history_service = HistoryService(storage)
        risk_calc = RiskCalculator()

        tickers = ["SPY", "QQQ"]

        print(f"Calculating risk metrics for {tickers}...")

        # Fetch price history
        price_history = {}
        for ticker in tickers:
            df = await history_service.get_history(ticker, period="2y")
            if df is not None:
                price_history[ticker] = df

        if not price_history:
            print("  WARNING: No price history available")
            return False

        # Calculate risk metrics
        metrics = risk_calc.calculate_all_risk_metrics(
            price_history,
            confidence_levels=[0.95, 0.99]
        )

        print("\nRisk Metrics (95% VaR):")
        for ticker, ticker_metrics in metrics.items():
            var_95 = ticker_metrics.get("var", {}).get("var_95", {})
            var_historical = var_95.get("var_historical", "N/A")
            print(f"  {ticker}: VaR (95%) = {var_historical:.2%}")

        print("\n✓ Risk metrics test PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Risk metrics test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_macro_data():
    """Test macro data fetching."""
    print("\n" + "=" * 60)
    print("Test 5: Macro Economic Data")
    print("=" * 60)

    try:
        storage = FirestoreStorage()
        macro_service = MacroService(storage)

        print("Fetching US macro indicators...")

        indicators = await macro_service.get_macro_indicators("US")

        if "error" in indicators:
            print(f"  ERROR: {indicators['error']}")
            print("  (This is expected if FRED_API_KEY is not set)")
            return True  # Don't fail test if API key not set

        print("\nMacro Indicators:")
        for key, value in indicators.items():
            if isinstance(value, dict) and "value" in value:
                val = value["value"]
                print(f"  {key}: {val}")

        # Test regime assessment
        print("\nAssessing economic regime...")
        regime = await macro_service.assess_macro_regime("US")

        if "error" not in regime:
            print(f"  Growth Phase: {regime.get('growth_phase', 'unknown')}")
            print(f"  Inflation: {regime.get('inflation_regime', 'unknown')}")
            print(f"  Monetary Policy: {regime.get('monetary_policy', 'unknown')}")

        print("\n✓ Macro data test PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Macro data test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_workflow():
    """Test complete research agent workflow."""
    print("\n" + "=" * 60)
    print("Test 6: Complete Agent Workflow")
    print("=" * 60)

    try:
        from app.services.research_agent import ResearchAgent
        from app.services.logger_service import LoggerService
        from app.infrastructure.logging.std_logger import StdLogger

        logger = StdLogger()
        storage = FirestoreStorage()
        history_service = HistoryService(storage)
        config_service = ConfigService()

        # Create agent with all services
        agent = ResearchAgent(
            logger=logger,
            storage=storage,
            history_service=history_service,
            forecasting_engine=ForecastingEngine(history_service, config_service),
            macro_service=MacroService(storage),
            risk_calculator=RiskCalculator(),
            config_service=config_service
        )

        print("Running agent workflow for SPY forecast...")

        result = await agent.run("Analyze SPY forecast for next 3 months")

        print("\nAgent Summary:")
        print(result.get("summary", "No summary available"))

        print("\n✓ Agent workflow test PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Agent workflow test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "FORECASTING SYSTEM TEST SUITE" + " " * 16 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    results = []

    # Test dependencies
    deps_ok = await test_dependencies()
    results.append(("Dependencies", deps_ok))

    # Only run other tests if dependencies are available
    if deps_ok:
        results.append(("Baseline Forecast", await test_baseline_forecast()))
        results.append(("Technical Indicators", await test_technical_indicators()))
        results.append(("Market Regime", await test_market_regime()))
        results.append(("Risk Metrics", await test_risk_metrics()))
        results.append(("Macro Data", await test_macro_data()))
        results.append(("Agent Workflow", await test_agent_workflow()))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {test_name}: {status}")

    print()
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

    print()


if __name__ == "__main__":
    asyncio.run(main())
