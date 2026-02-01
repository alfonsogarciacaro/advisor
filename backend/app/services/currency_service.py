"""
CurrencyService handles FX rate fetching, caching, and currency conversion.

This service is responsible for:
1. Fetching current and historical FX rates via CurrencyProvider
2. Caching FX rates to reduce API calls
3. Converting monetary values between currencies
4. Calculating FX returns for risk modeling
"""

import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta, timezone
from app.services.storage_service import StorageService
from app.services.logger_service import LoggerService
from app.services.currency.currency_provider import CurrencyProvider


class CurrencyService:
    """Service for currency conversion and FX data management"""

    # Currency symbols for display
    CURRENCY_SYMBOLS = {
        "JPY": "¥",
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
    }

    # Market to currency mapping
    MARKET_CURRENCY_MAP = {
        "US": "USD",
        "JP": "JPY",
        "UK": "GBP",
        "EU": "EUR",
    }

    def __init__(self, storage_service: StorageService, logger_service: LoggerService, provider: CurrencyProvider):
        self.storage = storage_service
        self.logger = logger_service
        self.provider = provider
        self.collection = "fx_cache"
        self.cache_ttl_hours = 24

    async def get_current_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Get current exchange rate.
        """
        if from_currency == to_currency:
            return 1.0

        # Check cache first
        cache_key = f"rate_{from_currency}_{to_currency}"
        cached = await self.storage.get(self.collection, cache_key)
        if cached:
            # Check if still valid
            updated = datetime.fromisoformat(cached["updated_at"])
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) - updated < timedelta(hours=self.cache_ttl_hours):
                self.logger.debug(f"Using cached FX rate {from_currency}/{to_currency}: {cached['rate']}")
                return cached["rate"]

        # Fetch from provider
        try:
            rate = await self.provider.get_current_rate(from_currency, to_currency)

            # Cache the rate
            await self.storage.save(
                self.collection,
                cache_key,
                {"rate": rate, "updated_at": datetime.now(timezone.utc).isoformat()}
            )

            self.logger.info(f"Fetched FX rate {from_currency}/{to_currency}: {rate}")
            return rate
        except Exception as e:
            self.logger.error(f"Error fetching FX rate {from_currency}/{to_currency}: {e}")
            raise ValueError(f"Failed to fetch FX rate for {from_currency}/{to_currency}: {e}")

    async def get_historical_rates(
        self,
        from_currency: str,
        to_currency: str,
        start_date: str,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical exchange rates for a date range.
        """
        if from_currency == to_currency:
            # Return DataFrame with rate = 1.0 for all dates
            end = end_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
            dates = pd.date_range(start=start_date, end=end, freq="D")
            return pd.DataFrame({"date": dates, "rate": 1.0})

        # Check cache
        cache_key = f"historical_{from_currency}_{to_currency}_{start_date}_{end_date}"
        cached = await self.storage.get(self.collection, cache_key)
        if cached:
            # Check if still valid
            updated = datetime.fromisoformat(cached["updated_at"])
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) - updated < timedelta(hours=self.cache_ttl_hours):
                self.logger.debug(f"Using cached historical FX rates for {from_currency}/{to_currency}")
                return pd.DataFrame(cached["data"])

        # Fetch from provider
        try:
            df = await self.provider.get_historical_rates(from_currency, to_currency, start_date, end_date)

            # Convert to list format for caching
            result_data = []
            for _, row in df.iterrows():
                # Ensure date is string
                date_val = row['date']
                if hasattr(date_val, 'strftime'):
                    date_str = date_val.strftime("%Y-%m-%d")
                else:
                    date_str = str(date_val)
                
                result_data.append({
                    "date": date_str,
                    "rate": float(row['rate'])
                })

            # Cache the data
            await self.storage.save(
                self.collection,
                cache_key,
                {"data": result_data, "updated_at": datetime.now(timezone.utc).isoformat()}
            )

            self.logger.info(f"Fetched historical FX rates for {from_currency}/{to_currency}: {len(df)} data points")
            return df
        except Exception as e:
            self.logger.error(f"Error fetching historical FX rates {from_currency}/{to_currency}: {e}")
            raise ValueError(f"Failed to fetch historical FX rates: {e}")

    def convert_currency(self, amount: float, from_currency: str, to_currency: str, rate: float) -> float:
        """
        Convert amount between currencies using provided rate.
        """
        if from_currency == to_currency:
            return amount
        return amount * rate

    def calculate_fx_returns(self, fx_rates: pd.DataFrame) -> pd.Series:
        """
        Calculate FX returns from historical rates.
        """
        df = fx_rates.copy()
        if 'date' in df.columns:
            df.set_index('date', inplace=True)
        returns = df['rate'].pct_change().fillna(0)
        return returns

    async def convert_amount_to_base(
        self,
        amount: float,
        from_currency: str,
        base_currency: str
    ) -> float:
        """
        Convert an amount from one currency to base currency.
        """
        if from_currency == base_currency:
            return amount

        rate = await self.get_current_rate(from_currency, base_currency)
        return self.convert_currency(amount, from_currency, base_currency, rate)

    def get_currency_symbol(self, currency_code: str) -> str:
        """
        Get display symbol for currency code.
        """
        return self.CURRENCY_SYMBOLS.get(currency_code, currency_code)

    @staticmethod
    def get_market_currency(market: str) -> str:
        """
        Get the native currency for a market.
        """
        return CurrencyService.MARKET_CURRENCY_MAP.get(market, "USD")
