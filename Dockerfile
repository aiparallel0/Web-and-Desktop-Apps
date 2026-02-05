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

# Create logs directory with proper permissions for non-root user
RUN mkdir -p logs && chown -R receipt:receipt logs

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    PORT=5000

# Expose port
EXPOSE 5000

# Switch to non-root user
USER receipt

HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD sh -c "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-5000}/api/health')\" || exit 1"

# Run gunicorn with optimized settings for Railway
# Reduced workers (2) and threads (4) for Railway's resource constraints
# Use exec form with explicit shell for proper signal handling and variable substitution
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 4 --timeout 120 --log-level info --access-logfile - --error-logfile - web.backend.app:app"]
