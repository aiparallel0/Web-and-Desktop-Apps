#!/bin/bash
# Start the web app backend

echo "=========================================="
echo "Starting Receipt Extraction Web App"
echo "=========================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python not found! Please install Python 3."
    exit 1
fi

PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# Check if dependencies are installed
echo "Checking dependencies..."
$PYTHON_CMD -c "import flask; import cv2; import PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Missing core dependencies detected!"
    echo ""
    echo "Running dependency installer..."
    $PYTHON_CMD check_dependencies.py --auto-install
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ Dependency installation failed!"
        echo ""
        echo "Please install dependencies manually:"
        echo "  pip install -r web-app/backend/requirements.txt"
        exit 1
    fi
    echo ""
fi

# Navigate to backend directory
cd web-app/backend || exit 1

echo "✅ Starting Flask server..."
echo ""
echo "📍 Backend: http://localhost:5000"
echo "📍 Frontend: Open web-app/frontend/index.html in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Start the Flask app
$PYTHON_CMD app.py
