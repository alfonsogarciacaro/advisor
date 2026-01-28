import os
from functools import lru_cache
from fastapi import Depends
from app.services.agent_service import AgentService
from app.services.news.alpha_vantage_provider import AlphaVantageProvider
from app.services.news.mock_news_provider import MockNewsProvider
from app.services.news_service import NewsService
from app.services.history_service import HistoryService
from app.services.logger_service import LoggerService
from app.infrastructure.logging.std_logger import StdLogger
from app.services.auth_service import AuthService
from app.infrastructure.auth.mock_auth import MockAuthService
from app.services.storage_service import StorageService
from app.infrastructure.storage.firestore_storage import FirestoreStorage

@lru_cache()
def get_logger() -> LoggerService:
    return StdLogger()

@lru_cache()
def get_auth_service() -> AuthService:
    return MockAuthService()

@lru_cache()
def get_storage_service() -> StorageService:
    return FirestoreStorage()

@lru_cache()
def get_news_service() -> NewsService:
    if os.getenv("ALPHA_VANTAGE_API_KEY"):
        provider = AlphaVantageProvider()
    else:
        provider = MockNewsProvider()
    storage = get_storage_service()
    ttl = int(os.getenv("NEWS_TTL_HOURS", "12"))
    return NewsService(provider=provider, storage=storage, ttl_hours=ttl)

@lru_cache()
def get_history_service(
    storage: StorageService = Depends(get_storage_service)
) -> HistoryService:
    return HistoryService(storage)

@lru_cache()
def get_agent_service(
    news_service: NewsService = Depends(get_news_service),
    history_service: HistoryService = Depends(get_history_service)
) -> AgentService:
    logger = get_logger()
    storage = get_storage_service()
    service = AgentService(logger=logger, storage=storage)
    
    # Register Agents
    from app.services.research_agent import ResearchAgent
    
    # Create a dynamic subclass that has the services bound
    class ConfiguredResearchAgent(ResearchAgent):
        def __init__(self, logger: LoggerService, storage: StorageService):
            super().__init__(logger, storage, news_service=news_service, history_service=history_service)

    service.register_agent("research", ConfiguredResearchAgent)
    
    return service
