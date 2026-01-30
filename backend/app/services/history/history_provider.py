
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class HistoryDataProvider(ABC):
    """Abstract base class for history data providers."""
    
    @abstractmethod
    def download_data(self, tickers: List[str], period: str = "1y", interval: str = "1d") -> Any:
        """Download raw data from source."""
        pass

    @abstractmethod
    def get_dividends(self, tickers: List[str], period: str = "5y") -> Dict[str, List[Dict[str, Any]]]:
        """Get dividend history."""
        pass
        
    @abstractmethod
    def get_fundamentals(self, tickers: List[str], fields: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get fundamental data."""
        pass

    @abstractmethod
    def get_latest_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Get the latest closing price for each ticker.
        
        Returns:
            Dict mapping ticker symbol to latest closing price.
        """
        pass
