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
export AUTH_PROVIDER=mock
export FIRESTORE_EMULATOR_HOST=localhost:8080
export BACKEND_PORT=$((8000 + CLONE_ID))
export GCP_PROJECT_ID="test-project$([ "$CLONE_ID" -gt 0 ] && echo "-$CLONE_ID")"

cd "$SCRIPT_DIR/../backend"

# Run pytest with any provided arguments
uv run pytest "$@"