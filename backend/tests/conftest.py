
import pytest
import tests.test_utils as test_utils

def pytest_sessionstart(session):
    test_utils.print_env_vars()
    if not test_utils.verify_storage_emulator():
        pytest.exit("Firestore emulator is not running", returncode=1)
    
    test_utils.clear_test_data_collections()

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
