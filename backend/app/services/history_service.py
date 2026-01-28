import datetime
import pandas as pd
import yfinance as yf
from .storage_service import StorageService
from typing import List, Dict, Any, Optional

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
