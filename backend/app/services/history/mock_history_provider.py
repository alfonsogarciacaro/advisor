
import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Optional
from .history_provider import HistoryDataProvider

logger = logging.getLogger(__name__)

class MockHistoryProvider(HistoryDataProvider):
    """Mock implementation for testing."""
    
    def download_data(self, tickers: List[str], period: str = "1y", interval: str = "1d") -> Any:
        logger.info(f"Generating mock data for {tickers}")
        
        # Create a MultiIndex DataFrame usually returned by yfinance
        # or a dict of DataFrames depending on how the service consumes it.
        # The service expects the raw yfinance output.
        
        # Generate dates
        if period == "1y":
            days = 252
        elif period == "2y":
            days = 504
        elif period == "5y":
            days = 1260
        else:
            days = 100
            
        dates = pd.date_range(end=pd.Timestamp.now(), periods=days, freq='B')
        
        data_frames = {}
        for ticker in tickers:
            # Random walk
            prices = 100 * np.cumprod(1 + np.random.normal(0, 0.01, size=len(dates)))
            df = pd.DataFrame({
                "Open": prices,
                "High": prices * 1.01,
                "Low": prices * 0.99,
                "Close": prices,
                "Volume": np.random.randint(1000000, 10000000, size=len(dates))
            }, index=dates)
            data_frames[ticker] = df

        if len(tickers) == 1:
            # yfinance returns single DF for single ticker if group_by='ticker' is not strict, 
            # but we used group_by='ticker' in service.
            # However, pandas concat is easier to Mock structure.
            return data_frames[tickers[0]]
            
        # Create MultiIndex: (Ticker, PriceType)
        # Actually yfinance with group_by='ticker' returns (Ticker, PriceType) columns
        reform = {(ticker, col): data_frames[ticker][col] for ticker in tickers for col in data_frames[ticker].columns}
        return pd.DataFrame(reform, index=dates)

    def get_dividends(self, tickers: List[str], period: str = "5y") -> Dict[str, List[Dict[str, Any]]]:
        results = {}
        for ticker in tickers:
            results[ticker] = [
                {"date": "2023-01-01", "amount": 1.5},
                {"date": "2023-04-01", "amount": 1.5},
            ]
        return results
        
    def get_fundamentals(self, tickers: List[str], fields: List[str]) -> Dict[str, Dict[str, Any]]:
        results = {}
        for ticker in tickers:
            data = {field: 100.0 for field in fields}
            data["_metadata"] = {
                "shortName": f"Mock {ticker}",
                "currency": "USD"
            }
            results[ticker] = data
        return results

    def get_latest_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Return deterministic mock prices for testing.
        
        US ETFs: ~$150
        Japanese ETFs (.T suffix): ~¥20,000
        """
        prices = {}
        for ticker in tickers:
            if ticker.endswith('.T'):
                # Japanese ETFs priced in JPY
                prices[ticker] = 20000.0
            else:
                # US ETFs priced in USD
                prices[ticker] = 150.0
        return prices
