import os

def print_env_vars():
    print(f"BACKEND_PORT: {os.environ.get('BACKEND_PORT')}")
    print(f"GCP_PROJECT_ID: {os.environ.get('GCP_PROJECT_ID')}")
    print(f"ENABLE_YFINANCE: {os.environ.get('ENABLE_YFINANCE')}")
    print(f"FIRESTORE_EMULATOR_HOST: {os.environ.get('FIRESTORE_EMULATOR_HOST')}")


def verify_storage_emulator():
    """Health check: verify Firestore emulator is running"""
    import socket

    firestore_host, firestore_port = os.environ.get("FIRESTORE_EMULATOR_HOST").split(":")
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
        "users",              # Test users
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
