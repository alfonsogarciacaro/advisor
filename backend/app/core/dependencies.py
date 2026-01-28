import os
from functools import lru_cache
from app.services.news.alpha_vantage_provider import AlphaVantageProvider
from app.services.news.mock_news_provider import MockNewsProvider
from app.services.news_service import NewsService
from app.services.logger_service import LoggerService
from app.infrastructure.logging.std_logger import StdLogger
from app.services.auth_service import AuthService
from app.infrastructure.auth.mock_auth import MockAuthService
from app.services.storage_service import StorageService
from app.infrastructure.storage.firestore_storage import FirestoreStorage
from app.services.pubsub_service import PubSubService
from app.infrastructure.pubsub.gcp_pubsub import GCPPubSubService
from app.services.agent_service import AgentService

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
def get_pubsub_service() -> PubSubService:
    return GCPPubSubService()

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
def get_agent_service() -> AgentService:
    logger = get_logger()
    storage = get_storage_service()
    service = AgentService(logger=logger, storage=storage)
    
    # Register Agents
    from app.services.research_agent import ResearchAgent
    service.register_agent("research", ResearchAgent)
    
    return service
