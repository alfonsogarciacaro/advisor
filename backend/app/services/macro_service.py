"""Macro economic data service."""

import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Import fredapi for FRED data
try:
    from fredapi import Fred
    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False

# Import yfinance for market data
import yfinance as yf
import pandas as pd
from app.services.logger_service import LoggerService


class MacroService:
    """
    Service for fetching macro economic indicators.

    Supports:
    - US data via FRED API
    - Japan data via OECD/yfinance
    - Market yields and exchange rates
    """

    # FRED series codes for key indicators
    FRED_SERIES = {
        "US": {
            "gdp_growth": "A191RL1Q225SBEA",  # Real GDP Growth
            "gdp": "GDP",  # Gross Domestic Product
            "unemployment": "UNRATE",  # Unemployment Rate
            "cpi": "CPIAUCSL",  # Consumer Price Index
            "core_cpi": "CPILFESL",  # Core CPI (ex food/energy)
            "pce": "PCEPI",  # PCE Price Index
            "fed_funds_rate": "FEDFUNDS",  # Federal Funds Rate
            "10y_treasury": "GS10",  # 10-Year Treasury Yield
            "2y_treasury": "GS2",  # 2-Year Treasury Yield
            "30y_treasury": "GS30",  # 30-Year Treasury Yield
            "dollar_index": "DTWEXBGS",  # Trade Weighted Dollar Index
        }
    }

    def __init__(self, storage_service, logger: LoggerService, fred_api_key: Optional[str] = None):
        """
        Initialize macro service.

        Args:
            storage_service: Storage service for caching
            logger: Service for logging
            fred_api_key: FRED API key (uses env var if None)
        """
        self.storage = storage_service
        self.logger = logger
        self.collection = "cache"
        self.doc_id_prefix = "macro_"
        self.cache_ttl_hours = 6

        # Initialize FRED client
        self.fred_api_key = fred_api_key or os.getenv("FRED_API_KEY")
        self.fred = None

        if FRED_AVAILABLE and self.fred_api_key:
            try:
                self.fred = Fred(api_key=self.fred_api_key)
            except Exception as e:
                self.logger.error(f"Failed to initialize FRED client: {e}")

    async def get_macro_indicators(
        self,
        market: str = "US",
        indicators: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch latest macro indicators for a market.

        Args:
            market: Market code ("US" or "JP")
            indicators: List of specific indicators (default: all)

        Returns:
            Dict of indicator values with metadata
        """
        # Check cache first
        cache_key = f"{market}_{indicators}"
        doc_id = f"{self.doc_id_prefix}{cache_key}"
        cached = await self.storage.get(self.collection, doc_id)

        if cached:
            last_updated_str = cached.get("updated_at")
            if last_updated_str:
                try:
                    last_updated = datetime.fromisoformat(last_updated_str)
                    if last_updated.tzinfo is None:
                        last_updated = last_updated.replace(tzinfo=datetime.timezone.utc)
                    if datetime.now(datetime.timezone.utc) - last_updated < timedelta(hours=self.cache_ttl_hours):
                        self.logger.debug(f"Cache hit for macro indicators: {market}")
                        return cached.get("data", {})
                except (ValueError, TypeError):
                    pass

        # Fetch fresh data
        if market.upper() == "US":
            data = await self._get_us_indicators(indicators)
        elif market.upper() == "JP":
            data = await self._get_japan_indicators(indicators)
        else:
            data = {"error": f"Unsupported market: {market}"}

        # Cache the results
        cache_entry = {
            "data": data,
            "updated_at": datetime.now(datetime.timezone.utc).isoformat()
        }
        await self.storage.save(self.collection, doc_id, cache_entry)

        return data

    async def _get_us_indicators(
        self,
        indicators: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Fetch US economic indicators from FRED."""
        result = {}

        if not self.fred:
            return {
                "error": "FRED API not configured. Set FRED_API_KEY environment variable."
            }

        if indicators is None:
            indicators = list(self.FRED_SERIES["US"].keys())

        for indicator in indicators:
            if indicator not in self.FRED_SERIES["US"]:
                continue

            series_id = self.FRED_SERIES["US"][indicator]

            try:
                # Fetch data in executor to avoid blocking
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(
                    None,
                    lambda: self._fetch_fred_series(series_id)
                )

                if data:
                    result[indicator] = data

            except Exception:
                result[indicator] = {"error": "Failed to fetch"}

        return result

    def _fetch_fred_series(self, series_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single FRED series."""
        try:
            series = self.fred.get_series(series_id)

            if series.empty:
                return None

            # Get latest value
            latest_value = float(series.iloc[-1])
            latest_date = series.index[-1]

            # Calculate change from previous period
            if len(series) >= 2:
                previous_value = float(series.iloc[-2])
                change = latest_value - previous_value
                change_pct = (latest_value / previous_value - 1) * 100 if previous_value != 0 else 0
            else:
                change = None
                change_pct = None

            return {
                "value": latest_value,
                "date": latest_date.isoformat() if hasattr(latest_date, "isoformat") else str(latest_date),
                "change": change,
                "change_pct": change_pct,
                "series_id": series_id,
            }

        except Exception:
            return None

    async def _get_japan_indicators(
        self,
        indicators: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch Japan economic indicators.

        Note: Limited free data sources for Japan.
        Uses yfinance for market data and yields.
        """
        result = {}

        # Default indicators for Japan
        if indicators is None:
            indicators = ["10y_jgb", "usd_jpy", "nikkei_225"]

        for indicator in indicators:
            try:
                if indicator == "10y_jgb":
                    # 10-year JGB yield (approximated via ETF)
                    data = await self._fetch_yfinance_data("^TNX")  # Use US treasuries as proxy
                    if data:
                        result["10y_jgb"] = data

                elif indicator == "usd_jpy":
                    # USD/JPY exchange rate
                    data = await self._fetch_yfinance_data("JPY=X")
                    if data:
                        result["usd_jpy"] = data

                elif indicator == "nikkei_225":
                    # Nikkei 225 index
                    data = await self._fetch_yfinance_data("^N225")
                    if data:
                        result["nikkei_225"] = data

            except Exception:
                result[indicator] = {"error": "Failed to fetch"}

        return result

    async def _fetch_yfinance_data(
        self,
        ticker: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch data from yfinance."""
        try:
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period="5d")

            if hist.empty:
                return None

            latest = hist.iloc[-1]
            latest_price = float(latest["Close"])

            # Calculate change
            if len(hist) >= 2:
                previous_price = float(hist.iloc[-2]["Close"])
                change = latest_price - previous_price
                change_pct = (latest_price / previous_price - 1) * 100
            else:
                change = None
                change_pct = None

            return {
                "value": latest_price,
                "date": hist.index[-1].isoformat(),
                "change": change,
                "change_pct": change_pct,
                "ticker": ticker,
            }

        except Exception:
            return None

    async def assess_macro_regime(
        self,
        market: str = "US"
    ) -> Dict[str, Any]:
        """
        Classify the current economic regime.

        Args:
            market: Market to analyze

        Returns:
            Dict with regime classification
        """
        indicators = await self.get_macro_indicators(market)

        if "error" in indicators:
            return {"error": indicators["error"]}

        if market.upper() == "US":
            return self._assess_us_regime(indicators)
        elif market.upper() == "JP":
            return self._assess_japan_regime(indicators)
        else:
            return {"error": "Unsupported market"}

    def _assess_us_regime(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Assess US economic regime."""
        regime = {
            "growth_phase": "unknown",
            "inflation_regime": "unknown",
            "monetary_policy": "unknown",
            "summary": "",
        }

        # Assess growth phase
        if "gdp_growth" in indicators and "error" not in indicators["gdp_growth"]:
            gdp_growth = indicators["gdp_growth"].get("value", 0)
            if gdp_growth > 3:
                regime["growth_phase"] = "expansion"
            elif gdp_growth > 0:
                regime["growth_phase"] = "recovery"
            elif gdp_growth > -2:
                regime["growth_phase"] = "slowdown"
            else:
                regime["growth_phase"] = "recession"

        # Assess inflation regime
        if "cpi" in indicators and "error" not in indicators["cpi"]:
            # Check recent trend (approximated by latest value)
            cpi_val = indicators["cpi"].get("value", 0)
            cpi_change = indicators["cpi"].get("change_pct", 0)

            if cpi_change > 0.4:  # High inflation (> 5% annualized)
                regime["inflation_regime"] = "high"
            elif cpi_change > 0.2:  # Moderate inflation (2-5%)
                regime["inflation_regime"] = "elevated"
            elif cpi_change > 0.1:  # Target range (~2%)
                regime["inflation_regime"] = "target"
            else:
                regime["inflation_regime"] = "low"

        # Assess monetary policy stance
        if "fed_funds_rate" in indicators and "error" not in indicators["fed_funds_rate"]:
            ff_rate = indicators["fed_funds_rate"].get("value", 0)
            ff_change = indicators["fed_funds_rate"].get("change", 0)

            if ff_change > 0.25:
                regime["monetary_policy"] = "tightening"
            elif ff_change < -0.25:
                regime["monetary_policy"] = "easing"
            elif ff_rate > 4:
                regime["monetary_policy"] = "restrictive"
            elif ff_rate < 1:
                regime["monetary_policy"] = "accommodative"
            else:
                regime["monetary_policy"] = "neutral"

        # Generate summary
        summary_parts = [
            f"Economic {regime['growth_phase']}",
            f"with {regime['inflation_regime']} inflation",
            f"and {regime['monetary_policy']} monetary policy"
        ]
        regime["summary"] = ", ".join(summary_parts) + "."

        return regime

    def _assess_japan_regime(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Assess Japan economic regime (simplified)."""
        # Japan assessment is more limited due to data availability
        regime = {
            "growth_phase": "unknown",
            "monetary_policy": "accommodative",  # BOJ typically dovish
            "currency_regime": "unknown",
            "summary": "Limited data for Japan economic assessment",
        }

        # Assess currency (USD/JPY)
        if "usd_jpy" in indicators and "error" not in indicators["usd_jpy"]:
            usdjpy_change = indicators["usd_jpy"].get("change_pct", 0)

            if usdjpy_change > 2:
                regime["currency_regime"] = "weakening_yen"
            elif usdjpy_change < -2:
                regime["currency_regime"] = "strengthening_yen"
            else:
                regime["currency_regime"] = "stable"

        return regime

    async def get_market_yields(
        self,
        market: str = "US"
    ) -> Dict[str, Any]:
        """
        Get current market yield curve.

        Args:
            market: Market code

        Returns:
            Dict with yield curve data
        """
        if market.upper() == "US":
            return await self.get_macro_indicators("US", ["2y_treasury", "10y_treasury", "30y_treasury"])
        else:
            return {"error": "Yield data not available for this market"}

    async def is_fred_available(self) -> bool:
        """Check if FRED API is available."""
        return self.fred is not None
