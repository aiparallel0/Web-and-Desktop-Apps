#!/bin/bash

###############################################################################
# Receipt Extractor Web App - Single-Click Launcher
#
# This script will:
# 1. Check for Python and dependencies
# 2. Start the backend API server
# 3. Start the frontend web server
# 4. Open your default browser automatically
# 5. Handle graceful shutdown (Ctrl+C)
###############################################################################

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=5000
FRONTEND_PORT=3000
BACKEND_DIR="web-app/backend"
FRONTEND_DIR="web-app/frontend"
LOG_DIR="logs"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Receipt Extractor - Single-Click Launcher${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down servers...${NC}"

    # Kill backend
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo -e "${GREEN}✓ Backend stopped${NC}"
    fi

    # Kill frontend
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo -e "${GREEN}✓ Frontend stopped${NC}"
    fi

    echo -e "${GREEN}Cleanup complete. Goodbye!${NC}"
    exit 0
}

# Set up trap to catch Ctrl+C and other termination signals
trap cleanup SIGINT SIGTERM EXIT

# Check if Python is installed
echo -e "${YELLOW}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed!${NC}"
    echo "Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Found Python $PYTHON_VERSION${NC}"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}✗ pip3 is not installed!${NC}"
    echo "Please install pip3 first."
    exit 1
fi
echo -e "${GREEN}✓ pip3 is available${NC}"

# Check if backend directory exists
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}✗ Backend directory not found: $BACKEND_DIR${NC}"
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}✗ Frontend directory not found: $FRONTEND_DIR${NC}"
    exit 1
fi

# Check and install dependencies
echo ""
echo -e "${YELLOW}Checking Python dependencies...${NC}"
cd "$BACKEND_DIR"

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}✗ requirements.txt not found in $BACKEND_DIR${NC}"
    exit 1
fi

# Install/upgrade dependencies (suppress verbose output)
echo "Installing/updating dependencies (this may take a moment)..."
pip3 install -q -r requirements.txt 2>"$SCRIPT_DIR/$LOG_DIR/pip-install.log"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ Some warnings during installation (check logs/$LOG_DIR/pip-install.log)${NC}"
fi

cd "$SCRIPT_DIR"

# Check if ports are already in use
echo ""
echo -e "${YELLOW}Checking port availability...${NC}"

if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${RED}✗ Port $BACKEND_PORT is already in use!${NC}"
    echo "Please stop the process using port $BACKEND_PORT and try again."
    exit 1
fi

if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${RED}✗ Port $FRONTEND_PORT is already in use!${NC}"
    echo "Please stop the process using port $FRONTEND_PORT and try again."
    exit 1
fi

echo -e "${GREEN}✓ Ports $BACKEND_PORT and $FRONTEND_PORT are available${NC}"

# Start backend server
echo ""
echo -e "${YELLOW}Starting backend API server...${NC}"
cd "$BACKEND_DIR"
python3 app.py > "$SCRIPT_DIR/$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
cd "$SCRIPT_DIR"

# Wait a moment for backend to start
sleep 2

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}✗ Backend failed to start!${NC}"
    echo "Check logs/backend.log for details."
    exit 1
fi

echo -e "${GREEN}✓ Backend API running on http://localhost:$BACKEND_PORT (PID: $BACKEND_PID)${NC}"

# Start frontend server
echo -e "${YELLOW}Starting frontend web server...${NC}"
cd "$FRONTEND_DIR"
python3 -m http.server $FRONTEND_PORT > "$SCRIPT_DIR/$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

# Wait a moment for frontend to start
sleep 1

# Check if frontend is running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}✗ Frontend failed to start!${NC}"
    echo "Check logs/frontend.log for details."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo -e "${GREEN}✓ Frontend web server running on http://localhost:$FRONTEND_PORT (PID: $FRONTEND_PID)${NC}"

# Open browser
echo ""
echo -e "${BLUE}Opening browser...${NC}"
sleep 1

# Try different browser commands (Linux)
if command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:$FRONTEND_PORT" 2>/dev/null
elif command -v gnome-open &> /dev/null; then
    gnome-open "http://localhost:$FRONTEND_PORT" 2>/dev/null
elif command -v firefox &> /dev/null; then
    firefox "http://localhost:$FRONTEND_PORT" 2>/dev/null &
elif command -v chromium-browser &> /dev/null; then
    chromium-browser "http://localhost:$FRONTEND_PORT" 2>/dev/null &
else
    echo -e "${YELLOW}⚠ Could not auto-open browser${NC}"
    echo "Please manually open: http://localhost:$FRONTEND_PORT"
fi

# Display success message
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  🚀 Receipt Extractor is now running!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "  Frontend:  ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
echo -e "  Backend:   ${BLUE}http://localhost:$BACKEND_PORT${NC}"
echo -e "  API Docs:  ${BLUE}http://localhost:$BACKEND_PORT/api/models${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""
echo "Logs are being written to:"
echo "  - logs/backend.log"
echo "  - logs/frontend.log"
echo ""

# Keep script running and monitor processes
while true; do
    # Check if backend is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}Backend process died unexpectedly!${NC}"
        echo "Check logs/backend.log for details."
        break
    fi

    # Check if frontend is still running
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}Frontend process died unexpectedly!${NC}"
        echo "Check logs/frontend.log for details."
        break
    fi

    sleep 2
done

# Cleanup will be called by trap
