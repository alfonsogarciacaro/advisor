import asyncio
import os
import sys
import traceback
from dotenv import load_dotenv

load_dotenv()

# Add the backend directory to sys.path to allow imports from app
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.storage_service import StorageService
from app.services.history_service import HistoryService
from app.infrastructure.storage.firestore_storage import FirestoreStorage

async def main():
    print("Initializing Storage Service...")
    # Using real FirestoreStorage if credentials allow, otherwise Mock (not implemented here but assuming dev env)
    try:
        storage = FirestoreStorage()
        history = HistoryService(storage)
        
        tickers = ['SPY', '2561.T']
        print(f"Fetching history for: {tickers}")
        
        # 1. First fetch (should hit API)
        start_time = asyncio.get_event_loop().time()
        data1 = await history.get_historical_data(tickers, period="5d")
        end_time = asyncio.get_event_loop().time()
        print(f"First fetch took: {end_time - start_time:.4f}s")
        
        for ticker, hist in data1.items():
            print(f"Ticker: {ticker}, Records: {len(hist)}")
            if hist:
                print(f"  Sample: {hist[0]}")
            else:
                print(f"  WARNING: No data for {ticker}")

        # 2. Second fetch (should hit cache)
        print("\nFetching again (should be cached)...")
        start_time = asyncio.get_event_loop().time()
        data2 = await history.get_historical_data(tickers, period="5d")
        end_time = asyncio.get_event_loop().time()
        print(f"Second fetch took: {end_time - start_time:.4f}s")
        
        if len(data1) == len(data2):
             print(f"SUCCESS: Cached data count matches ({len(data2)} tickers)")
        else:
             print("FAILURE: Cached data count mismatch")
            
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
