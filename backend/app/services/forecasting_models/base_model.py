"""Base class for forecasting models."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class BaseModel(ABC):
    """
    Abstract base class for forecasting models.

    All forecasting models should inherit from this class and implement
    the required methods.
    """

    def __init__(self, name: str):
        """
        Initialize the model.

        Args:
            name: Model name for identification
        """
        self.name = name
        self.metadata = {
            "name": name,
            "requires_history": True,
            "supports_parallel": True,
        }
        self._storage_service = None

    def set_storage_service(self, storage_service: Any):
        """
        Set storage service for caching.
        
        Args:
            storage_service: Storage service instance
        """
        self._storage_service = storage_service

    @abstractmethod
    async def forecast(
        self,
        tickers: List[str],
        horizon_days: int,
        price_history: Dict[str, pd.DataFrame],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run forecast for given tickers.

        Args:
            tickers: List of ticker symbols
            horizon_days: Forecast horizon in days
            price_history: Dict of {ticker: DataFrame with OHLCV data}
            **kwargs: Additional model-specific parameters

        Returns:
            Dict of {ticker: forecast_results}
        """
        pass

    def calculate_returns(self, prices: pd.Series) -> pd.Series:
        """
        Calculate daily returns from price series.

        Args:
            prices: Price series

        Returns:
            Daily returns series
        """
        return prices.pct_change().dropna()

    def annualize_metrics(self, daily_mu: float, daily_sigma: float) -> tuple[float, float]:
        """
        Convert daily metrics to annualized.

        Args:
            daily_mu: Daily mean return
            daily_sigma: Daily volatility

        Returns:
            Tuple of (annual_return, annual_volatility)
        """
        annual_return = daily_mu * 252
        annual_volatility = daily_sigma * np.sqrt(252)
        return annual_return, annual_volatility

    def calculate_confidence_intervals(
        self,
        values: np.ndarray,
        percentiles: Optional[List[float]] = None
    ) -> Dict[str, float]:
        """
        Calculate confidence intervals from array of values.

        Args:
            values: Array of forecasted values (e.g., terminal prices)
            percentiles: List of percentiles to calculate

        Returns:
            Dict of percentile names and values
        """
        if percentiles is None:
            percentiles = [5, 10, 25, 50, 75, 90, 95]

        result = {}
        for p in percentiles:
            result[f"percentile_{p}"] = float(np.percentile(values, p))

        return result

    def validate_history(
        self,
        price_history: pd.DataFrame,
        min_days: int = 252
    ) -> bool:
        """
        Validate that price history has sufficient data.

        Args:
            price_history: Price history DataFrame
            min_days: Minimum required days of history

        Returns:
            True if valid, False otherwise
        """
        if price_history is None or price_history.empty:
            return False
        return len(price_history) >= min_days

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model metadata and capabilities.

        Returns:
            Dict with model information
        """
        return self.metadata.copy()
