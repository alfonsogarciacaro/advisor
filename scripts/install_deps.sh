#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

cd "$SCRIPT_DIR/../backend"
uv sync --extra dev

cd "$SCRIPT_DIR/../frontend"
npm ci
npx playwright install --with-deps
