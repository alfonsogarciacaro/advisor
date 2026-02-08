#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

CLONE_ID=0
if [ -f "$SCRIPT_DIR/../.cloneid" ]; then
    CLONE_ID=$(cat "$SCRIPT_DIR/../.cloneid")
    if ! [[ "$CLONE_ID" =~ ^[0-9]+$ ]]; then
        CLONE_ID=0
    fi
fi

export FAST_OPTIMIZE=true
export ENABLE_YFINANCE=false
export FIRESTORE_EMULATOR_HOST=localhost:8080
export BACKEND_PORT=$((8000 + CLONE_ID))
export FRONTEND_PORT=$((8100 + CLONE_ID))
export CORS_ORIGINS="http://localhost:$FRONTEND_PORT"
export GCP_PROJECT_ID="test-project$([ "$CLONE_ID" -gt 0 ] && echo "-$CLONE_ID")"

# Start the backend server in the background
echo "Starting backend test server..."
cd "$SCRIPT_DIR/../backend"
uv run python start_test_server.py > backend.log 2>&1 &
SERVER_PID=$!

# Wait for server to be ready
echo "Waiting for backend server to start..."
for i in {1..30}; do
    if curl -s http://localhost:$BACKEND_PORT/ > /dev/null 2>&1; then
        echo "Backend server is ready"
        break
    fi
    sleep 0.5
done

# Kill the server on script exit (even on failure or interruption)
trap "kill $SERVER_PID 2>/dev/null" EXIT

export PORT=$FRONTEND_PORT
export NEXT_PUBLIC_API_URL="http://localhost:$BACKEND_PORT"

cd "$SCRIPT_DIR/../frontend"
# Run tests and capture exit code
npx playwright test "$@"
EXIT_CODE=$?

exit $EXIT_CODE
