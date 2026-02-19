#!/bin/bash
# Development runner for Xcapit Privacy Platform
# Runs both backend API and frontend dashboard

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Xcapit Privacy Platform - Dev Server${NC}"
echo -e "${BLUE}======================================${NC}"

# Check if we're in the right directory
if [ ! -f "sdk/api/server.py" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo -e "${GREEN}Virtual environment activated${NC}"
else
    echo "Error: Virtual environment not found. Run: python -m venv .venv"
    exit 1
fi

# Start backend in background
echo -e "\n${GREEN}Starting backend API on http://localhost:8000${NC}"
python -m sdk.api.server &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend..."
sleep 3

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "Error: Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi
echo -e "${GREEN}Backend is running${NC}"

# Start frontend
echo -e "\n${GREEN}Starting frontend dashboard on http://localhost:5173${NC}"
cd dashboard
npm run dev &
FRONTEND_PID=$!

echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}Development servers are running:${NC}"
echo -e "  Backend API:  http://localhost:8000"
echo -e "  API Docs:     http://localhost:8000/docs"
echo -e "  Dashboard:    http://localhost:5173"
echo -e "${GREEN}======================================${NC}"
echo -e "\nPress Ctrl+C to stop all servers"

# Handle cleanup on exit
cleanup() {
    echo -e "\n${BLUE}Stopping servers...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Servers stopped${NC}"
}

trap cleanup EXIT

# Wait for both processes
wait
