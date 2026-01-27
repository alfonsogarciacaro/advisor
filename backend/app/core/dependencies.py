from functools import lru_cache
from app.services.logger_service import LoggerService
from app.infrastructure.logging.std_logger import StdLogger
from app.services.auth_service import AuthService
from app.infrastructure.auth.mock_auth import MockAuthService
from app.services.storage_service import StorageService
from app.infrastructure.storage.firestore_storage import FirestoreStorage
from app.services.pubsub_service import PubSubService
from app.infrastructure.pubsub.gcp_pubsub import GCPPubSubService

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
