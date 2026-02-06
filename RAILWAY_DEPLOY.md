# Railway Deployment Guide

## Quick Start

1. Push code to GitHub
2. Create Railway project from repo
3. Set environment variables (see below)
4. Railway automatically detects Dockerfile
5. Deploy! ✅

## How It Works

Railway uses `railway.json` configuration without a `startCommand`, allowing it to use the Dockerfile's CMD directly:
- ✅ Railway uses Dockerfile CMD which properly expands `${PORT}` environment variable
- ✅ Only starts: `gunicorn ... web.backend.app:app`
- ❌ Ignores: Procfile's worker and beat entries (only used in other deployments)
- ✅ No Celery errors: Beat never starts, no schedule configuration

The Dockerfile CMD uses shell form which allows proper variable expansion:
```dockerfile
CMD sh -c "gunicorn -w 4 -b 0.0.0.0:${PORT:-5000} web.backend.app:app ..."
```

## Required Environment Variables

```bash
# Required
SECRET_KEY=your-secret-key-here-min-32-chars
JWT_SECRET=your-jwt-secret-here-min-32-chars

# Database (if using PostgreSQL)
DATABASE_URL=postgresql://user:password@host:port/database

# Optional - Redis/Celery (only if you deploy worker/beat separately)
REDIS_URL=redis://host:port/0
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Optional - Storage (S3, Google Drive, Dropbox)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET=

# Optional - Stripe billing
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PUBLISHABLE_KEY=

# Optional - Training providers
HUGGINGFACE_API_KEY=
REPLICATE_API_TOKEN=
RUNPOD_API_KEY=
```

## Deployment Architecture

### Single Service Deployment (Default)

Railway configuration deploys only the web application:

```
railway.json (uses Dockerfile CMD)
  ↓
Dockerfile CMD (shell form with ${PORT:-5000})
  ↓
Only runs: gunicorn (web server)
  ↓
No Celery worker or beat processes
  ↓
No beat schedule errors ✅
```

### Multi-Service Deployment (Optional)

If you need background job processing:

1. **Create three separate Railway services:**
   - **Web Service**: Uses `railway.json` which uses Dockerfile CMD (gunicorn only)
   - **Worker Service**: Override start command to `celery -A web.backend.training.celery_worker worker --loglevel=info`
   - **Beat Service**: Override start command to `python -c "from web.backend.training.celery_worker import configure_beat_schedule; configure_beat_schedule()" && celery -A web.backend.training.celery_worker beat --loglevel=info`

2. **Add Redis service** (required for all three services)

3. **Share environment variables** across all services

## Celery Beat Configuration Fix

### Problem (Fixed)

Previous deployment failed with:
```
TypeError: string indices must be integers, not 'str'
File "celery/beat.py", line 468, in merge_inplace
    entry = self.Entry(**dict(b[key], name=key, app=self.app))
```

**Root cause:** `beat_schedule` config was set to a file path string instead of a dict.

### Solution

1. **Changed configuration in `celery_worker.py` line 65:**
   ```python
   # WRONG (before)
   beat_schedule=os.getenv('CELERY_BEAT_SCHEDULE', '/app/celerybeat/schedule.db')
   
   # CORRECT (after)
   beat_schedule_filename=os.getenv('CELERY_BEAT_SCHEDULE', '/app/celerybeat/schedule.db')
   ```

2. **Added conditional beat configuration function:**
   ```python
   def configure_beat_schedule():
       """Configure beat schedule only when beat worker starts."""
       celery_app.conf.beat_schedule = {
           'cleanup-old-jobs-daily': {
               'task': 'training.cleanup_old_jobs',
               'schedule': 86400.0,
               'args': (7,),
           },
       }
   ```

3. **Updated Procfile beat command:**
   ```
   beat: python -c "from web.backend.training.celery_worker import configure_beat_schedule; configure_beat_schedule()" && celery -A web.backend.training.celery_worker beat --loglevel=info
   ```

This ensures:
- ✅ `beat_schedule_filename` (string) = file path for persistence
- ✅ `beat_schedule` (dict) = task definitions, only set when beat starts
- ✅ No errors when beat is not running

## Verification

### Check Web Service

```bash
# Health check
curl https://your-app.railway.app/api/health

# Expected response
{"status": "healthy", "timestamp": "..."}
```

### Check Logs

```bash
# Railway dashboard → Service → Logs
# Should see:
# ✅ "Starting gunicorn..."
# ✅ "Booting worker..."
# ❌ No "celery" or "beat" messages (correct for web-only deployment)
```

## Troubleshooting

### Issue: Port binding error

**Symptom:**
```
Error: Cannot bind to port
```

**Solution:**
Railway auto-assigns `$PORT`. Make sure:
- Dockerfile uses `${PORT:-5000}`
- railway.json uses `${PORT:-8000}`

### Issue: Health check failing

**Symptom:**
```
Health check timeout
```

**Solution:**
1. Increase `healthcheckTimeout` in `railway.json` (currently 300s)
2. Check `/api/health` endpoint is accessible
3. Verify app starts within timeout period

### Issue: Environment variables not loading

**Symptom:**
```
KeyError: 'SECRET_KEY'
```

**Solution:**
1. Go to Railway dashboard → Variables
2. Add all required variables from list above
3. Redeploy service

## Production Checklist

Before deploying to production:

- [ ] Set all required environment variables
- [ ] Configure database (PostgreSQL recommended)
- [ ] Set up domain/DNS (if needed)
- [ ] Configure CORS for your domain
- [ ] Set `FLASK_ENV=production`
- [ ] Enable HTTPS (Railway auto-enables)
- [ ] Test health check endpoint
- [ ] Monitor logs for errors
- [ ] Set up error tracking (Sentry, etc.)
- [ ] Configure backups for database
- [ ] Test all critical API endpoints

## Scaling

Railway auto-scales based on:
- CPU usage
- Memory usage
- Request volume

Configure in `railway.json`:
```json
{
  "deploy": {
    "numReplicas": 1  // Increase for horizontal scaling
  }
}
```

## Cost Optimization

For minimal Railway costs:
- Use lightweight Dockerfile (current: ~300-500 MB)
- Deploy only web service (no worker/beat unless needed)
- Use Railway's free tier PostgreSQL
- Monitor usage in Railway dashboard

## Support

For issues:
1. Check Railway logs first
2. Review this guide
3. Check GitHub issues: https://github.com/aiparallel0/Web-and-Desktop-Apps/issues
4. Railway docs: https://docs.railway.app

---

**Last Updated:** 2026-02-05  
**Version:** 1.0.0
