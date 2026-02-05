# Railway Deployment Setup

## Quick Deploy

1. Fork or push this repository to GitHub
2. Create new project in Railway
3. Connect GitHub repository
4. Railway will automatically detect Dockerfile
5. Set environment variables (see below)
6. Deploy!

## Required Environment Variables

```bash
# Application
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
PORT=5000  # Railway sets this automatically

# Optional (for Celery workers - deploy as separate service)
REDIS_URL=redis://your-redis-url
CELERY_BEAT_ENABLED=false  # Set to true only on beat service
```

## Architecture

Railway deployment uses **web-only** mode:
- ✅ Flask web application
- ❌ Celery workers (optional, deploy separately)
- ❌ Celery beat (optional, deploy separately)

## If You Need Celery Workers

Deploy as 3 separate Railway services:
1. **Web Service**: Use `Procfile.railway` (web only)
2. **Worker Service**: Use `Procfile` with only worker line
3. **Beat Service**: Use `Procfile` with only beat line + set `CELERY_BEAT_ENABLED=true`

All three services share the same Docker image but run different processes.

## Procfile Configuration

### Procfile.railway (Web-only - for Railway deployment)
```procfile
web: gunicorn -w 4 -b 0.0.0.0:${PORT:-8000} web.backend.app:app --timeout 120 --keep-alive 5 --log-level info
```

### Procfile (Full stack - for local development with Redis)
```procfile
web: gunicorn -w 4 -b 0.0.0.0:${PORT:-8000} web.backend.app:app --timeout 120 --keep-alive 5 --log-level info
worker: celery -A web.backend.training.celery_worker worker --loglevel=info
beat: celery -A web.backend.training.celery_worker beat --loglevel=info --schedule=/tmp/celerybeat-schedule
```

## Deployment Configuration

Railway uses `railway.json` for deployment settings:
- Health check: `/api/health`
- Health check timeout: 300 seconds
- Restart policy: ON_FAILURE
- Max retries: 3

## File Permissions

The Docker container runs as non-root user `receipt` for security. The following directories have write permissions:
- `/app/logs` - Application logs
- `/app/celerybeat` - Celery beat schedule database (if beat is enabled)

## Environment Variables Explained

### CELERY_BEAT_SCHEDULE
Default: `/app/celerybeat/schedule.db`

Location where Celery Beat stores its schedule database. Must be writable by the `receipt` user.

### CELERY_BEAT_ENABLED
Default: `false`

Set to `true` only when running Celery Beat service. This prevents the beat schedule from being configured when beat isn't actually running, which avoids permission errors.

## Troubleshooting

### Issue: "Permission denied: 'celerybeat-schedule'"

**Solution**: Ensure you're using the correct Procfile:
- Railway deployment: Should use `Procfile.railway` (web-only)
- Local with Celery: Use standard `Procfile` with Redis configured

### Issue: Railway starts all Procfile processes

**Solution**: Railway automatically uses `Procfile.railway` when available, which only starts the web process.

### Issue: Health check fails

**Cause**: The `/api/health` endpoint is not responding.

**Solution**: 
- Check logs in Railway dashboard
- Verify `PORT` environment variable is set
- Ensure health check timeout is sufficient (300s)

## Testing Locally

### Test web-only (simulates Railway):
```bash
docker build -t receipt-app .
docker run -p 5000:5000 -e PORT=5000 receipt-app gunicorn -w 4 -b 0.0.0.0:5000 web.backend.app:app
```

### Test with Celery (requires Redis):
```bash
# Start Redis first
docker run -d -p 6379:6379 redis:alpine

# Start web service
docker run -p 5000:5000 -e PORT=5000 -e REDIS_URL=redis://host.docker.internal:6379/0 receipt-app

# Start worker (in another terminal)
docker run -e REDIS_URL=redis://host.docker.internal:6379/0 receipt-app celery -A web.backend.training.celery_worker worker

# Start beat (in another terminal)
docker run -e REDIS_URL=redis://host.docker.internal:6379/0 -e CELERY_BEAT_ENABLED=true receipt-app celery -A web.backend.training.celery_worker beat --schedule=/tmp/celerybeat-schedule
```

## Docker Image Optimization

The production Docker image is optimized for size:
- Base image: `python:3.11-slim` (~150MB)
- Lightweight OCR: Tesseract only (no EasyOCR/OpenCV)
- Final image: ~300-500MB

Heavy dependencies removed:
- EasyOCR (~2-3GB)
- OpenCV (~500MB)
- CRAFT detector
- Donut/Florence models

## Security

- ✅ Container runs as non-root user `receipt`
- ✅ Minimal attack surface (slim base image)
- ✅ No unnecessary packages installed
- ✅ Environment variables for secrets (not hardcoded)
- ✅ HTTPS enforced in production

## Support

- **Railway Documentation**: https://docs.railway.app/
- **GitHub Issues**: Report deployment issues
- **Project README**: See main README.md for general setup

---

*Last Updated: 2026-02-05*
