from abc import ABC, abstractmethod
from typing import List, Dict, Any

class NewsProvider(ABC):
    @abstractmethod
    async def get_news_summary(self) -> List[Dict[str, Any]]:
        """
        Fetches a summary of the latest financial news.
        Returns a list of dicts with keys: title, summary, url, source, time_published.
        """
        pass
