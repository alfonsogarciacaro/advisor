import os

def load_test_env():
    """
    Automatically load .env.test to configure environment for testing (mocks, etc)
    """
    from dotenv import load_dotenv

    # Look for .env.test in the backend root (one level up from tests/)
    env_test_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env.test"))
    if os.path.exists(env_test_path):
        print(f"Loading test environment from {env_test_path}")
        load_dotenv(env_test_path, override=True)
    else:
        print("WARNING: .env.test not found!")

    print(f"GCP_PROJECT_ID: {os.environ.get('GCP_PROJECT_ID')}")


def verify_storage_emulator():
    """Health check: verify Firestore emulator is running"""
    import socket

    firestore_host, firestore_port = os.environ.get("FIRESTORE_EMULATOR_HOST", "localhost:8080").split(":")
    firestore_port = int(firestore_port)

    try:
        with socket.create_connection((firestore_host, firestore_port), timeout=2):
            print(f"✓ Firestore emulator is reachable at {firestore_host}:{firestore_port}")
            return True
    except (socket.timeout, OSError) as e:
        print(f"✗ ERROR: Firestore emulator is NOT running at {firestore_host}:{firestore_port}")
        return False


def clear_test_data_collections():
    """Clear all collections that might have stale test data."""
    from google.cloud import firestore

    print("Clearing test data from Firestore emulator...")
    project_id = os.getenv("GCP_PROJECT_ID")
    db = firestore.Client(project=project_id)

    # Collections to clear before tests
    collections_to_clear = [
        "cache",              # Historical data cache
        "optimization_jobs",  # Previous optimization results
        "llm_cache",          # LLM response cache
        "plans",              # Test plans
    ]

    total_deleted = 0

    for collection_name in collections_to_clear:
        print(f"  Clearing '{collection_name}'...")
        try:
            collection_ref = db.collection(collection_name)
            deleted_in_collection = 0

            # Delete in batches to avoid timeout/memory issues
            while True:
                docs = list(collection_ref.limit(100).stream())
                if not docs:
                    break
                
                batch = db.batch()
                for doc in docs:
                    batch.delete(doc.reference)
                batch.commit()
                
                deleted_in_collection += len(docs)
                print(f"    - Deleted batch of {len(docs)}")

            if deleted_in_collection > 0:
                print(f"  ✓ Cleared {deleted_in_collection} documents from '{collection_name}'")
                total_deleted += deleted_in_collection
            else:
                print(f"  - '{collection_name}' already empty")
        except Exception as e:
            print(f"  ✗ Error clearing '{collection_name}': {e}")
            
    print(f"Done! Cleared {total_deleted} documents total.")
    return total_deleted
