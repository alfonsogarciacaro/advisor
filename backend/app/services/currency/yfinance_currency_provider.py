
import yfinance as yf
import pandas as pd
from typing import Optional
from datetime import datetime, timezone
import logging
from .currency_provider import CurrencyProvider

logger = logging.getLogger(__name__)

class YFinanceCurrencyProvider(CurrencyProvider):
    """
    Implementation of currency provider using yfinance.
    """
    
    # FX pair mappings (yfinance format)
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
    
    async def get_current_rate(self, from_currency: str, to_currency: str) -> float:
        if from_currency == to_currency:
            return 1.0
            
        fx_pair = self.FX_PAIRS.get((from_currency, to_currency))
        
        # If not direct pair found, try inverse
        if not fx_pair:
             # This provider only handles direct lookup for known pairs.
             # The Service layer handles inverse calculation logic if provider fails or returns distinct error.
             # But for simplicity, let's implement basic lookup here.
             pass
             
        # Actually the service layer handled the logic of "try direct, try inverse".
        # The provider should just provide data for a requested pair if possible.
        # But yfinance needs specific tickers. 
        
        # Strategy:
        # 1. Look for direct pair ticker
        # 2. If not found, return None (Service handles inverse/cross logic)
        
        # Ideally the provider interface should be simple: fetch rate for X/Y.
        # If yfinance doesn't have X/Y, we can try Y/X and invert.
        
        ticker_symbol = self.FX_PAIRS.get((from_currency, to_currency))
        inverse = False
        
        if not ticker_symbol:
            ticker_symbol = self.FX_PAIRS.get((to_currency, from_currency))
            inverse = True
            
        if not ticker_symbol:
            raise ValueError(f"Unsupported FX pair: {from_currency}/{to_currency}")
            
        try:
            ticker = yf.Ticker(ticker_symbol)
            data = ticker.history(period="1d")
            
            if data.empty:
                raise ValueError(f"Failed to fetch FX rate for {ticker_symbol}")
                
            rate = float(data['Close'].iloc[-1])
            
            if inverse:
                return 1.0 / rate
            return rate
            
        except Exception as e:
            logger.error(f"Error fetching FX rate {from_currency}/{to_currency}: {e}")
            raise ValueError(f"Failed to fetch FX rate: {e}")

    async def get_historical_rates(
        self,
        from_currency: str,
        to_currency: str,
        start_date: str,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        if from_currency == to_currency:
             end = end_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
             dates = pd.date_range(start=start_date, end=end, freq="D")
             return pd.DataFrame({"date": dates, "rate": 1.0})

        ticker_symbol = self.FX_PAIRS.get((from_currency, to_currency))
        inverse = False
        
        if not ticker_symbol:
            ticker_symbol = self.FX_PAIRS.get((to_currency, from_currency))
            inverse = True
            
        if not ticker_symbol:
             raise ValueError(f"Unsupported FX pair: {from_currency}/{to_currency}")
             
        try:
            ticker = yf.Ticker(ticker_symbol)
            data = ticker.history(start=start_date, end=end_date)

            if data.empty:
                raise ValueError(f"Failed to fetch historical FX data for {ticker_symbol}")

            # Convert to list format
            result_data = []
            for date, row in data.iterrows():
                rate = float(row['Close'])
                if inverse:
                    rate = 1.0 / rate
                    
                result_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "rate": rate
                })

            return pd.DataFrame(result_data)
            
        except Exception as e:
            logger.error(f"Error fetching historical FX rates {from_currency}/{to_currency}: {e}")
            raise ValueError(f"Failed to fetch historical FX rates: {e}")
