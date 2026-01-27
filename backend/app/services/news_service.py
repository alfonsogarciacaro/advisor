import datetime
from typing import List, Dict, Any, Optional
from .news.news_provider import NewsProvider
from .storage_service import StorageService

class NewsService:
    def __init__(self, provider: NewsProvider, storage: StorageService, ttl_hours: int = 12):
        self.provider = provider
        self.storage = storage
        self.ttl_hours = ttl_hours
        self.collection = "cache"
        self.doc_id = "financial_news"

    async def get_latest_news(self) -> List[Dict[str, Any]]:
        # 1. Check if news in storage
        cached_data = await self.storage.get(self.collection, self.doc_id)
        
        if cached_data:
            # 2. Check if it's fresh
            last_updated_str = cached_data.get("updated_at")
            if last_updated_str:
                last_updated = datetime.datetime.fromisoformat(last_updated_str)
                if datetime.datetime.now(datetime.timezone.utc) - last_updated < datetime.timedelta(hours=self.ttl_hours):
                    return cached_data.get("news", [])

        # 3. If no cached news or not fresh, fetch them
        news = await self.provider.get_news_summary()

        # 4. Save news to storage
        cache_entry = {
            "news": news,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        await self.storage.save(self.collection, self.doc_id, cache_entry)

        return news
