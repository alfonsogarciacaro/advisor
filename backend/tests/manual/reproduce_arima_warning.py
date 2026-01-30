
import asyncio
import pandas as pd
import numpy as np
import warnings
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from app.services.forecasting_models.arima_model import ARIMAModel

async def run_test():
    print("Testing ARIMA Model for warnings...")
    
    # Create dummy data with date index but no frequency
    dates = pd.date_range(start="2023-01-01", periods=100, freq='D')
    # Drop some dates to simulate irregular data (e.g. trading days)
    # This removes the frequency from the index
    dates = dates.drop(dates[5:10]) 
    
    data = pd.DataFrame({
        "Close": np.random.lognormal(mean=0, sigma=0.1, size=len(dates)) * 100
    }, index=dates)
    
    # Verify index has no freq
    print(f"Data index frequency: {data.index.freq}")
    
    model = ARIMAModel()
    
    # Run forecast
    # We expect statsmodels warnings here
    results = await model.forecast(
        tickers=["TEST"],
        horizon_days=5,
        price_history={"TEST": data}
    )
    
    print("\nResults keys:", results["TEST"].keys())
    if "error" in results["TEST"]:
        print("Error:", results["TEST"]["error"])
    else:
        print("Success")

if __name__ == "__main__":
    asyncio.run(run_test())
