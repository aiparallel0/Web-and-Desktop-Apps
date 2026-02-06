# =============================================================================
# Receipt Extractor - Optimized Lightweight Dockerfile
# =============================================================================
# Single-stage build optimized for minimal image size (~300-500 MB)
# Removes EasyOCR (2-3 GB) and OpenCV (500 MB) for production deployment

FROM python:3.11-slim

# Create non-root user for security
RUN groupadd -r receipt && useradd -r -g receipt receipt

WORKDIR /app

# Install ONLY runtime dependencies in one layer
# Includes Tesseract OCR for lightweight text extraction
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
    curl \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove gcc g++

# Copy only production requirements (lightweight, no EasyOCR/OpenCV)
COPY requirements-prod.txt .

# Install Python packages with no cache to minimize layer size
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy application code (shared, backend, frontend only)
COPY --chown=receipt:receipt shared/ ./shared/
COPY --chown=receipt:receipt web/backend/ ./web/backend/
COPY --chown=receipt:receipt web/frontend/ ./web/frontend/

# Aggressive cleanup to reduce image size
# Remove test files, cache, and heavy unused model processors
RUN find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find . -type f -name "*.pyc" -delete && \
    find . -type f -name "*.pyo" -delete && \
    find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find . -type d -name "test" -exec rm -rf {} + 2>/dev/null || true && \
    rm -rf shared/models/craft_detector.py 2>/dev/null || true && \
    rm -rf shared/models/donut_model.py 2>/dev/null || true && \
    rm -rf shared/models/donut_finetuner.py 2>/dev/null || true && \
    rm -rf shared/models/florence_finetuner.py 2>/dev/null || true && \
    rm -rf shared/models/ocr_finetuner.py 2>/dev/null || true

# Create logs and celerybeat directories with proper permissions for non-root user
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
# ✅ Fixed - Handle unexpanded PORT variable
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD sh -c " \
        if [ -z \"$PORT\" ] || [ \"$PORT\" = \"\$PORT\" ] || [ \"$PORT\" = \"\${PORT}\" ]; then \
            HEALTHCHECK_PORT=5000; \
        else \
            HEALTHCHECK_PORT=$PORT; \
        fi && \
        python -c \"import urllib.request; urllib.request.urlopen('http://localhost:${HEALTHCHECK_PORT}/api/health')\" || exit 1"

# Run gunicorn with optimized settings for Railway
# Sanitize PORT variable before using it (in case it's set to unexpanded '$PORT' string)
CMD sh -c " \
    if [ -z \"$PORT\" ] || [ \"$PORT\" = \"\$PORT\" ] || [ \"$PORT\" = \"\${PORT}\" ]; then \
        export PORT=5000; \
        echo 'PORT not set or invalid, using default: 5000'; \
    fi && \
    gunicorn -w 4 -b 0.0.0.0:${PORT} web.backend.app:app --timeout 120 --keep-alive 5 --log-level info"
