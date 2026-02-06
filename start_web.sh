#!/bin/bash
# =============================================================================
# Web Server Startup Script
# =============================================================================
# Handles PORT environment variable for deployment platforms that don't
# properly expand ${PORT:-8000} syntax in Procfile
#
# Also handles case where PORT is set to unexpanded shell variable like '$PORT'
#
# Usage: ./start_web.sh
#
# Environment Variables:
#   PORT - Port to bind to (default: 8000)
# =============================================================================

# Set default PORT if not provided or if it's an unexpanded shell variable
# Also handle empty/whitespace-only strings
if [ -z "$PORT" ] || [ "$PORT" = "\$PORT" ] || [ "$PORT" = "\${PORT}" ] || [ -z "$(echo $PORT | tr -d '[:space:]')" ]; then
    export PORT=8000
    echo "PORT not set or invalid (was: '$PORT'), using default: $PORT"
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
