import os
import json
from google.cloud import pubsub_v1
from typing import Dict, Any
from app.services.pubsub_service import PubSubService

class GCPPubSubService(PubSubService):
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "local-project")
        self.publisher = pubsub_v1.PublisherClient()

    async def publish(self, topic: str, data: Dict[str, Any]) -> str:
        topic_path = self.publisher.topic_path(self.project_id, topic)
        data_str = json.dumps(data)
        data_bytes = data_str.encode("utf-8")
        
        try:
            future = self.publisher.publish(topic_path, data_bytes)
            return future.result()
        except Exception as e:
            # If topic doesn't exist (common in emulator), create it if local
            if os.getenv("PUBSUB_EMULATOR_HOST"):
                try:
                    self.publisher.create_topic(request={"name": topic_path})
                    future = self.publisher.publish(topic_path, data_bytes)
                    return future.result()
                except Exception as inner_e:
                    print(f"Failed to create topic: {inner_e}")
                    raise inner_e
            raise e
