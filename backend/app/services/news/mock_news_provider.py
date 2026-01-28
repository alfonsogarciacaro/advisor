from typing import List, Dict, Any
from .news_provider import NewsProvider

class MockNewsProvider(NewsProvider):
    async def get_news_summary(self) -> List[Dict[str, Any]]:
        return [
            {
                "title": "Stock Market Reaches New All-Time High",
                "summary": "Major indexes closed at record levels today as tech stocks continued their strong momentum.",
                "url": "https://example.com/news1",
                "source": "Financial Times",
                "time_published": "20260128T090000"
            },
            {
                "title": "Federal Reserve Signals Interest Rate Pause",
                "summary": "The central bank indicated it will keep rates steady in the coming months, citing stable inflation data.",
                "url": "https://example.com/news2",
                "source": "Bloomberg",
                "time_published": "20260128T103000"
            },
            {
                "title": "Global Trade Tensions Ease as New Deal is Negotiated",
                "summary": "Major economies have reached a preliminary agreement to reduce tariffs on consumer goods.",
                "url": "https://example.com/news3",
                "source": "Reuters",
                "time_published": "20260128T114500"
            }
        ]
