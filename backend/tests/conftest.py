
import os
import pytest
from dotenv import load_dotenv

@pytest.fixture(scope="session", autouse=True)
def load_test_env():
    """
    Automatically load .env.test before any tests run.
    This ensures all external APIs are disabled and mocks are used.
    """
    env_test_path = os.path.join(os.path.dirname(__file__), "..", ".env.test")
    if os.path.exists(env_test_path):
        print(f"Loading test environment from {env_test_path}")
        load_dotenv(env_test_path, override=True)
    else:
        print("WARNING: .env.test not found. Mocking might depend on existing env vars.")

@pytest.fixture(autouse=True)
def clear_dependency_cache():
    """
    Clear dependency cache before each test to ensure
    env var changes (if any) are respected and mocks are fresh.
    """
    from app.core import dependencies
    dependencies.get_history_service.cache_clear()
    dependencies.get_news_service.cache_clear()
    dependencies.get_llm_service.cache_clear()
    dependencies.get_auth_service.cache_clear()
    dependencies.get_currency_service.cache_clear()
    dependencies.get_config_service.cache_clear()

@pytest.fixture
def storage():
    from app.infrastructure.storage.firestore_storage import FirestoreStorage
    return FirestoreStorage()

@pytest.fixture
def logger():
    from app.infrastructure.logging.std_logger import StdLogger
    return StdLogger()

@pytest.fixture
def history_service(storage, logger):
    from app.services.history_service import HistoryService
    from app.services.history.mock_history_provider import MockHistoryProvider
    return HistoryService(storage, logger, MockHistoryProvider())
