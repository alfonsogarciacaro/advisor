"""
CurrencyService handles FX rate fetching, caching, and currency conversion.

This service is responsible for:
1. Fetching current and historical FX rates from yfinance
2. Caching FX rates to reduce API calls
3. Converting monetary values between currencies
4. Calculating FX returns for risk modeling
"""

import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from app.services.storage_service import StorageService
from app.services.logger_service import LoggerService


class CurrencyService:
    """Service for currency conversion and FX data management"""

    # FX pair mappings (yfinance format)
    # Note: These are the base pairs available in yfinance
    # Inverse pairs will be calculated automatically
    FX_PAIRS = {
        ("USD", "JPY"): "JPY=X",  # USD to JPY
        ("EUR", "JPY"): "EURJPY=X",
        ("GBP", "JPY"): "GBPJPY=X",
        ("AUD", "JPY"): "AUDJPY=X",
        ("CAD", "JPY"): "CADJPY=X",
        ("CHF", "JPY"): "CHFJPY=X",
        ("EUR", "USD"): "EURUSD=X",
        ("GBP", "USD"): "GBPUSD=X",
    }

    # Currency symbols for display
    CURRENCY_SYMBOLS = {
        "JPY": "¥",
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
    }

    def __init__(self, storage_service: StorageService, logger_service: LoggerService):
        self.storage = storage_service
        self.logger = logger_service
        self.collection = "fx_cache"
        self.cache_ttl_hours = 24

    async def get_current_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Get current exchange rate.

        Args:
            from_currency: Source currency code (e.g., "USD")
            to_currency: Target currency code (e.g., "JPY")

        Returns:
            Exchange rate (multiplier to convert from_currency to to_currency)

        Raises:
            ValueError: If FX pair is not supported or fetching fails
        """
        if from_currency == to_currency:
            return 1.0

        fx_pair = self.FX_PAIRS.get((from_currency, to_currency))
        if not fx_pair:
            # Try to find inverse rate
            try:
                inverse_rate = await self.get_current_rate(to_currency, from_currency)
                calculated_rate = 1.0 / inverse_rate

                # Cache the calculated inverse rate
                cache_key = f"rate_{from_currency}_{to_currency}"
                await self.storage.save(
                    self.collection,
                    cache_key,
                    {"rate": calculated_rate, "updated_at": datetime.now().isoformat()}
                )
                self.logger.debug(f"Calculated and cached inverse FX rate {from_currency}/{to_currency}: {calculated_rate}")
                return calculated_rate
            except Exception:
                raise ValueError(f"Unsupported FX pair: {from_currency}/{to_currency}")

        # Check cache first
        cache_key = f"rate_{from_currency}_{to_currency}"
        cached = await self.storage.get(self.collection, cache_key)
        if cached:
            # Check if still valid
            updated = datetime.fromisoformat(cached["updated_at"])
            if datetime.now() - updated < timedelta(hours=self.cache_ttl_hours):
                self.logger.debug(f"Using cached FX rate {from_currency}/{to_currency}: {cached['rate']}")
                return cached["rate"]

        # Fetch from yfinance
        try:
            ticker = yf.Ticker(fx_pair)
            data = ticker.history(period="1d")
            if data.empty:
                raise ValueError(f"Failed to fetch FX rate for {fx_pair}")

            rate = float(data['Close'].iloc[-1])

            # Cache the rate
            await self.storage.save(
                self.collection,
                cache_key,
                {"rate": rate, "updated_at": datetime.now().isoformat()}
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

        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional, defaults to today)

        Returns:
            DataFrame with 'date' and 'rate' columns

        Raises:
            ValueError: If FX pair is not supported or fetching fails
        """
        if from_currency == to_currency:
            # Return DataFrame with rate = 1.0 for all dates
            end = end_date or datetime.now().strftime("%Y-%m-%d")
            dates = pd.date_range(start=start_date, end=end, freq="D")
            return pd.DataFrame({"date": dates, "rate": 1.0})

        fx_pair = self.FX_PAIRS.get((from_currency, to_currency))
        if not fx_pair:
            # Try to find inverse and convert
            try:
                df_inverse = await self.get_historical_rates(to_currency, from_currency, start_date, end_date)
                df_inverse["rate"] = 1.0 / df_inverse["rate"]
                return df_inverse
            except Exception:
                raise ValueError(f"Unsupported FX pair: {from_currency}/{to_currency}")

        # Check cache
        cache_key = f"historical_{from_currency}_{to_currency}_{start_date}_{end_date}"
        cached = await self.storage.get(self.collection, cache_key)
        if cached:
            # Check if still valid
            updated = datetime.fromisoformat(cached["updated_at"])
            if datetime.now() - updated < timedelta(hours=self.cache_ttl_hours):
                self.logger.debug(f"Using cached historical FX rates for {from_currency}/{to_currency}")
                return pd.DataFrame(cached["data"])

        # Fetch from yfinance
        try:
            ticker = yf.Ticker(fx_pair)
            data = ticker.history(start=start_date, end=end_date)

            if data.empty:
                raise ValueError(f"Failed to fetch historical FX data for {fx_pair}")

            # Convert to list format
            result_data = []
            for date, row in data.iterrows():
                result_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "rate": float(row['Close'])
                })

            # Cache the data
            await self.storage.save(
                self.collection,
                cache_key,
                {"data": result_data, "updated_at": datetime.now().isoformat()}
            )

            df = pd.DataFrame(result_data)
            self.logger.info(f"Fetched historical FX rates for {from_currency}/{to_currency}: {len(df)} data points")
            return df
        except Exception as e:
            self.logger.error(f"Error fetching historical FX rates {from_currency}/{to_currency}: {e}")
            raise ValueError(f"Failed to fetch historical FX rates: {e}")

    def convert_currency(self, amount: float, from_currency: str, to_currency: str, rate: float) -> float:
        """
        Convert amount between currencies using provided rate.

        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            rate: Exchange rate (from_currency to to_currency)

        Returns:
            Converted amount in target currency
        """
        if from_currency == to_currency:
            return amount
        return amount * rate

    def calculate_fx_returns(self, fx_rates: pd.DataFrame) -> pd.Series:
        """
        Calculate FX returns from historical rates.

        This represents the percentage change in exchange rate over time,
        which is used as a risk factor in portfolio optimization.

        Args:
            fx_rates: DataFrame with 'date' and 'rate' columns

        Returns:
            Series of FX returns (percentage change)
        """
        df = fx_rates.copy()
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

        Args:
            amount: Amount to convert
            from_currency: Source currency code
            base_currency: Target base currency code

        Returns:
            Amount in base currency
        """
        if from_currency == base_currency:
            return amount

        rate = await self.get_current_rate(from_currency, base_currency)
        return self.convert_currency(amount, from_currency, base_currency, rate)

    def get_currency_symbol(self, currency_code: str) -> str:
        """
        Get display symbol for currency code.

        Args:
            currency_code: Currency code (e.g., "JPY", "USD")

        Returns:
            Currency symbol (e.g., "¥", "$")
        """
        return self.CURRENCY_SYMBOLS.get(currency_code, currency_code)

    async def get_etf_native_currency(self, ticker: str, market: str) -> str:
        """
        Determine the native currency for an ETF based on its market.

        Args:
            ticker: ETF ticker symbol
            market: Market identifier (e.g., "US", "JP")

        Returns:
            Currency code (e.g., "USD", "JPY")
        """
        # Simple mapping based on market
        market_currency_map = {
            "US": "USD",
            "JP": "JPY",
            "UK": "GBP",
            "EU": "EUR",
        }
        return market_currency_map.get(market, "USD")  # Default to USD

    async def fetch_and_convert_current_prices(
        self,
        tickers: List[Tuple[str, str]],  # List of (ticker, market) tuples
        base_currency: str
    ) -> Dict[str, float]:
        """
        Fetch current prices for tickers and convert to base currency.

        Args:
            tickers: List of (ticker, market) tuples
            base_currency: Target base currency code

        Returns:
            Dict mapping ticker to price in base currency
        """
        prices = {}

        for ticker, market in tickers:
            try:
                # Fetch price from yfinance
                yf_ticker = yf.Ticker(ticker)
                data = yf_ticker.history(period="1d")
                if data.empty:
                    continue

                native_price = float(data['Close'].iloc[-1])
                native_currency = await self.get_etf_native_currency(ticker, market)

                # Convert to base currency if needed
                if native_currency != base_currency:
                    rate = await self.get_current_rate(native_currency, base_currency)
                    price = native_price * rate
                else:
                    price = native_price

                prices[ticker] = price
            except Exception as e:
                self.logger.warning(f"Failed to fetch/convert price for {ticker}: {e}")
                continue

        return prices
