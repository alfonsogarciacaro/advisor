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
from app.infrastructure.logging.std_logger import StdLogger
from app.services.auth_service import AuthService, JWTAuthService, oauth2_scheme
from app.models.auth import User
from fastapi import HTTPException, status
from app.services.storage_service import StorageService
from app.infrastructure.storage.firestore_storage import FirestoreStorage

@lru_cache()
def get_logger() -> LoggerService:
    return StdLogger()

@lru_cache()
def get_auth_service() -> AuthService:
    from app.services.auth.mock_user_provider import MockUserProvider
    # In the future we can switch based on env var
    user_provider = MockUserProvider() 
    return JWTAuthService(user_provider)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = auth_service.verify_token(token, credentials_exception)
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    token_type = payload.get("type")
    if token_type != "access":
         raise credentials_exception
    
    # We could fetch full user here to verify existence/enabled status
    # user = await auth_service.user_provider.get_user_by_username(username)
    # if not user: raise credentials_exception
    
    role = payload.get("role", "user")
    return User(username=username, role=role)

async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme), # Optional dependency? No, Depends(oauth2_scheme) throws if missing usually unless auto_error=False
    auth_service: AuthService = Depends(get_auth_service)
) -> User | None:
    # oauth2_scheme throws 401 if no token by default. 
    # To make it optional we need auto_error=False in the scheme instantiation.
    # But oauth2_scheme is imported. Let's assume we handle it or use a separate optional scheme if needed.
    # For now, let's just stick to the pattern we had: try/except or re-implement logic.
    # If the previous implementation relied on missing token returning None, implies auto_error=False or handling. 
    # Actually standard OAuth2PasswordBearer(auto_error=True) raises 401.
    return None # TODO: Implement correct optional logic if needed


@lru_cache()
def get_storage_service() -> StorageService:
    return FirestoreStorage()

@lru_cache()
def get_currency_service() -> Any:
    storage_service = get_storage_service()
    logger_service = get_logger()
    
    # Choose provider based on config
    # Default to Mock unless explicitly enabled (Safety first)
    enable_yfinance = os.getenv("ENABLE_YFINANCE", "false").lower() in ["1", "true", "yes"]
    
    if enable_yfinance:
        from app.services.currency.yfinance_currency_provider import YFinanceCurrencyProvider
        provider = YFinanceCurrencyProvider()
    else:
        from app.services.currency.mock_currency_provider import MockCurrencyProvider
        provider = MockCurrencyProvider()
        
    from app.services.currency_service import CurrencyService
    return CurrencyService(storage_service, logger_service, provider)


@lru_cache()
def get_news_service() -> NewsService:
    logger = get_logger()
    if os.getenv("ALPHA_VANTAGE_API_KEY"):
        provider = AlphaVantageProvider()
    else:
        provider = MockNewsProvider()
    storage = get_storage_service()
    ttl = int(os.getenv("NEWS_TTL_HOURS", "12"))
    return NewsService(provider=provider, storage=storage, logger=logger, ttl_hours=ttl)

@lru_cache()
def get_history_service() -> HistoryService:
    from app.services.history.yfinance_provider import YFinanceProvider
    from app.services.history.mock_history_provider import MockHistoryProvider
    
    storage = get_storage_service()
    logger = get_logger()
    
    # Default to Mock unless explicitly enabled (Safety first)
    enable_yfinance = os.getenv("ENABLE_YFINANCE", "false").lower() in ["1", "true", "yes"]
    
    if not enable_yfinance:
        logger.info("Initializing Mock History Provider (ENABLE_YFINANCE=False)")
        provider = MockHistoryProvider()
    else:
        logger.info("Initializing YFinance History Provider")
        provider = YFinanceProvider()
        
    return HistoryService(storage, logger, provider)

@lru_cache()
def get_config_service() -> ConfigService:
    storage = get_storage_service()
    return ConfigService(storage_service=storage)

@lru_cache()
def get_llm_service() -> Any:
    from app.services.llm_service import LLMService
    config = get_config_service()
    storage = get_storage_service()
    return LLMService(config_service=config, storage_service=storage)

@lru_cache()
def get_forecasting_engine() -> Any:
    from app.services.forecasting_engine import ForecastingEngine
    history_service = get_history_service()
    config_service = get_config_service()
    storage_service = get_storage_service()
    logger = get_logger()
    return ForecastingEngine(history_service, logger, config_service, storage_service)

@lru_cache()
def get_macro_service() -> Any:
    from app.services.macro_service import MacroService
    storage = get_storage_service()
    logger = get_logger()
    return MacroService(storage, logger)

@lru_cache()
def get_risk_calculator() -> Any:
    from app.services.risk_calculators import RiskCalculator
    return RiskCalculator()

@lru_cache()
def get_agent_service(
    news_service: NewsService = Depends(get_news_service),
    history_service: HistoryService = Depends(get_history_service),
    llm_service: Any = Depends(get_llm_service),
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
                llm_service=llm_service,
                forecasting_engine=forecasting_engine,
                macro_service=macro_service,
                risk_calculator=risk_calculator,
                config_service=config_service
            )

    service.register_agent("research", ConfiguredResearchAgent)

    return service

@lru_cache()
def get_portfolio_optimizer_service(
    history_service: HistoryService = Depends(get_history_service),
    config_service: ConfigService = Depends(get_config_service),
    storage_service: StorageService = Depends(get_storage_service),
    currency_service: Any = Depends(get_currency_service),
    forecasting_engine: Any = Depends(get_forecasting_engine),
    llm_service: Any = Depends(get_llm_service),
    macro_service: Any = Depends(get_macro_service),
    risk_calculator: Any = Depends(get_risk_calculator)
) -> Any:
    from app.services.portfolio_optimizer import PortfolioOptimizerService
    logger = get_logger()
    return PortfolioOptimizerService(
        history_service,
        config_service,
        storage_service,
        logger,
        currency_service,
        forecasting_engine,
        llm_service,
        macro_service,
        risk_calculator
    )


@lru_cache()
def get_plan_service(
    storage_service: StorageService = Depends(get_storage_service),
    config_service: ConfigService = Depends(get_config_service)
) -> Any:
    from app.services.plan_service import PlanService
    logger = get_logger()
    return PlanService(storage_service, logger, config_service)


@lru_cache()
def get_research_agent(
    news_service: NewsService = Depends(get_news_service),
    history_service: HistoryService = Depends(get_history_service),
    llm_service: Any = Depends(get_llm_service),
    forecasting_engine: Any = Depends(get_forecasting_engine),
    macro_service: Any = Depends(get_macro_service),
    risk_calculator: Any = Depends(get_risk_calculator),
    config_service: ConfigService = Depends(get_config_service)
) -> Any:
    from app.services.research_agent import ResearchAgent
    logger = get_logger()
    storage = get_storage_service()
    return ResearchAgent(
        logger=logger,
        storage=storage,
        news_service=news_service,
        history_service=history_service,
        llm_service=llm_service,
        forecasting_engine=forecasting_engine,
        macro_service=macro_service,
        risk_calculator=risk_calculator,
        config_service=config_service
    )

async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user
