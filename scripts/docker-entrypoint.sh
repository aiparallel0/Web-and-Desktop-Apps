#!/bin/bash
# =============================================================================
# Docker Entrypoint Script - Receipt Extractor
# =============================================================================
# Handles PORT environment variable for deployment platforms like Railway/Koyeb
# that inject PORT at runtime.
#
# Usage: Called automatically by Docker CMD
#
# Environment Variables:
#   PORT - Port to bind to (default: 5000)
#   FLASK_ENV - Flask environment (default: production)
# =============================================================================

set -e

# Use PORT from environment, default to 5000 if not set or invalid
if [ -z "$PORT" ] || [ "$PORT" = "\$PORT" ] || [ "$PORT" = "\${PORT}" ]; then
    PORT=5000
    echo "⚠️  PORT not set or invalid, using default: $PORT"
else
    echo "🚀 Starting Receipt Extractor on port $PORT"
fi

echo "Environment: ${FLASK_ENV:-production}"

# Start Gunicorn with environment-specific configuration
exec gunicorn web.backend.app:app \
    --bind 0.0.0.0:$PORT \
    --workers 4 \
    --timeout 120 \
    --worker-class gevent \
    --keep-alive 5 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
