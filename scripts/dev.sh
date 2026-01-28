#!/bin/bash
# Dev mode script - starts emulators + FastAPI + Next.js

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}Starting dev environment...${NC}"

# Start emulators in background
echo -e "${YELLOW}Starting emulators...${NC}"
docker compose --profile emulators up -d

# Wait for emulators to be ready
echo -e "${YELLOW}Waiting for emulators to be ready...${NC}"
sleep 5

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping services...${NC}"
    # Kill background processes
    jobs -p | xargs -r kill 2>/dev/null || true
    # Stop emulators
    docker compose --profile emulators down
    echo -e "${GREEN}Done!${NC}"
}

trap cleanup EXIT INT TERM

# Set environment variables for local development
export GCP_PROJECT_ID=local-project
export FIRESTORE_EMULATOR_HOST=localhost:8080
export PUBSUB_EMULATOR_HOST=localhost:8085

# Start FastAPI with hot reload
echo -e "${GREEN}Starting FastAPI (http://localhost:8000)${NC}"
cd "$PROJECT_ROOT/backend"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
FASTAPI_PID=$!

# Start Next.js dev server
echo -e "${GREEN}Starting Next.js (http://localhost:3000)${NC}"
cd "$PROJECT_ROOT/frontend"
npm run dev &
NEXTJS_PID=$!

echo -e "${GREEN}✓ All services running!${NC}"
echo -e "  - Firestore:  http://localhost:8080"
echo -e "  - PubSub:     http://localhost:8085"
echo -e "  - FastAPI:    http://localhost:8000"
echo -e "  - Next.js:    http://localhost:3000"
echo ""
echo -e "Press Ctrl+C to stop all services"

# Wait for any background process to exit
wait -n
