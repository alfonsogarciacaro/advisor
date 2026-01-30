import os
from google.cloud import firestore
from google.cloud.firestore import FieldFilter
from typing import Dict, Any, Optional, List
from app.services.storage_service import StorageService
from app.services.logger_service import LoggerService
from app.infrastructure.logging.std_logger import StdLogger

class FirestoreStorage(StorageService):
    def __init__(self, logger: Optional[LoggerService] = None):
        project_id = os.getenv("GCP_PROJECT_ID", "local-project")
        self.db = firestore.Client(project=project_id)
        self.logger = logger or StdLogger()

    async def save(self, collection: str, id: str, data: Dict[str, Any]) -> str:
        self.logger.debug(f"Firestore Save: {collection}/{id}")
        doc_ref = self.db.collection(collection).document(id)
        doc_ref.set(data)
        return id

    async def get(self, collection: str, id: str) -> Optional[Dict[str, Any]]:
        self.logger.debug(f"Firestore Get: {collection}/{id}")
        doc_ref = self.db.collection(collection).document(id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None

    async def update(self, collection: str, id: str, data: Dict[str, Any]) -> None:
        self.logger.debug(f"Firestore Update: {collection}/{id}")
        doc_ref = self.db.collection(collection).document(id)
        doc_ref.update(data)

    async def delete(self, collection: str, id: str) -> None:
        self.logger.debug(f"Firestore Delete: {collection}/{id}")
        doc_ref = self.db.collection(collection).document(id)
        doc_ref.delete()

    async def list(self, collection: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        self.logger.debug(f"Firestore List: {collection} filters={filters}")
        query = self.db.collection(collection)
        
        if filters:
            for key, value in filters.items():
                query = query.where(filter=FieldFilter(key, "==", value))
                
        docs = query.stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            results.append(data)
        return results
