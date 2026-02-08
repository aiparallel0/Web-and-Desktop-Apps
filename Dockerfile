# =============================================================================
# Receipt Extractor - Full-Featured Production Dockerfile
# =============================================================================
# Includes all OCR models and AI dependencies for production deployment

FROM python:3.11-slim

# Create non-root user for security
RUN groupadd -r receipt && useradd -r -g receipt receipt

WORKDIR /app

# Install system dependencies for all OCR models
# Includes Tesseract, OpenGL for OpenCV, and other required libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libpq5 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy full requirements with all dependencies
COPY requirements.txt .

# Install Python packages with no cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=receipt:receipt shared/ ./shared/
COPY --chown=receipt:receipt web/backend/ ./web/backend/
COPY --chown=receipt:receipt web/frontend/ ./web/frontend/

# Cleanup to reduce image size but keep model files
RUN find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find . -type f -name "*.pyc" -delete && \
    find . -type f -name "*.pyo" -delete

# Copy startup script
COPY --chown=receipt:receipt scripts/docker-entrypoint.sh /app/scripts/
RUN chmod +x /app/scripts/docker-entrypoint.sh

# Create logs and celerybeat directories with proper permissions
RUN mkdir -p logs celerybeat && chown -R receipt:receipt logs celerybeat

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    PORT=5000 \
    CELERY_BEAT_SCHEDULE=/app/celerybeat/schedule.db

# Expose port
EXPOSE 5000

# Switch to non-root user
USER receipt

# HEALTHCHECK
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD sh -c "curl -f http://localhost:${PORT:-5000}/api/health || exit 1"

# Use startup script as entrypoint
CMD ["/app/scripts/docker-entrypoint.sh"]
