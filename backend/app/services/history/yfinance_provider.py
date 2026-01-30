
import yfinance as yf
import pandas as pd
import datetime
import logging
from typing import List, Dict, Any, Optional
from .history_provider import HistoryDataProvider

logger = logging.getLogger(__name__)

class YFinanceProvider(HistoryDataProvider):
    """Deep implementation of history provider using yfinance."""
    
    def download_data(self, tickers: List[str], period: str = "1y", interval: str = "1d") -> Any:
        logger.info(f"Fetching data from yfinance for {len(tickers)} tickers: {tickers}")
        return yf.download(tickers, period=period, interval=interval, group_by='ticker', auto_adjust=True, threads=True)

    def get_dividends(self, tickers: List[str], period: str = "5y") -> Dict[str, List[Dict[str, Any]]]:
        results = {}
        
        for ticker in tickers:
            try:
                ticker_obj = yf.Ticker(ticker)
                dividends = ticker_obj.dividends

                if dividends.empty:
                    results[ticker] = []
                    continue

                start_date = None
                if period == "1y":
                    start_date = pd.Timestamp.now(datetime.timezone.utc) - pd.Timedelta(days=365)
                elif period == "2y":
                    start_date = pd.Timestamp.now(datetime.timezone.utc) - pd.Timedelta(days=365*2)
                elif period == "5y":
                    start_date = pd.Timestamp.now(datetime.timezone.utc) - pd.Timedelta(days=365*5)

                dividend_data = []
                for date, amount in dividends.items():
                    # date from yfinance is usually timezone aware
                    if start_date:
                        div_date = date
                        if div_date.tzinfo is None:
                             div_date = div_date.replace(tzinfo=datetime.timezone.utc)
                        if div_date < start_date:
                            continue

                    dividend_data.append({
                        "date": date.isoformat(),
                        "amount": float(amount)
                    })

                results[ticker] = dividend_data

            except Exception as e:
                logger.error(f"Failed to fetch dividends for {ticker}: {e}")
                results[ticker] = []
                
        return results

    def get_fundamentals(self, tickers: List[str], fields: List[str]) -> Dict[str, Dict[str, Any]]:
        results = {}
        for ticker in tickers:
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
            except Exception as e:
                logger.error(f"Failed to fetch fundamentals for {ticker}: {e}")
                results[ticker] = {}
        return results

    def get_latest_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Fetch latest closing prices from Yahoo Finance.
        
        Uses batch download for efficiency.
        """
        prices = {}
        if not tickers:
            return prices
            
        try:
            data = yf.download(tickers, period="1d", progress=False)
            
            for ticker in tickers:
                try:
                    if len(tickers) == 1:
                        # Single ticker returns flat DataFrame
                        if not data.empty:
                            prices[ticker] = float(data['Close'].iloc[-1])
                    else:
                        # Multiple tickers returns MultiIndex columns
                        if ('Close', ticker) in data.columns:
                            val = data['Close'][ticker].iloc[-1]
                            if pd.notna(val):
                                prices[ticker] = float(val)
                except Exception as e:
                    logger.warning(f"Failed to get price for {ticker}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to download prices: {e}")
            
        return prices
