import datetime
import pandas as pd
import yfinance as yf
from .storage_service import StorageService
from typing import List, Dict, Any

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
                
                if len(tickers_to_fetch) == 1:
                    df = data
                else:
                    # Multi-index or just standard dict-like access?
                    # yf.download with group_by='ticker' returns a dataframe with MultiIndex columns (Ticker, PriceType)
                    # OR if only one ticker...
                    # Getting data[ticker] from MultiIndex DataFrame returns DataFrame with single level cols
                    try:
                        df = data[ticker]
                    except KeyError:
                        results[ticker] = []
                        continue

                if df.empty:
                    results[ticker] = []
                    continue

                df_reset = df.reset_index()
                
                for _, row in df_reset.iterrows():
                    date_val = row.get('Date')
                    # Check for NaT (Not a Time)
                    if pd.isna(date_val):
                        continue
                        
                    if date_val:
                        # Convert pandas Timestamp to pydatetime or string
                        # date_val might be Timestamp or datetime
                        try:
                            date_str = date_val.isoformat() if hasattr(date_val, 'isoformat') else str(date_val)
                            
                            def sanitize(val):
                                if pd.isna(val):
                                    return None
                                try:
                                    return float(val)
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
                        except Exception as e:
                            # Log warning or skip
                            continue

                results[ticker] = ticker_data

                # Save to cache
                cache_entry = {
                    "data": ticker_data,
                    "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
                doc_id = f"{self.doc_id_prefix}{ticker}_{period}_{interval}"
                await self.storage.save(self.collection, doc_id, cache_entry)

        return results
