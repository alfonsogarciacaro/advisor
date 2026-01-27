import os
import httpx
from typing import List, Dict, Any
from .news_provider import NewsProvider

class AlphaVantageProvider(NewsProvider):
    def __init__(self):
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.base_url = "https://www.alphavantage.co/query"

    async def get_news_summary(self) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY is not set")

        params = {
            "function": "NEWS_SENTIMENT",
            "apikey": self.api_key,
            "sort": "LATEST",
            "limit": 10
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if "feed" not in data:
                # Handle potential error messages from API
                error_msg = data.get("Note") or data.get("ErrorMessage") or "Unknown error from Alpha Vantage"
                raise Exception(f"Alpha Vantage API error: {error_msg}")

            news_items = []
            for item in data.get("feed", []):
                news_items.append({
                    "title": item.get("title"),
                    "summary": item.get("summary"),
                    "url": item.get("url"),
                    "source": item.get("source"),
                    "time_published": item.get("time_published")
                })
            
            return news_items
