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

export ENABLE_YFINANCE=true
export FIRESTORE_EMULATOR_HOST=localhost:8080
export BACKEND_PORT=$((8000 + CLONE_ID))
export FRONTEND_PORT=$((8100 + CLONE_ID))
export CORS_ORIGINS="http://localhost:$FRONTEND_PORT"
export GCP_PROJECT_ID="finance-advisor$([ "$CLONE_ID" -gt 0 ] && echo "-$CLONE_ID")"

echo "Starting backend dev server..."
echo "  Port: $BACKEND_PORT"
echo "  Firestore: $FIRESTORE_EMULATOR_HOST"
echo "  Project ID: $GCP_PROJECT_ID"

cd "$SCRIPT_DIR/../backend"
uv run --env-file .env uvicorn app.main:app --reload --port $BACKEND_PORT
