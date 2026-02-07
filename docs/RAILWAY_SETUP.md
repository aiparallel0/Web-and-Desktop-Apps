# Railway Deployment Setup Guide

## Prerequisites
- Railway account
- GitHub repository connected to Railway

## Step-by-Step Setup

### 1. Add PostgreSQL Database (REQUIRED)

Your app needs a database. Railway makes this easy:

1. Go to your Railway project dashboard
2. Click **"+ New"** button
3. Select **"Database"** → **"PostgreSQL"**
4. Railway automatically:
   - Creates the database
   - Sets `DATABASE_URL` environment variable
   - Connects it to your service

**That's it!** Railway handles the configuration automatically.

### 2. Environment Variables (Optional)

The following variables are optional - the app has sensible defaults:

```bash
# Optional: Set environment
FLASK_ENV=production

# Optional: Custom JWT secret (recommended for production)
JWT_SECRET=your-secret-key-min-32-chars

# Optional: Enable debug logging
LOG_LEVEL=DEBUG
```

### 3. Deploy

Push to your main branch or click **"Deploy"** in Railway.

## Troubleshooting

### App won't start - Database connection errors

**Symptom:** Logs show `connection to server at "localhost"` or `unable to open database file`

**Solution:** You forgot to add PostgreSQL database! See Step 1 above.

### Health check failing (503 errors)

**Symptom:** `/api/ready HTTP/1.1" 503`

**Solution:** 
- Check if database is added (Step 1)
- Check logs for specific error messages
- The app will now tell you exactly what's wrong

### Using SQLite instead of PostgreSQL

**Not recommended for production**, but for testing:

```bash
USE_SQLITE=true
DATABASE_URL=sqlite:////tmp/receipt_extractor.db
```

⚠️ **Warning:** SQLite data is lost on container restart!

## Verifying Deployment

Once deployed, test these endpoints:

```bash
# Basic health check
curl https://your-app.railway.app/api/health

# Readiness check (shows database status)
curl https://your-app.railway.app/api/ready

# Database health (detailed metrics)
curl https://your-app.railway.app/api/database/health
```

All should return 200 OK.

## Architecture

```
┌─────────────────┐
│  Railway App    │
│  (Flask)        │
└────────┬────────┘
         │
         │ DATABASE_URL (auto-set)
         │
┌────────▼────────┐
│  PostgreSQL     │
│  (Railway DB)   │
└─────────────────┘
```

Railway automatically injects `DATABASE_URL` connecting your app to the database.
