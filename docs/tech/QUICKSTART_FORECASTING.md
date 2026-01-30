# Forecasting System - Quick Start Guide

## Installation Steps

### 1. Install New Dependencies

```bash
cd backend
pip install statsmodels>=0.14.0 scipy>=1.11.0 pandas-ta>=0.3.14b fredapi>=0.4.0
```

### 2. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your FRED API key (get free at https://fred.stlouisfed.org/docs/api/api_key.html)
# FRED_API_KEY=your_api_key_here
```

### 3. Run the Test Suite

```bash
python tests/manual_test_forecasting.py
```

This will verify all components are working correctly.

## Quick Usage Examples

### Example 1: Run a Simple Forecast

```python
import asyncio
from app.services.forecasting_engine import ForecastingEngine
from app.services.history_service import HistoryService
from app.services.config_service import ConfigService
from app.infrastructure.storage.firestore_storage import FirestoreStorage

async def forecast_example():
    # Initialize services
    storage = FirestoreStorage()
    history_service = HistoryService(storage)
    config_service = ConfigService()
    engine = ForecastingEngine(history_service, config_service)

    # Run forecast
    results = await engine.run_forecast_suite(
        tickers=["SPY", "QQQ"],
        horizon="6mo",
        simulations=1000
    )

    # Print results
    for ticker, forecast in results["ensemble"].items():
        expected_return = forecast["return_metrics"]["mean_return"]
        print(f"{ticker}: {expected_return:.2%} expected return")

asyncio.run(forecast_example())
```

### Example 2: Get Technical Indicators

```python
import asyncio
from app.services.history_service import HistoryService
from app.infrastructure.storage.firestore_storage import FirestoreStorage

async def technical_example():
    storage = FirestoreStorage()
    history_service = HistoryService(storage)

    # Get technical indicators
    indicators = await history_service.get_technical_indicators(
        tickers=["SPY"],
        indicators=["RSI", "MACD", "BBANDS"]
    )

    # Get market regime
    regime = await history_service.get_market_regime(["SPY"])

    print(f"RSI: {indicators['SPY']['rsi']:.1f}")
    print(f"Trend: {regime['SPY']['trend']['direction']}")
    print(f"Sentiment: {regime['SPY']['sentiment']}")

asyncio.run(technical_example())
```

### Example 3: Calculate Risk Metrics

```python
import asyncio
from app.services.history_service import HistoryService
from app.services.risk_calculators import RiskCalculator
from app.infrastructure.storage.firestore_storage import FirestoreStorage

async def risk_example():
    storage = FirestoreStorage()
    history_service = HistoryService(storage)
    risk_calc = RiskCalculator()

    # Fetch price history
    df = await history_service.get_history("SPY", period="2y")

    # Calculate risk metrics
    metrics = risk_calc.calculate_all_risk_metrics(
        {"SPY": df},
        confidence_levels=[0.95, 0.99]
    )

    # Print VaR
    var_95 = metrics["SPY"]["var"]["var_95"]["var_historical"]
    print(f"95% VaR: {var_95:.2%}")

    # Print drawdown
    max_dd = metrics["SPY"]["drawdown"]["max_drawdown"]
    print(f"Max Drawdown: {max_dd:.2%}")

    # Print Sharpe ratio
    sharpe = metrics["SPY"]["sharpe"]["sharpe_ratio"]
    print(f"Sharpe Ratio: {sharpe:.2f}")

asyncio.run(risk_example())
```

### Example 4: Get Macro Economic Data

```python
import asyncio
from app.services.macro_service import MacroService
from app.infrastructure.storage.firestore_storage import FirestoreStorage

async def macro_example():
    storage = FirestoreStorage()
    macro_service = MacroService(storage)

    # Get macro indicators
    indicators = await macro_service.get_macro_indicators("US")

    # Assess economic regime
    regime = await macro_service.assess_macro_regime("US")

    print(f"Growth Phase: {regime['growth_phase']}")
    print(f"Inflation: {regime['inflation_regime']}")
    print(f"Monetary Policy: {regime['monetary_policy']}")

asyncio.run(macro_example())
```

### Example 5: Run Complete Agent Workflow

```python
import asyncio
from app.services.research_agent import ResearchAgent
from app.services.logger_service import LoggerService
from app.services.history_service import HistoryService
from app.services.forecasting_engine import ForecastingEngine
from app.services.macro_service import MacroService
from app.services.risk_calculators import RiskCalculator
from app.services.config_service import ConfigService
from app.infrastructure.storage.firestore_storage import FirestoreStorage
from app.infrastructure.logging.std_logger import StdLogger

async def agent_example():
    # Initialize services
    logger = StdLogger()
    storage = FirestoreStorage()
    history_service = HistoryService(storage)
    config_service = ConfigService()

    # Create agent
    agent = ResearchAgent(
        logger=logger,
        storage=storage,
        history_service=history_service,
        forecasting_engine=ForecastingEngine(history_service, config_service),
        macro_service=MacroService(storage),
        risk_calculator=RiskCalculator(),
        config_service=config_service
    )

    # Run analysis
    result = await agent.run("Analyze SPY forecast for next 3 months")

    # Print summary
    print(result["summary"])
    print(f"\nConfidence: {result['confidence_level']}")

asyncio.run(agent_example())
```

## Configuration

The forecasting system can be configured via `backend/config/forecasting_config.yaml`:

```yaml
# Adjust default simulations
performance:
  default_simulations: 1000  # Increase for more accuracy

# Adjust scenario weights
scenarios:
  base_case:
    weight: 0.6
  bull_case:
    weight: 0.2
  bear_case:
    weight: 0.2

# Adjust cache TTL
cache_ttl_hours:
  forecasts: 4
  technicals: 4
  macro: 6
```

## Testing Your Setup

Run the manual test script to verify everything works:

```bash
cd backend
python tests/manual_test_forecasting.py
```

Expected output:
```
✓ numpy available
✓ pandas available
✓ scipy available
✓ statsmodels available
✓ yfinance available
✓ pandas_ta available
✓ fredapi available

Test 1: Baseline Forecasting Engine
  SPY: 5.23% expected return
  QQQ: 6.45% expected return
✓ Baseline forecast test PASSED

...

Total: 7/7 tests passed

🎉 All tests passed!
```

## Troubleshooting

### Issue: Import errors for new packages

**Solution**: Install the dependencies
```bash
pip install statsmodels scipy pandas-ta fredapi
```

### Issue: FRED API not working

**Solution**: Get a free API key and add to `.env`:
1. Visit https://fred.stlouisfed.org/docs/api/api_key.html
2. Sign up for free account
3. Copy API key to `.env`: `FRED_API_KEY=your_key_here`

### Issue: Technical indicators not working

**Solution**: Install pandas-ta:
```bash
pip install pandas-ta
```

### Issue: Firestore connection error

**Solution**: Ensure `GOOGLE_APPLICATION_CREDENTIALS` is set in `.env`:
```
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

## Next Steps

1. ✅ Install dependencies
2. ✅ Configure environment variables
3. ✅ Run test suite
4. ✅ Try the examples above
5. 📚 Read `FORECASTING_IMPLEMENTATION.md` for detailed documentation

## Support

For issues or questions:
- Check the implementation guide: `FORECASTING_IMPLEMENTATION.md`
- Review the configuration: `config/forecasting_config.yaml`
- Run the test suite: `tests/manual_test_forecasting.py`

Happy forecasting! 📈
