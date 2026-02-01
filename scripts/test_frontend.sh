#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)


# Start the backend server in the background
echo "Starting backend test server..."
cd "$SCRIPT_DIR/../backend"
uv run python start_test_server.py > /dev/null 2>&1 &
SERVER_PID=$!

# Wait for server to be ready
echo "Waiting for backend server to start..."
for i in {1..30}; do
    if curl -s http://localhost:8001/ > /dev/null 2>&1; then
        echo "Backend server is ready"
        break
    fi
    sleep 0.5
done

# Kill the server on script exit (even on failure or interruption)
trap "kill $SERVER_PID 2>/dev/null" EXIT

cd "$SCRIPT_DIR/../frontend"
# Run tests and capture exit code
npx playwright test "$@"
EXIT_CODE=$?

exit $EXIT_CODE
