import asyncio
import sys
import os
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

async def test_forecast():
    from app.services.history_service import HistoryService
    from app.services.forecast_service import ForecastService
    from app.infrastructure.storage.firestore_storage import FirestoreStorage
    
    # Use real Firestore (requires emulator)
    storage = FirestoreStorage()
    history = HistoryService(storage)
    forecast = ForecastService(history)
    
    ticker = "SPY"
    print(f"Running Monte Carlo for {ticker}...")
    
    # 1. Test metrics
    metrics = await history.get_return_metrics([ticker])
    print(f"Metrics: {metrics}")
    
    if not metrics or ticker not in metrics:
        print("No metrics found. Make sure tests/manual_test_history.py was run or emulator is seeded.")
        return

    # 2. Test simulation
    results = await forecast.run_monte_carlo([ticker], days=252, simulations=1000)
    
    if ticker in results:
        res = results[ticker]
        print(f"\nResults for {ticker}:")
        print(f"Current Price: {res['current_price']:.2f}")
        print(f"Mean Terminal Price: {res['mean_terminal_price']:.2f}")
        print(f"Expected Return: {res['return_mean']:.2%}")
        print(f"Probability of Positive Return: {res['prob_positive_return']:.1%}")
        print(f"95% Confidence Interval: [{res['percentile_5']:.2f}, {res['percentile_95']:.2f}]")
    else:
        print(f"No results for {ticker}")

if __name__ == "__main__":
    asyncio.run(test_forecast())
