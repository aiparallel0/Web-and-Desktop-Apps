# Railway Deployment Guide

Complete guide for deploying Receipt Extractor to Railway with health-check validation.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Deployment Steps](#deployment-steps)
4. [Post-Deployment Verification](#post-deployment-verification)
5. [Troubleshooting](#troubleshooting)
6. [Monitoring & Logs](#monitoring--logs)
7. [Scaling & Performance](#scaling--performance)

---

## Pre-Deployment Checklist

Before deploying to Railway, ensure you have:

- ✅ **Railway Account**: Sign up at https://railway.app
- ✅ **GitHub Repository**: Connected to Railway
- ✅ **Environment Variables**: Generated secrets ready
- ✅ **Dockerfile**: Validated and optimized
- ✅ **railway.json**: Configuration file present
- ✅ **Package Structure**: Python packages properly initialized

### Validate Deployment Readiness

Run the deployment readiness script:

```bash
python check_railway_ready.py
```

Expected output:
```
✅ Dockerfile: Valid
✅ railway.json: Valid
✅ Package structure: Valid
✅ Environment docs: Complete
⚠️  Remember to set SECRET_KEY and JWT_SECRET in Railway!
```

---

## Environment Setup

### Step 1: Generate Secrets

Run the secret generation script:

```bash
python generate-secrets.py
```

This generates:
- `SECRET_KEY`: Flask session secret (64 characters)
- `JWT_SECRET`: JWT token signing secret (64 characters)

**IMPORTANT**: Save these values securely - you'll need them in the next step.

### Step 2: Configure Railway Environment Variables

1. Go to Railway dashboard: https://railway.app/dashboard
2. Select your project
3. Click on your service
4. Navigate to **Variables** tab
5. Add the following variables:

#### Required Variables (Critical)

| Variable | Value | Description |
|----------|-------|-------------|
| `SECRET_KEY` | From generate-secrets.py | Flask session secret |
| `JWT_SECRET` | From generate-secrets.py | JWT signing secret |
| `FLASK_ENV` | `production` | Flask environment mode |
| `FLASK_DEBUG` | `False` | Disable debug mode |

#### Auto-Configured by Railway

These are automatically set by Railway - **DO NOT** set them manually:

- `PORT` - Application port (injected by Railway)
- `DATABASE_URL` - PostgreSQL connection (if linked)
- `RAILWAY_ENVIRONMENT` - Deployment environment
- `RAILWAY_GIT_COMMIT_SHA` - Git commit hash
- `RAILWAY_GIT_BRANCH` - Git branch name

#### Optional Variables (Based on Features)

**Payments (Stripe)**:
- `STRIPE_SECRET_KEY` - Stripe API secret key
- `STRIPE_PUBLISHABLE_KEY` - Stripe publishable key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook signing secret

**Email (SendGrid)**:
- `SENDGRID_API_KEY` - SendGrid API key
- `SENDGRID_FROM_EMAIL` - Default sender email

**Cloud Storage**:
- AWS S3: `S3_BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- Google Drive: `GOOGLE_DRIVE_CLIENT_ID`, `GOOGLE_DRIVE_CLIENT_SECRET`
- Dropbox: `DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`

**AI/ML Training**:
- HuggingFace: `HUGGINGFACE_API_TOKEN`
- Replicate: `REPLICATE_API_TOKEN`
- RunPod: `RUNPOD_API_KEY`

---

## Deployment Steps

### Option 1: Automatic Deployment (Recommended)

Railway automatically deploys when you push to your configured branch:

```bash
git add .
git commit -m "Deploy to Railway"
git push origin main
```

Railway will:
1. Detect the push
2. Build using Dockerfile
3. Run health checks
4. Deploy if healthy
5. Keep previous version if deployment fails

### Option 2: Manual Deployment via Dashboard

1. Go to Railway dashboard
2. Select your service
3. Click **Deploy** button
4. Monitor deployment logs

### Deployment Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Build | 3-5 minutes | Docker image build |
| Startup | 30-60 seconds | App initialization |
| Health Check | 10-60 seconds | Health endpoint validation |
| **Total** | **4-7 minutes** | Complete deployment |

---

## Post-Deployment Verification

### 1. Check Deployment Status

In Railway dashboard:
- **Status** should show: ✅ **Deployed**
- **Health** should show: ✅ **Healthy**

### 2. Test Health Endpoint

Get your Railway URL from the dashboard (e.g., `https://your-app.railway.app`), then test:

```bash
# Basic health check
curl https://your-app.railway.app/api/health

# Expected response:
{
  "status": "healthy",
  "service": "receipt-extraction-api",
  "version": "2.0",
  "timestamp": 1707048360.123,
  "port": "5000"
}

# Full health check (with detailed metrics)
curl "https://your-app.railway.app/api/health?full=true"
```

### 3. Test Receipt Extraction

```bash
# Upload and extract a test receipt
curl -X POST https://your-app.railway.app/api/extract \
  -F "image=@test-receipt.jpg" \
  -F "model_id=ocr_tesseract"
```

### 4. Monitor Initial Logs

Watch logs for first 5 minutes:

```bash
# In Railway dashboard → Logs
```

Look for:
- ✅ `Receipt Extraction API - Ready to accept requests`
- ✅ `Startup validation passed`
- ✅ No `STARTUP ERROR` messages
- ✅ Health check requests returning 200

---

## Troubleshooting

### Common Issues & Solutions

#### 1. Health Check Timeout

**Symptoms**:
- Deployment fails with "Health check timeout"
- Logs show app starting but no health check response

**Solutions**:
```bash
# Check if app is listening on correct PORT
# Railway injects PORT variable - don't override it

# Verify in logs:
grep "Port:" railway-logs.txt
# Should show: Port: 5000 (or Railway's assigned port)

# Check railway.json has correct health path:
cat railway.json | grep healthcheckPath
# Should show: "healthcheckPath": "/api/health"
```

#### 2. Missing Environment Variables

**Symptoms**:
- Logs show: `STARTUP ERROR: Missing required environment variable: SECRET_KEY`
- Health endpoint returns 503 with startup_errors

**Solutions**:
```bash
# 1. Generate secrets
python generate-secrets.py

# 2. Add to Railway dashboard → Variables
# SECRET_KEY=<your-generated-secret>
# JWT_SECRET=<your-generated-jwt-secret>

# 3. Redeploy
```

#### 3. Out of Memory (OOM) Errors

**Symptoms**:
- App crashes with exit code 137
- Logs show memory exhaustion

**Solutions**:
```bash
# Default: 2 workers, 4 threads per worker (optimized for 512MB)
# If still OOM, reduce to 1 worker:

# Update Dockerfile CMD to:
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --threads 4 --timeout 120 --log-level info --access-logfile - --error-logfile - web.backend.app:app"]

# Monitor memory in health check:
curl "https://your-app.railway.app/api/health?full=true" | jq '.system.memory_percent_used'
```

#### 4. Database Connection Issues

**Symptoms**:
- `Database connection failed`
- `psycopg2.OperationalError`

**Solutions**:
```bash
# 1. Check if PostgreSQL service is linked
# Railway dashboard → Service → Settings → Add Database

# 2. Verify DATABASE_URL is auto-injected
# Railway dashboard → Variables
# Should see: DATABASE_URL=postgresql://...

# 3. Check database is running
# Railway dashboard → PostgreSQL → Metrics
```

#### 5. Port Binding Issues

**Symptoms**:
- `Address already in use`
- App starts but health check fails

**Solutions**:
```bash
# Ensure you're not setting PORT manually
# Railway auto-injects PORT variable

# Check railway.json doesn't override PORT
# Dockerfile should use: ${PORT:-5000}
```

#### 6. Startup Taking Too Long

**Symptoms**:
- Health check timeout (>600 seconds)
- Logs show slow model initialization

**Solutions**:
```bash
# Models are lazy-loaded by default
# First extraction will be slower

# To preload models (optional):
# Add to Dockerfile before CMD:
# RUN python -c "from web.backend.app import get_model_manager; get_model_manager()"
```

---

## Monitoring & Logs

### Reading Railway Logs

Railway provides real-time logs in the dashboard. Key patterns to watch:

#### Successful Startup
```
Receipt Extraction API - Ready to accept requests
Health endpoint: /api/health
Port: 5000
✅ Startup validation passed
```

#### Health Check Requests
```
GET /api/health - 200 OK (45ms)
```

#### Errors to Watch For
```
❌ STARTUP ERROR: Missing required environment variable: SECRET_KEY
❌ STARTUP ERROR: PORT must be a number, got: invalid
⚠️  STARTUP WARNING: PORT 0 is outside valid range
```

### Log Analysis Commands

From Railway CLI:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# View logs
railway logs

# Follow logs (real-time)
railway logs --follow

# Filter errors
railway logs | grep ERROR

# Filter startup messages
railway logs | grep STARTUP
```

### Setting Up Alerts

Railway can send notifications for:
- Deployment failures
- Health check failures
- High memory usage
- Crash loops

Configure in: Dashboard → Project → Settings → Notifications

---

## Scaling & Performance

### Initial Configuration (Default)

- **Workers**: 2 (Gunicorn)
- **Threads per worker**: 4
- **Memory**: ~300-400 MB
- **CPU**: Shared
- **Disk**: Ephemeral (resets on redeploy)

### Scaling Up Workers

After successful initial deployment, if you need more capacity:

1. **Update Dockerfile** (line 78):
```dockerfile
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 4 --threads 8 --timeout 120 --log-level info --access-logfile - --error-logfile - web.backend.app:app"]
```

2. **Monitor memory usage**:
```bash
curl "https://your-app.railway.app/api/health?full=true" | jq '.system.memory_percent_used'
```

3. **Redeploy**:
```bash
git commit -am "Scale up to 4 workers"
git push origin main
```

### Worker Configuration Guidelines

| Workers | Threads | Memory Usage | Use Case |
|---------|---------|--------------|----------|
| 1 | 2 | ~150-200 MB | Development, low traffic |
| 2 | 4 | ~300-400 MB | **Railway initial deployment (recommended)** |
| 3 | 6 | ~450-550 MB | Medium traffic |
| 4 | 8 | ~600-700 MB | High traffic (may need Railway Pro plan) |

**Formula**: `workers * 100 MB base + threads * 10 MB ≈ Total Memory`

### Performance Optimization Tips

1. **Use Model Lazy Loading** (already enabled):
   - Models load only when first used
   - Reduces startup time and initial memory

2. **Enable Response Caching**:
   - Cache health check responses (5 seconds)
   - Cache model results for duplicate requests

3. **Optimize Tesseract**:
   - Default PSM mode: 6 (assume uniform block of text)
   - For receipts, use PSM 4 (single column)

4. **Monitor Resource Usage**:
   ```bash
   # Check detailed metrics
   curl "https://your-app.railway.app/api/health?full=true"
   ```

---

## Quick Reference

### Essential Commands

```bash
# Generate secrets
python generate-secrets.py

# Validate deployment readiness
python check_railway_ready.py

# Test health endpoint
curl https://your-app.railway.app/api/health

# View Railway logs
railway logs --follow

# Redeploy after changes
git push origin main
```

### Essential URLs

- Railway Dashboard: https://railway.app/dashboard
- Health Endpoint: `https://your-app.railway.app/api/health`
- API Docs: `https://your-app.railway.app/api/docs` (if enabled)

### Support Resources

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: GitHub Issues tab

---

## Rollback Procedure

If deployment fails and you need to rollback:

### Option 1: Railway Dashboard

1. Go to Railway dashboard → Deployments
2. Find previous successful deployment
3. Click **⋮** (three dots)
4. Select **Redeploy**

### Option 2: Git Revert

```bash
# Revert last commit
git revert HEAD

# Push to trigger redeploy
git push origin main
```

### Option 3: Roll Back to Specific Commit

```bash
# Find commit hash of working deployment
git log --oneline

# Revert to that commit
git reset --hard <commit-hash>

# Force push (careful!)
git push --force origin main
```

---

## Success Criteria

Your Railway deployment is successful when:

- ✅ Health endpoint returns 200 within 60 seconds
- ✅ No startup errors in logs
- ✅ Memory usage < 512 MB (for 2 workers)
- ✅ Receipt extraction works correctly
- ✅ Authentication endpoints respond
- ✅ No crash loops (stable for 5+ minutes)

---

## Next Steps

After successful deployment:

1. **Set up custom domain** (Railway dashboard → Settings → Domains)
2. **Configure SSL** (automatic with custom domain)
3. **Enable monitoring** (Railway metrics + external APM)
4. **Set up backups** (if using PostgreSQL)
5. **Configure CI/CD** (GitHub Actions + Railway webhooks)
6. **Load testing** (verify performance under traffic)

---

**Last Updated**: 2024-02-04  
**Railway Configuration**: railway.json v2.0  
**Docker Configuration**: Dockerfile (optimized, 2 workers)
