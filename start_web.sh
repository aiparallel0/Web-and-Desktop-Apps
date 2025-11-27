#!/bin/bash
###############################################################################
# Simple Web App Launcher for Receipt Extractor
# Quick start script without extensive dependency checks
###############################################################################

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "Receipt Extractor - Web App Launcher"
echo -e "==========================================${NC}"
echo ""

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Python not found!${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo -e "${GREEN}✓${NC} Using: $($PYTHON_CMD --version)"

# Check if we're in the right directory
if [ ! -d "web-app/backend" ]; then
    echo -e "${RED}❌ Error: web-app/backend directory not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

echo -e "${GREEN}✓${NC} Project directory OK"
echo ""

# Quick dependency check
echo "Checking dependencies..."
$PYTHON_CMD -c "import flask" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Flask installed"
else
    echo -e "${YELLOW}⚠${NC}  Flask not installed"
    echo ""
    echo "Would you like to install dependencies now? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo ""
        echo "Running dependency installer..."
        $PYTHON_CMD check_dependencies.py --auto-install || {
            echo -e "${RED}❌ Installation failed${NC}"
            echo ""
            echo "Try manually:"
            echo "  pip install -r web-app/backend/requirements.txt"
            exit 1
        }
    else
        echo "Continuing anyway (server may not start)..."
    fi
fi

echo ""
echo -e "${BLUE}=========================================="
echo "Starting Backend Server..."
echo -e "==========================================${NC}"
echo ""
echo -e "Backend API: ${GREEN}http://localhost:5000${NC}"
echo -e "Frontend:    ${GREEN}http://localhost:3000${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Start backend in background
cd web-app/backend
$PYTHON_CMD app.py &
BACKEND_PID=$!
cd ../..

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Backend failed to start${NC}"
    echo "Check the error messages above"
    exit 1
fi

echo -e "${GREEN}✓${NC} Backend running (PID: $BACKEND_PID)"
echo ""

# Start frontend server
echo "Starting frontend server..."
cd web-app/frontend
$PYTHON_CMD -m http.server 3000 &
FRONTEND_PID=$!
cd ../..

sleep 2

# Check if frontend started
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Frontend failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo -e "${GREEN}✓${NC} Frontend running (PID: $FRONTEND_PID)"
echo ""

# Try to open browser
echo "Opening browser..."
if command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:3000" 2>/dev/null &
elif command -v open &> /dev/null; then
    open "http://localhost:3000" 2>/dev/null &
else
    echo -e "${YELLOW}⚠${NC}  Could not auto-open browser"
    echo "Please open: http://localhost:3000"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "🚀 Receipt Extractor is Running!"
echo -e "==========================================${NC}"
echo ""
echo -e "Frontend: ${BLUE}http://localhost:3000${NC}"
echo -e "Backend:  ${BLUE}http://localhost:5000${NC}"
echo -e "API:      ${BLUE}http://localhost:5000/api/health${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $BACKEND_PID 2>/dev/null && echo -e "${GREEN}✓${NC} Backend stopped"
    kill $FRONTEND_PID 2>/dev/null && echo -e "${GREEN}✓${NC} Frontend stopped"
    echo ""
    echo "Goodbye!"
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

# Wait for processes
wait
