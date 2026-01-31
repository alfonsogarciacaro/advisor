
import os
import sys
import socket
import time
import uvicorn

if __name__ == "__main__":
    from dotenv import load_dotenv
    
    # Load .env.test to configure environment for testing (mocks, etc)
    env_test_path = os.path.join(os.path.dirname(__file__), ".env.test")
    if os.path.exists(env_test_path):
        print(f"Loading test environment from {env_test_path}")
        load_dotenv(env_test_path, override=True)
    else:
        print("WARNING: .env.test not found!")

    print("Starting backend for integration tests with mocked services...")
    print(f"GCP_PROJECT_ID: {os.environ.get('GCP_PROJECT_ID')}")
    print(f"FIRESTORE_EMULATOR_HOST: {os.environ.get('FIRESTORE_EMULATOR_HOST')}")

    # Health check: verify Firestore emulator is running
    firestore_host, firestore_port = os.environ.get("FIRESTORE_EMULATOR_HOST", "localhost:8080").split(":")
    firestore_port = int(firestore_port)

    print(f"Checking if Firestore emulator is running at {firestore_host}:{firestore_port}...")
    try:
        with socket.create_connection((firestore_host, firestore_port), timeout=2):
            print(f"✓ Firestore emulator is reachable at {firestore_host}:{firestore_port}")
    except (socket.timeout, OSError) as e:
        print(f"\n✗ ERROR: Firestore emulator is NOT running at {firestore_host}:{firestore_port}")
        sys.exit(1)

    # Run the server
    port = 8001
    print(f"Starting server on port {port}...")
    uvicorn.run("app.main:app", port=port, reload=True, log_level="info")

