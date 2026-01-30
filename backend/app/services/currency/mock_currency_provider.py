
import pandas as pd
from typing import Optional
from datetime import datetime
from .currency_provider import CurrencyProvider

class MockCurrencyProvider(CurrencyProvider):
    """
    Mock implementation of currency provider for testing.
    """
    
    # Mock rates relative to USD
    # JPY: ~150, EUR: ~0.92, GBP: ~0.79
    MOCK_RATES = {
        ("USD", "JPY"): 150.0,
        ("EUR", "JPY"): 163.0,  # 150 / 0.92
        ("GBP", "JPY"): 190.0,  # 150 / 0.79
        ("USD", "EUR"): 0.92,
        ("USD", "GBP"): 0.79,
    }

    async def get_current_rate(self, from_currency: str, to_currency: str) -> float:
        if from_currency == to_currency:
            return 1.0
            
        # Try direct
        rate = self.MOCK_RATES.get((from_currency, to_currency))
        if rate:
            return rate
            
        # Try inverse
        inverse_rate = self.MOCK_RATES.get((to_currency, from_currency))
        if inverse_rate:
            return 1.0 / inverse_rate
            
        # Fallback for unknown pairs involving JPY (common base)
        if to_currency == "JPY":
            if from_currency == "USD": return 150.0
            if from_currency == "EUR": return 160.0
            if from_currency == "GBP": return 190.0
            if from_currency == "AUD": return 100.0
            
        if from_currency == "JPY":
            if to_currency == "USD": return 1/150.0
            
        # Default fallback
        raise ValueError(f"Unsupported FX pair: {from_currency}/{to_currency}")

    async def get_historical_rates(
        self,
        from_currency: str,
        to_currency: str,
        start_date: str,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        end = end_date or datetime.now().strftime("%Y-%m-%d")
        dates = pd.date_range(start=start_date, end=end, freq="D")
        
        # Get base rate
        base_rate = await self.get_current_rate(from_currency, to_currency)
        
        # Add some random variation if needed, but constant is fine for mocks
        return pd.DataFrame({
            "date": dates,
            "rate": base_rate
        })
