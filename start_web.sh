#!/bin/bash
# =============================================================================
# Web Server Startup Script
# =============================================================================
# Handles PORT environment variable for deployment platforms that don't
# properly expand ${PORT:-8000} syntax in Procfile
#
# Usage: ./start_web.sh
#
# Environment Variables:
#   PORT - Port to bind to (default: 8000)
# =============================================================================

# Set default PORT if not provided
if [ -z "$PORT" ]; then
    export PORT=8000
    echo "PORT not set, using default: $PORT"
else
    echo "Starting on PORT: $PORT"
fi

# Start gunicorn with proper configuration
exec gunicorn \
    --bind "0.0.0.0:${PORT}" \
    --workers 4 \
    --timeout 120 \
    --keep-alive 5 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    web.backend.app:app
