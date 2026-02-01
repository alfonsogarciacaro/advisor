#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

echo "Starting backend dev server..."
cd "$SCRIPT_DIR/../backend"
uv run --env-file .env.dev --env-file .env.secrets uvicorn app.main:app --reload
