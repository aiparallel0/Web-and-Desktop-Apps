# Health Check Configuration for Railway Deployment

## Overview

This document explains the health check configuration for the Receipt Extractor API on Railway.

## Health Check Endpoint

**URL:** `/api/health`

**Method:** `GET`

**Response (Success - 200 OK):**
```json
{
  "status": "healthy",
  "service": "receipt-extraction-api",
  "version": "2.0",
  "timestamp": 1770198498.99
}
```

## Configuration Files

### 1. railway.json

```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 300
  }
}
```

**Key Settings:**
- `builder`: Set to "DOCKERFILE" to use the Dockerfile instead of Nixpacks
- `healthcheckTimeout`: 300 seconds (5 minutes) to allow for app initialization
- `healthcheckPath`: `/api/health` - lightweight endpoint that responds quickly

### 2. Dockerfile

```dockerfile
# Docker's internal health check (complementary to Railway's)
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:$PORT/api/health')" || exit 1

# Gunicorn command - uses Railway's $PORT environment variable
CMD exec gunicorn --bind :$PORT --workers 4 --threads 8 --timeout 120 web.backend.app:app
```

**Key Settings:**
- `start-period`: 120 seconds - allows time for app to initialize before health checks start
- `--bind :$PORT`: Binds to Railway's dynamically assigned PORT
- `workers: 4`: Number of worker processes
- `timeout: 120`: Request timeout in seconds

### 3. web/backend/app.py

The health endpoint is implemented as a fast, lightweight route:

```python
@app.route('/api/health', methods=['GET'])
def health_check() -> Response:
    """
    Health check endpoint with lightweight and full modes.
    
    - Default (fast): Returns basic health status in <100ms
    - Full mode (?full=true): Returns detailed system metrics
    """
    # Basic health check (no parameters) - responds immediately
    if not request.args.get('full', 'false').lower() == 'true':
        return jsonify({
            'status': 'healthy',
            'service': 'receipt-extraction-api',
            'version': '2.0',
            'timestamp': time.time()
        })
    
    # Full health check only runs when explicitly requested
    # ...
```

## Optimization: Lazy ModelManager

To ensure fast startup, the `ModelManager` is loaded lazily:

```python
# Initialize model manager (lazy initialization)
model_manager = None

def get_model_manager() -> ModelManager:
    """Get or initialize the model manager (lazy loading)."""
    global model_manager
    if model_manager is None:
        logger.info("Initializing ModelManager (lazy load)...")
        model_manager = ModelManager(max_loaded_models=3)
        logger.info("ModelManager initialized successfully")
    return model_manager
```

**Benefits:**
- App starts in <1 second
- Health endpoint responds immediately
- Heavy ML models only load when first needed (e.g., during first extraction request)

## Troubleshooting

### Problem: "service unavailable" error

**Possible Causes:**
1. App is taking too long to start (>300 seconds)
2. App is crashing during startup
3. PORT environment variable not properly used
4. Health endpoint not accessible

**Solutions:**
1. Check Railway logs for startup errors
2. Verify `healthcheckTimeout` is sufficient (currently 300s)
3. Ensure Dockerfile uses `--bind :$PORT` in gunicorn command
4. Test health endpoint locally: `curl http://localhost:5000/api/health`

### Problem: Health check times out

**Possible Causes:**
1. App initialization taking too long
2. Heavy imports blocking startup
3. Database connection timeouts

**Solutions:**
1. Review startup logs to identify slow operations
2. Use lazy loading for heavy components (like ModelManager)
3. Increase `healthcheckTimeout` if necessary
4. Optimize imports and database connections

## Testing Locally

### Test with Flask development server:
```bash
cd web/backend
python app.py
curl http://localhost:5000/api/health
```

### Test with gunicorn (production-like):
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 8 web.backend.app:app
curl http://localhost:5000/api/health
```

### Test Docker build:
```bash
docker build -t receipt-extractor .
docker run -p 5000:5000 -e PORT=5000 receipt-extractor
curl http://localhost:5000/api/health
```

## Railway-Specific Notes

1. **PORT Environment Variable**: Railway provides a dynamic `$PORT` variable. Always bind to this port.

2. **Healthcheck Hostname**: Railway uses `healthcheck.railway.app` as the hostname for health checks. The app accepts requests from any hostname, so this works automatically.

3. **Zero-Downtime Deployments**: Railway waits for the health check to pass before routing traffic to the new deployment. This ensures zero downtime during updates.

4. **Retry Window**: Railway retries the health check multiple times within the timeout window (currently 300 seconds). If all attempts fail, the deployment is marked as failed.

## Monitoring

To monitor health check status in Railway:
1. Go to your Railway project dashboard
2. Select the service
3. Click on "Deployments"
4. View the deployment logs to see health check attempts

Look for messages like:
```
====================
Starting Healthcheck
====================
Path: /api/health
Retry window: 300s

✓ Healthcheck passed
```

## Advanced: Full Health Check

For detailed system metrics, use the full health check mode:

```bash
curl http://localhost:5000/api/health?full=true
```

Response includes:
- CPU count
- Memory usage (total, available, percent)
- Disk usage (total, free, percent)
- Python version
- Platform information
- Model manager resource stats

**Note:** Full health check requires `psutil` to be installed (included in requirements-prod.txt).

## Summary

The health check configuration ensures:
- ✅ Fast app startup (<5 seconds typical)
- ✅ Reliable health checks with 300-second timeout
- ✅ Zero-downtime deployments on Railway
- ✅ Clear logging for debugging
- ✅ Graceful handling of optional dependencies

For questions or issues, refer to the Railway documentation:
https://docs.railway.app/guides/healthchecks
