import datetime
import pandas as pd
import numpy as np
import yfinance as yf
from .storage_service import StorageService
from typing import List, Dict, Any, Optional

# Import pandas-ta for technical indicators
try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False

class HistoryService:
    def __init__(self, storage: StorageService, ttl_hours: int = 24):
        self.storage = storage
        self.ttl_hours = ttl_hours
        self.collection = "cache"
        self.doc_id_prefix = "history_"

    async def get_historical_data(self, tickers: List[str], period: str = "1y", interval: str = "1d") -> Dict[str, Any]:
        """
        Fetches historical data for the given tickers.
        Tries to fetch from cache first, then falls back to yfinance.
        """
        results = {}
        tickers_to_fetch = []

        # 1. Check cache for each ticker
        for ticker in tickers:
            doc_id = f"{self.doc_id_prefix}{ticker}_{period}_{interval}"
            cached_data = await self.storage.get(self.collection, doc_id)

            if cached_data:
                last_updated_str = cached_data.get("updated_at")
                if last_updated_str:
                    try:
                        last_updated = datetime.datetime.fromisoformat(last_updated_str)
                        # Ensure timezone-aware datetime for comparison
                        if last_updated.tzinfo is None:
                            last_updated = last_updated.replace(tzinfo=datetime.timezone.utc)
                        if datetime.datetime.now(datetime.timezone.utc) - last_updated < datetime.timedelta(hours=self.ttl_hours):
                            results[ticker] = cached_data.get("data")
                            continue
                    except (ValueError, TypeError):
                        # Invalid timestamp format, fetch fresh data
                        pass
            
            tickers_to_fetch.append(ticker)

        # 2. Fetch missing data from yfinance
        if tickers_to_fetch:
            data = yf.download(tickers_to_fetch, period=period, interval=interval, group_by='ticker', auto_adjust=True, threads=True)
            
            for ticker in tickers_to_fetch:
                if data is None:
                    results[ticker] = []
                    continue

                ticker_data = []
                
                if len(tickers_to_fetch) == 1 and ticker in tickers_to_fetch:
                    # If only one ticker, yf.download might return simple DF or MultiIndex
                    if isinstance(data.columns, pd.MultiIndex):
                        try:
                            df = data[ticker]
                        except KeyError:
                            df = data
                    else:
                        df = data
                else:
                    try:
                        df = data[ticker]
                    except (KeyError, IndexError):
                        results[ticker] = []
                        continue

                if df.empty:
                    results[ticker] = []
                    continue

                df_reset = df.reset_index()
                
                # Identify the date column (usually 'Date' or 'index')
                date_col = None
                for col in ['Date', 'index', 'Datetime']:
                    if col in df_reset.columns:
                        date_col = col
                        break
                
                if not date_col:
                    continue
                
                for _, row in df_reset.iterrows():
                    date_val = row.get(date_col)
                    
                    # Ensure date_val is a scalar and a valid datetime-like object
                    if isinstance(date_val, (pd.Series, pd.DataFrame)):
                        continue
                    
                    if pd.isna(date_val):
                        continue
                        
                    try:
                        # Convert to string and validate it looks like a date (YYYY-MM-DD or ISO)
                        if hasattr(date_val, 'isoformat'):
                            date_str = date_val.isoformat()
                        else:
                            # Try to parse and then format to be sure
                            date_str = pd.to_datetime(date_val).isoformat()

                        # Basic validation: ensure it's not a generic string like "Price"
                        if " " in date_str and "T" not in date_str: # Likely not ISO
                             continue

                        def sanitize(val):
                            if pd.isna(val):
                                return None
                            try:
                                if isinstance(val, (pd.Series, pd.DataFrame)):
                                    val = val.iloc[0] if not val.empty else None
                                return float(val) if val is not None else None
                            except (ValueError, TypeError):
                                return None

                        entry = {
                            "date": date_str,
                            "open": sanitize(row.get('Open')),
                            "high": sanitize(row.get('High')),
                            "low": sanitize(row.get('Low')),
                            "close": sanitize(row.get('Close')),
                            "volume": sanitize(row.get('Volume'))
                        }
                        ticker_data.append(entry)
                    except Exception:
                        continue

                results[ticker] = ticker_data

                # Save to cache
                if ticker_data:
                    cache_entry = {
                        "data": ticker_data,
                        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                    }
                    doc_id = f"{self.doc_id_prefix}{ticker}_{period}_{interval}"
                    await self.storage.save(self.collection, doc_id, cache_entry)

        return results

    async def get_return_metrics(self, tickers: List[str], period: str = "1y") -> Dict[str, Any]:
        """
        Calculates annual return and volatility for given tickers based on historical data.
        """
        history = await self.get_historical_data(tickers, period=period)
        metrics = {}

        for ticker, data in history.items():
            if not data or len(data) < 2:
                metrics[ticker] = {"annual_return": 0.0, "annual_volatility": 0.0, "last_price": 0.0}
                continue

            df = pd.DataFrame(data)
            
            # Robust date conversion
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df.dropna(subset=['date'], inplace=True)
            
            if df.empty:
                metrics[ticker] = {"annual_return": 0.0, "annual_volatility": 0.0, "last_price": 0.0}
                continue
                
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            
            prices = df['close'].dropna()
            if prices.empty or len(prices) < 2:
                metrics[ticker] = {"annual_return": 0.0, "annual_volatility": 0.0, "last_price": 0.0}
                continue

            daily_returns = prices.pct_change().dropna()
            if daily_returns.empty:
                metrics[ticker] = {"annual_return": 0.0, "annual_volatility": 0.0, "last_price": 0.0}
                continue
            
            mean_daily_return = daily_returns.mean()
            std_daily_return = daily_returns.std()
            
            annual_return = (1 + mean_daily_return) ** 252 - 1
            annual_volatility = std_daily_return * (252 ** 0.5)
            
            metrics[ticker] = {
                "annual_return": float(annual_return),
                "annual_volatility": float(annual_volatility),
                "last_price": float(prices.iloc[-1]),
                "count": len(prices)
            }

        return metrics

    async def get_dividend_history(
        self,
        tickers: List[str],
        period: str = "5y"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetches dividend history for given tickers.
        Returns list of dividend payments with dates and amounts.
        """
        results = {}
        tickers_to_fetch = []

        # Check cache first
        for ticker in tickers:
            doc_id = f"{self.doc_id_prefix}div_{ticker}_{period}"
            cached_data = await self.storage.get(self.collection, doc_id)

            if cached_data:
                last_updated_str = cached_data.get("updated_at")
                if last_updated_str:
                    try:
                        last_updated = datetime.datetime.fromisoformat(last_updated_str)
                        if last_updated.tzinfo is None:
                            last_updated = last_updated.replace(tzinfo=datetime.timezone.utc)
                        if datetime.datetime.now(datetime.timezone.utc) - last_updated < datetime.timedelta(hours=self.ttl_hours):
                            results[ticker] = cached_data.get("data", [])
                            continue
                    except (ValueError, TypeError):
                        pass

            tickers_to_fetch.append(ticker)

        # Fetch from yfinance
        for ticker in tickers_to_fetch:
            try:
                ticker_obj = yf.Ticker(ticker)
                dividends = ticker_obj.dividends

                if dividends.empty:
                    results[ticker] = []
                    continue

                dividend_data = []
                for date, amount in dividends.items():
                    dividend_data.append({
                        "date": date.isoformat(),
                        "amount": float(amount)
                    })

                results[ticker] = dividend_data

                # Cache the results
                cache_entry = {
                    "data": dividend_data,
                    "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
                doc_id = f"{self.doc_id_prefix}div_{ticker}_{period}"
                await self.storage.save(self.collection, doc_id, cache_entry)

            except Exception as e:
                # Log error if logger available
                results[ticker] = []

        return results

    async def get_fundamental_data(
        self,
        tickers: List[str],
        fields: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetches fundamental data for given tickers.
        Default fields: marketCap, trailingPE, dividendYield, etc.
        Uses longer TTL (7 days) as fundamentals change slowly.
        """
        # Default fundamental fields if none specified
        default_fields = [
            "marketCap", "trailingPE", "forwardPE", "pegRatio",
            "priceToBook", "dividendYield", "beta",
            "52WeekChange", "enterpriseValue", "profitMargins"
        ]

        if fields is None:
            fields = default_fields

        results = {}
        tickers_to_fetch = []

        # Use longer TTL for fundamentals (7 days)
        fundamentals_ttl = self.ttl_hours * 7

        for ticker in tickers:
            doc_id = f"{self.doc_id_prefix}fund_{ticker}"
            cached_data = await self.storage.get(self.collection, doc_id)

            if cached_data:
                last_updated_str = cached_data.get("updated_at")
                if last_updated_str:
                    try:
                        last_updated = datetime.datetime.fromisoformat(last_updated_str)
                        if last_updated.tzinfo is None:
                            last_updated = last_updated.replace(tzinfo=datetime.timezone.utc)
                        if datetime.datetime.now(datetime.timezone.utc) - last_updated < datetime.timedelta(hours=fundamentals_ttl):
                            results[ticker] = cached_data.get("data", {})
                            continue
                    except (ValueError, TypeError):
                        pass

            tickers_to_fetch.append(ticker)

        # Fetch from yfinance
        for ticker in tickers_to_fetch:
            try:
                ticker_obj = yf.Ticker(ticker)
                info = ticker_obj.info

                fundamental_data = {}
                for field in fields:
                    fundamental_data[field] = info.get(field, None)

                # Add metadata
                fundamental_data["_metadata"] = {
                    "shortName": info.get("shortName", ""),
                    "longName": info.get("longName", ""),
                    "currency": info.get("currency", "USD"),
                    "exchange": info.get("exchange", ""),
                    "market": info.get("market", "")
                }

                results[ticker] = fundamental_data

                # Cache the results
                cache_entry = {
                    "data": fundamental_data,
                    "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
                doc_id = f"{self.doc_id_prefix}fund_{ticker}"
                await self.storage.save(self.collection, doc_id, cache_entry)

            except Exception as e:
                results[ticker] = {}

        return results

    async def get_complete_etf_data(
        self,
        tickers: List[str],
        period: str = "5y",
        include_dividends: bool = True,
        include_fundamentals: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetches complete ETF data including OHLCV, dividends, and fundamentals.
        Returns aggregated data structure.
        """
        ohlcv_data = await self.get_historical_data(tickers, period=period)

        result = {}
        for ticker in tickers:
            result[ticker] = {
                "ohlcv": ohlcv_data.get(ticker, []),
                "dividends": [],
                "fundamentals": {}
            }

        if include_dividends:
            dividend_data = await self.get_dividend_history(tickers, period=period)
            for ticker, data in dividend_data.items():
                if ticker in result:
                    result[ticker]["dividends"] = data

        if include_fundamentals:
            fundamental_data = await self.get_fundamental_data(tickers)
            for ticker, data in fundamental_data.items():
                if ticker in result:
                    result[ticker]["fundamentals"] = data

        return result

    async def get_history(self, ticker: str, period: str = "2y") -> Optional[pd.DataFrame]:
        """
        Fetch historical data as DataFrame for analysis.

        Args:
            ticker: Ticker symbol
            period: Historical period

        Returns:
            DataFrame with OHLCV data or None
        """
        data = await self.get_historical_data([ticker], period=period)

        if ticker not in data or not data[ticker]:
            return None

        df = pd.DataFrame(data[ticker])
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)

        # Capitalize column names for consistency
        df.columns = [col.capitalize() for col in df.columns]

        return df

    async def get_technical_indicators(
        self,
        tickers: List[str],
        indicators: Optional[List[str]] = None,
        period: str = "1y"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate technical indicators using pandas-ta.

        Args:
            tickers: List of ticker symbols
            indicators: List of indicators to calculate (default: all)
            period: Historical period for calculation

        Returns:
            Dict of {ticker: {indicator: value}}
        """
        if not PANDAS_TA_AVAILABLE:
            return {
                ticker: {"error": "pandas-ta not available. Install with: pip install pandas-ta"}
                for ticker in tickers
            }

        if indicators is None:
            indicators = ["RSI", "MACD", "BBANDS", "SMA", "EMA", "ADX", "ATR"]

        results = {}

        for ticker in tickers:
            df = await self.get_history(ticker, period=period)

            if df is None or df.empty:
                results[ticker] = {"error": "No historical data available"}
                continue

            try:
                ticker_indicators = self._calculate_indicators(df, indicators)
                results[ticker] = ticker_indicators

            except Exception as e:
                results[ticker] = {"error": f"Failed to calculate indicators: {str(e)}"}

        return results

    def _calculate_indicators(
        self,
        df: pd.DataFrame,
        indicators: List[str]
    ) -> Dict[str, Any]:
        """Calculate technical indicators on DataFrame."""
        result = {}

        # Ensure we have the required columns
        if len(df.columns) < 4:
            return {"error": "Insufficient OHLCV data"}

        # Trend Indicators
        if "SMA" in indicators or "EMA" in indicators:
            if len(df) >= 50:
                result["sma_50"] = float(df["Close"].tail(50).mean())
                result["sma_200"] = float(df["Close"].tail(200).mean()) if len(df) >= 200 else None

            if len(df) >= 20:
                result["ema_20"] = float(df["Close"].tail(20).ewm(span=20, adjust=False).mean())

        # Momentum: RSI
        if "RSI" in indicators and len(df) >= 15:
            rsi_period = 14
            delta = df["Close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            result["rsi"] = float(rsi.iloc[-1])

        # Momentum: MACD
        if "MACD" in indicators and len(df) >= 26:
            ema_12 = df["Close"].ewm(span=12, adjust=False).mean()
            ema_26 = df["Close"].ewm(span=26, adjust=False).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            histogram = macd_line - signal_line

            result["macd"] = {
                "value": float(macd_line.iloc[-1]),
                "signal": float(signal_line.iloc[-1]),
                "histogram": float(histogram.iloc[-1]),
            }

        # Volatility: Bollinger Bands
        if "BBANDS" in indicators and len(df) >= 20:
            sma_20 = df["Close"].rolling(window=20).mean()
            std_20 = df["Close"].rolling(window=20).std()
            upper_band = sma_20 + (2 * std_20)
            lower_band = sma_20 - (2 * std_20)

            current_price = float(df["Close"].iloc[-1])
            result["bollinger_bands"] = {
                "upper": float(upper_band.iloc[-1]),
                "middle": float(sma_20.iloc[-1]),
                "lower": float(lower_band.iloc[-1]),
                "bandwidth": float(
                    (upper_band.iloc[-1] - lower_band.iloc[-1]) / sma_20.iloc[-1]
                ),
                "position": self._get_bb_position(current_price, upper_band.iloc[-1], lower_band.iloc[-1]),
            }

        # Trend Strength: ADX (if High/Low available)
        if "ADX" in indicators and "High" in df.columns and "Low" in df.columns and len(df) >= 14:
            # Simplified ADX calculation
            high = df["High"]
            low = df["Low"]
            close = df["Close"]

            plus_dm = high.diff()
            minus_dm = -low.diff()
            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm < 0] = 0

            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            atr = tr.rolling(window=14).mean()
            plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)

            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=14).mean()

            result["adx"] = {
                "value": float(adx.iloc[-1]),
                "plus_di": float(plus_di.iloc[-1]),
                "minus_di": float(minus_di.iloc[-1]),
                "trend_strength": self._get_adx_trend(adx.iloc[-1]),
            }

        # Volatility: ATR
        if "ATR" in indicators and "High" in df.columns and "Low" in df.columns and len(df) >= 14:
            high = df["High"]
            low = df["Low"]
            close = df["Close"]

            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean()

            result["atr"] = {
                "value": float(atr.iloc[-1]),
                "percent": float(atr.iloc[-1] / close.iloc[-1]),
            }

        return result

    def _get_bb_position(self, price: float, upper: float, lower: float) -> str:
        """Determine price position relative to Bollinger Bands."""
        if price >= upper:
            return "above_upper"
        elif price <= lower:
            return "below_lower"
        else:
            mid = (upper + lower) / 2
            if price > mid:
                return "upper_half"
            else:
                return "lower_half"

    def _get_adx_trend(self, adx: float) -> str:
        """Classify trend strength based on ADX value."""
        if adx >= 50:
            return "strong_trend"
        elif adx >= 25:
            return "trending"
        elif adx >= 20:
            return "weak_trend"
        else:
            return "ranging"

    async def get_market_regime(
        self,
        tickers: List[str],
        period: str = "1y"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Detect current market regime using technical indicators.

        Args:
            tickers: List of ticker symbols
            period: Historical period for analysis

        Returns:
            Dict of {ticker: regime_info}
        """
        indicators = await self.get_technical_indicators(
            tickers,
            indicators=["SMA", "RSI", "MACD", "BBANDS", "ADX"],
            period=period
        )

        results = {}

        for ticker, data in indicators.items():
            if "error" in data:
                results[ticker] = {"error": data["error"]}
                continue

            # Detect trend
            trend = self._detect_trend(data)

            # Detect volatility regime
            volatility = self._detect_volatility_regime(data)

            # Detect support/resistance
            sr = self._detect_support_resistance(data)

            # Overall market sentiment
            sentiment = self._assess_sentiment(data)

            results[ticker] = {
                "trend": trend,
                "volatility_regime": volatility,
                "support_resistance": sr,
                "sentiment": sentiment,
            }

        return results

    def _detect_trend(self, indicators: Dict[str, Any]) -> Dict[str, str]:
        """Detect trend direction and strength."""
        trend = {
            "direction": "sideways",
            "strength": "weak",
        }

        # SMA crossover analysis
        if "sma_50" in indicators and "sma_200" in indicators:
            if indicators["sma_50"] and indicators["sma_200"]:
                if indicators["sma_50"] > indicators["sma_200"]:
                    trend["direction"] = "uptrend"
                else:
                    trend["direction"] = "downtrend"

        # ADX trend strength
        if "adx" in indicators:
            trend["strength"] = indicators["adx"]["trend_strength"]

        return trend

    def _detect_volatility_regime(self, indicators: Dict[str, Any]) -> str:
        """Detect volatility regime from indicators."""
        if "bollinger_bands" not in indicators:
            return "unknown"

        bb = indicators["bollinger_bands"]
        bandwidth = bb["bandwidth"]

        if bandwidth > 0.05:
            return "high"
        elif bandwidth > 0.03:
            return "normal"
        else:
            return "low"

    def _detect_support_resistance(self, indicators: Dict[str, Any]) -> Dict[str, float]:
        """Detect support and resistance levels."""
        sr = {
            "support": None,
            "resistance": None,
        }

        if "bollinger_bands" in indicators:
            bb = indicators["bollinger_bands"]
            sr["support"] = bb["lower"]
            sr["resistance"] = bb["upper"]

        return sr

    def _assess_sentiment(self, indicators: Dict[str, Any]) -> str:
        """Assess overall market sentiment."""
        score = 0

        # RSI sentiment
        if "rsi" in indicators:
            rsi = indicators["rsi"]
            if rsi > 70:
                score += 2  # Overbought - bearish signal
            elif rsi < 30:
                score -= 2  # Oversold - bullish signal
            elif rsi > 50:
                score += 1  # Slightly bullish
            else:
                score -= 1  # Slightly bearish

        # MACD sentiment
        if "macd" in indicators:
            macd = indicators["macd"]
            if macd["histogram"] > 0:
                score += 1  # Bullish
            else:
                score -= 1  # Bearish

        # Classify overall sentiment
        if score >= 3:
            return "very_bullish"
        elif score >= 1:
            return "bullish"
        elif score <= -3:
            return "very_bearish"
        elif score <= -1:
            return "bearish"
        else:
            return "neutral"

