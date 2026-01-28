import asyncio
import os
import sys
import traceback
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.storage_service import StorageService
from app.services.history_service import HistoryService
from app.services.config_service import ConfigService
from app.services.portfolio_optimizer import PortfolioOptimizerService
from app.infrastructure.storage.firestore_storage import FirestoreStorage

async def main():
    try:
        print("Initializing services...")
        storage = FirestoreStorage()
        history = HistoryService(storage)
        config = ConfigService()
        optimizer = PortfolioOptimizerService(history, config, storage)
        
        print("Starting optimization for $10,000 USD...")
        job_id = await optimizer.start_optimization(amount=10000.0, currency="USD", excluded_tickers=[])
        print(f"Job ID: {job_id}")
        
        while True:
            # Re-read status from storage
            status = await storage.get("optimization_jobs", job_id)
            current_status = status.get('status')
            print(f"Status: {current_status}")
            
            if current_status in ["completed", "failed"]:
                if current_status == "completed":
                    print("\nOptimization Completed!")
                    metrics = status.get('metrics', {})
                    print(f"Net Investment: {metrics.get('net_investment'):.2f}")
                    print(f"Total Commission: {metrics.get('total_commission'):.2f}")
                    print(f"Expected Annual Return: {metrics.get('expected_annual_return'):.2%}")
                    print(f"Annual Volatility: {metrics.get('annual_volatility'):.2%}")
                    print(f"Sharpe Ratio: {metrics.get('sharpe_ratio'):.2f}")
                    
                    print(f"Efficient Frontier Points: {len(status.get('efficient_frontier', []))}")
                    print("Optimal Metrics:")
                    
                    print("\nOptimal Portfolio Weights:")
                    optimal = status.get("optimal_portfolio", [])
                    total_weight = 0
                    for asset in optimal:
                        if asset['weight'] > 0.001:
                            print(f"  {asset['ticker']:<10} {asset['weight']:>6.1%} ({asset['amount']:>9.2f}) Return: {asset['expected_return']:.1%}")
                            total_weight += asset['weight']
                    print(f"  TOTAL      {total_weight:>6.1%}")

                else:
                    print(f"\nOptimization Failed: {status.get('error')}")
                break
            
            await asyncio.sleep(2)

    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
