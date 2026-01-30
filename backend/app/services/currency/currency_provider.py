
from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd

class CurrencyProvider(ABC):
    """
    Abstract base class for currency data providers.
    """

    @abstractmethod
    async def get_current_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Get current exchange rate.

        Args:
            from_currency: Source currency code (e.g., "USD")
            to_currency: Target currency code (e.g., "JPY")

        Returns:
            Exchange rate (multiplier to convert from_currency to to_currency)
        """
        pass

    @abstractmethod
    async def get_historical_rates(
        self,
        from_currency: str,
        to_currency: str,
        start_date: str,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical exchange rates for a date range.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional, defaults to today)

        Returns:
            DataFrame with 'date' and 'rate' columns
        """
        pass
