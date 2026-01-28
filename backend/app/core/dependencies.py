import os
from functools import lru_cache
from typing import Any
from fastapi import Depends
from app.services.agent_service import AgentService
from app.services.news.alpha_vantage_provider import AlphaVantageProvider
from app.services.news.mock_news_provider import MockNewsProvider
from app.services.news_service import NewsService
from app.services.history_service import HistoryService
from app.services.config_service import ConfigService
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
def get_history_service() -> HistoryService:
    storage = get_storage_service()
    return HistoryService(storage)

@lru_cache()
def get_config_service() -> ConfigService:
    return ConfigService()

@lru_cache()
def get_forecast_service() -> Any:
    from app.services.forecast_service import ForecastService
    history_service = get_history_service()
    return ForecastService(history_service)

@lru_cache()
def get_forecasting_engine() -> Any:
    from app.services.forecasting_engine import ForecastingEngine
    history_service = get_history_service()
    config_service = get_config_service()
    return ForecastingEngine(history_service, config_service)

@lru_cache()
def get_macro_service() -> Any:
    from app.services.macro_service import MacroService
    storage = get_storage_service()
    return MacroService(storage)

@lru_cache()
def get_risk_calculator() -> Any:
    from app.services.risk_calculators import RiskCalculator
    return RiskCalculator()

@lru_cache()
def get_agent_service(
    news_service: NewsService = Depends(get_news_service),
    history_service: HistoryService = Depends(get_history_service),
    forecast_service: Any = Depends(get_forecast_service),
    forecasting_engine: Any = Depends(get_forecasting_engine),
    macro_service: Any = Depends(get_macro_service),
    risk_calculator: Any = Depends(get_risk_calculator),
    config_service: ConfigService = Depends(get_config_service)
) -> AgentService:
    logger = get_logger()
    storage = get_storage_service()
    service = AgentService(logger=logger, storage=storage)

    # Register Agents
    from app.services.research_agent import ResearchAgent

    # Create a dynamic subclass that has the services bound
    class ConfiguredResearchAgent(ResearchAgent):
        def __init__(self, logger: LoggerService, storage: StorageService):
            super().__init__(
                logger,
                storage,
                news_service=news_service,
                history_service=history_service,
                forecast_service=forecast_service,
                forecasting_engine=forecasting_engine,
                macro_service=macro_service,
                risk_calculator=risk_calculator,
                config_service=config_service
            )

    service.register_agent("research", ConfiguredResearchAgent)

    return service
