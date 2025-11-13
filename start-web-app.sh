#!/bin/bash

echo "========================================"
echo "   Receipt Extractor Web App Launcher"
echo "========================================"
echo ""

# Get the directory where the script is located
cd "$(dirname "$0")"

echo "Starting Backend API on port 5000..."
cd web-app/backend
python app.py &
BACKEND_PID=$!
cd ../..

echo "Waiting for backend to start..."
sleep 5

echo "Starting Frontend Server on port 3000..."
cd web-app/frontend
python -m http.server 3000 &
FRONTEND_PID=$!
cd ../..

echo ""
echo "========================================"
echo "   Application Started Successfully!"
echo "========================================"
echo ""
echo "Backend API:  http://localhost:5000"
echo "Frontend App: http://localhost:3000"
echo ""
echo "Opening browser..."
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:3000
elif command -v open > /dev/null; then
    open http://localhost:3000
fi

echo ""
echo "Press Ctrl+C to stop both servers..."

# Trap SIGINT and SIGTERM to cleanup
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Servers stopped. Goodbye!'; exit 0" SIGINT SIGTERM

# Wait for user interrupt
wait
