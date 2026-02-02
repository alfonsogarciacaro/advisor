#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
REPO_ROOT="$SCRIPT_DIR/.."

CLONE_ID=0
if [ -f "$SCRIPT_DIR/../.cloneid" ]; then
    CLONE_ID=$(cat "$SCRIPT_DIR/../.cloneid")
    if ! [[ "$CLONE_ID" =~ ^[0-9]+$ ]]; then
        CLONE_ID=0
    fi
fi

export PORT=$((3000 + CLONE_ID))
export BACKEND_PORT=$((8000 + CLONE_ID))
export NEXT_PUBLIC_API_URL="http://localhost:$BACKEND_PORT"

cd "$SCRIPT_DIR/../frontend"
npm run dev -- -p $PORT
