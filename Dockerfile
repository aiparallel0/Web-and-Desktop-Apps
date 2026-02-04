# =============================================================================
# Receipt Extractor - Production Dockerfile (Optimized for Railway)
# =============================================================================
# Multi-stage build for optimized production image under 2GB

# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .

# Install Python dependencies with minimal extras
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim

# Create non-root user for security
RUN groupadd -r receipt && useradd -r -g receipt receipt

WORKDIR /app

# Install runtime dependencies (minimal for headless OpenCV)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels

# Copy application code
COPY --chown=receipt:receipt . .

# Remove unnecessary files to reduce image size
RUN find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find . -type f -name "*.pyc" -delete && \
    find . -type f -name "*.pyo" -delete && \
    rm -rf tools/tests tests docs/*.md *.md desktop/ logs/ && \
    rm -rf shared/models/craft_detector.py shared/models/donut_model.py 2>/dev/null || true && \
    rm -rf web/backend/training 2>/dev/null || true

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    PORT=5000

# Expose port
EXPOSE 5000

# Switch to non-root user
USER receipt

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run gunicorn with optimized settings for Railway
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 web.backend.app:app
