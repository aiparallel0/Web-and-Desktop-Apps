# Receipt Extractor Deployment Guide

## Overview

This guide covers deploying the Receipt Extractor application to various cloud platforms.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Local Development](#local-development)
4. [Docker Deployment](#docker-deployment)
5. [Railway Deployment](#railway-deployment)
6. [AWS Deployment](#aws-deployment)
7. [Google Cloud Deployment](#google-cloud-deployment)
8. [Database Setup](#database-setup)
9. [SSL/TLS Configuration](#ssltls-configuration)
10. [Monitoring & Logging](#monitoring--logging)
11. [Scaling](#scaling)

---

## Prerequisites

### Required Software

- Python 3.8+ (3.11 recommended)
- pip or pipenv
- Git
- Docker (for containerized deployment)
- PostgreSQL 13+ (for production)

### Required Accounts

- Cloud provider account (Railway, AWS, GCP, etc.)
- Stripe account (for billing)
- Optional: Sentry, DataDog for monitoring

---

## Environment Configuration

### Required Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Application
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-min-32-chars

# Database
DATABASE_URL=postgresql://user:password@host:5432/receipt_extractor
USE_SQLITE=false

# Authentication
JWT_SECRET=your-jwt-secret-min-32-chars
JWT_ACCESS_TOKEN_EXPIRES=900
JWT_REFRESH_TOKEN_EXPIRES=2592000

# Stripe (Required for billing)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Optional: Cloud Storage
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=

# Optional: Monitoring
SENTRY_DSN=
OTEL_EXPORTER_OTLP_ENDPOINT=
```

### Generating Secrets

```bash
# Generate JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Local Development

### Setup

```bash
# Clone repository
git clone https://github.com/your-org/receipt-extractor.git
cd receipt-extractor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your values

# Initialize database
python -c "from web.backend.database import init_db; init_db()"

# Run development server
python -m web.backend.app
```

### Running Tests

```bash
# Run all tests
pytest tools/tests/ -v

# Run with coverage
pytest tools/tests/ --cov=web --cov=shared --cov-report=html
```

---

## Docker Deployment

### Building the Image

```bash
# Build image
docker build -t receipt-extractor:latest .

# Run container
docker run -p 5000:5000 \
  --env-file .env \
  receipt-extractor:latest
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/receipt_extractor
    depends_on:
      - db
    restart: unless-stopped
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=receipt_extractor
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

---

## Railway Deployment

Railway provides easy deployment with automatic builds.

### Quick Deploy

1. Push code to GitHub
2. Connect Railway to your repository
3. Add environment variables in Railway dashboard
4. Deploy

### Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up

# View logs
railway logs
```

### Railway Configuration

The included `railway.json` configures:
- Build command
- Start command
- Health check endpoint

---

## AWS Deployment

### Elastic Beanstalk

1. Install EB CLI:
```bash
pip install awsebcli
```

2. Initialize:
```bash
eb init -p python-3.11 receipt-extractor
```

3. Create environment:
```bash
eb create production --instance-type t3.medium
```

4. Set environment variables:
```bash
eb setenv FLASK_ENV=production DATABASE_URL=... JWT_SECRET=...
```

5. Deploy:
```bash
eb deploy
```

### ECS with Fargate

1. Build and push Docker image to ECR:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

docker build -t receipt-extractor .
docker tag receipt-extractor:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/receipt-extractor:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/receipt-extractor:latest
```

2. Create ECS task definition and service through AWS Console or Terraform

---

## Google Cloud Deployment

### Cloud Run

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/receipt-extractor

# Deploy to Cloud Run
gcloud run deploy receipt-extractor \
  --image gcr.io/PROJECT_ID/receipt-extractor \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "FLASK_ENV=production"
```

### App Engine

Create `app.yaml`:

```yaml
runtime: python311
entrypoint: gunicorn -b :$PORT web.backend.app:app

env_variables:
  FLASK_ENV: "production"

instance_class: F2

automatic_scaling:
  min_instances: 1
  max_instances: 10
```

```bash
gcloud app deploy
```

---

## Database Setup

### PostgreSQL Setup

```sql
-- Create database
CREATE DATABASE receipt_extractor;

-- Create user
CREATE USER receipt_user WITH ENCRYPTED PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE receipt_extractor TO receipt_user;
```

### Connection String Format

```
postgresql://username:password@host:port/database

# With SSL
postgresql://username:password@host:port/database?sslmode=require
```

### Running Migrations

```bash
# Initialize Alembic (first time only)
alembic init migrations

# Generate migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

---

## SSL/TLS Configuration

### Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com
```

### Nginx Configuration

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Monitoring & Logging

### Sentry Integration

```python
# In app.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.1
)
```

### OpenTelemetry

```bash
# Install dependencies
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp

# Configure endpoint
export OTEL_EXPORTER_OTLP_ENDPOINT=https://your-collector:4318
export OTEL_SERVICE_NAME=receipt-extractor
```

### Prometheus Metrics

Expose `/metrics` endpoint for Prometheus scraping:

```python
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})
```

---

## Scaling

### Horizontal Scaling

- Use multiple Gunicorn workers: `gunicorn -w 4 -b :5000 web.backend.app:app`
- Deploy multiple containers behind a load balancer
- Use Redis for session/rate limit storage

### Vertical Scaling

- Increase instance size for heavy workloads
- Use GPU instances for model inference
- Optimize database with read replicas

### Database Scaling

- Enable connection pooling with PgBouncer
- Use read replicas for heavy read workloads
- Consider sharding for very large datasets

### Caching

```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.getenv('REDIS_URL')
})

@app.route('/api/models')
@cache.cached(timeout=300)
def get_models():
    ...
```

---

## Health Checks

The `/api/health` endpoint provides:
- System status
- Database connectivity
- Memory usage
- Model status

Use this for load balancer health checks and monitoring.

---

## Security Checklist

Before going to production:

- [ ] Set strong `JWT_SECRET` (32+ characters)
- [ ] Enable HTTPS only
- [ ] Set `FLASK_ENV=production`
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable Sentry for error tracking
- [ ] Configure proper database permissions
- [ ] Set up database backups
- [ ] Configure security headers
- [ ] Review and restrict API access

---

## Troubleshooting

### Common Issues

**Database connection fails:**
- Check DATABASE_URL format
- Verify network connectivity
- Check firewall rules

**High memory usage:**
- Reduce `MAX_LOADED_MODELS`
- Increase instance size
- Enable model unloading

**Slow response times:**
- Check database indexes
- Enable caching
- Use faster models

### Getting Help

- Check logs: `docker logs container_name`
- Review `/api/health` endpoint
- Contact support with error details
