import os
import uvicorn
import tests.test_utils as test_utils

if __name__ == "__main__":
    import sys
    test_utils.load_test_env()
    if not test_utils.verify_storage_emulator():
        sys.exit(1)
        
    test_utils.clear_test_data_collections()

    # Run the server
    port = os.getenv("BACKEND_PORT", 8001)
    print(f"Starting backend test server on port {port}...")
    uvicorn.run("app.main:app", port=port, reload=False, log_level="info")

