import os
from google.cloud import firestore
from typing import Dict, Any, Optional, List
from app.services.storage_service import StorageService

class FirestoreStorage(StorageService):
    def __init__(self):
        project_id = os.getenv("GCP_PROJECT_ID", "local-project")
        self.db = firestore.Client(project=project_id)

    async def save(self, collection: str, id: str, data: Dict[str, Any]) -> str:
        doc_ref = self.db.collection(collection).document(id)
        doc_ref.set(data)
        return id

    async def get(self, collection: str, id: str) -> Optional[Dict[str, Any]]:
        doc_ref = self.db.collection(collection).document(id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None

    async def update(self, collection: str, id: str, data: Dict[str, Any]) -> None:
        doc_ref = self.db.collection(collection).document(id)
        doc_ref.update(data)

    async def delete(self, collection: str, id: str) -> None:
        doc_ref = self.db.collection(collection).document(id)
        doc_ref.delete()

    async def list(self, collection: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        query = self.db.collection(collection)
        
        if filters:
            for key, value in filters.items():
                query = query.where(field_path=key, op_string="==", value=value)
                
        docs = query.stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            results.append(data)
        return results
