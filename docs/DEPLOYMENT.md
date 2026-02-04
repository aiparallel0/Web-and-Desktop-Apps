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

### Horizontal Scaling (Multiple Instances)

**Strategy:** Run multiple application instances behind a load balancer

**Implementation:**

1. **Deploy multiple containers:**
   ```bash
   # Docker Compose example
   docker-compose up --scale web=3
   ```

2. **Configure load balancer:**
   - Use sticky sessions for WebSocket connections
   - Health check: `/api/health` endpoint
   - Load balancing algorithm: Round-robin or least connections

3. **Gunicorn workers per instance:**
   ```bash
   # Calculate optimal workers: (2 x CPU cores) + 1
   gunicorn -w 4 -b :5000 web.backend.app:app
   ```

4. **Shared session storage (Redis):**
   ```python
   # Required for multi-instance deployments
   SESSION_TYPE = 'redis'
   SESSION_REDIS = redis_client
   ```

5. **Database connection pooling:**
   ```bash
   # Per instance
   export DB_POOL_SIZE=10
   export DB_POOL_MAX_OVERFLOW=5
   
   # Total connections: (instances × pool_size) < max_db_connections
   ```

**When to scale horizontally:**
- CPU usage consistently >70%
- Need high availability (multiple instances)
- Geographic distribution required

---

### Vertical Scaling (Larger Instances)

**Strategy:** Increase resources on existing instances

**Scaling Guidelines:**

| User Load | CPU | Memory | Instance Type (AWS) |
|-----------|-----|--------|---------------------|
| 1-50 users | 1-2 cores | 1-2 GB | t3.small |
| 50-200 users | 2-4 cores | 4-8 GB | t3.medium |
| 200-500 users | 4-8 cores | 8-16 GB | t3.large |
| 500-1000 users | 8-16 cores | 16-32 GB | t3.xlarge |
| 1000+ users | Multi-instance | Multi-instance | Horizontal scaling |

**GPU Instances (for AI models):**
```bash
# Significant performance improvement for:
- Florence-2 model
- Donut model
- CRAFT detector

# AWS GPU instances:
- g4dn.xlarge: 4 vCPUs, 16 GB RAM, 1 GPU (NVIDIA T4)
- p3.2xlarge: 8 vCPUs, 61 GB RAM, 1 GPU (NVIDIA V100)
```

**When to scale vertically:**
- Single instance deployment
- Model inference requires more resources
- Memory-intensive operations
- Before implementing horizontal scaling

---

### Database Scaling

#### Connection Pooling with PgBouncer

**Setup:**
```bash
# Install PgBouncer
sudo apt-get install pgbouncer

# Configure /etc/pgbouncer/pgbouncer.ini
[databases]
receipt_extractor = host=localhost port=5432 dbname=receipt_extractor

[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6432
pool_mode = transaction
max_client_conn = 100
default_pool_size = 25
```

**Update application:**
```bash
# Point to PgBouncer instead of PostgreSQL directly
DATABASE_URL=postgresql://user:pass@localhost:6432/receipt_extractor
```

#### Read Replicas

**When to implement:**
- Read/write ratio >80/20
- Database CPU consistently >60%
- Complex reporting queries slow down application

**Setup (PostgreSQL):**
```sql
-- On primary server
CREATE ROLE replicator WITH REPLICATION LOGIN ENCRYPTED PASSWORD 'password';

-- Configure pg_hba.conf
host replication replicator replica_ip/32 md5

-- Create read-only connection in application
READ_DATABASE_URL=postgresql://user:pass@replica:5432/receipt_extractor
```

**Application code:**
```python
from sqlalchemy import create_engine

# Write operations
write_engine = create_engine(os.getenv('DATABASE_URL'))

# Read operations
read_engine = create_engine(os.getenv('READ_DATABASE_URL'))

# Use read replica for queries
@app.route('/api/receipts')
def list_receipts():
    with read_engine.connect() as conn:
        receipts = conn.execute(text("SELECT * FROM receipts"))
```

#### Database Sharding

**When to implement:**
- Database size >500 GB
- Single table >100 million rows
- Horizontal scalability required

**Sharding strategy:**
- Shard by user_id (hash-based)
- Shard by date range (time-based)
- Geographic sharding (region-based)

---

### Caching Strategy

#### Application-Level Caching

**Setup Redis:**
```bash
# Install Redis
docker run -d -p 6379:6379 redis:7-alpine

# Or use managed service
# AWS ElastiCache, Redis Cloud, etc.
```

**Configure Flask-Caching:**
```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    'CACHE_DEFAULT_TIMEOUT': 300
})

# Cache model list (changes infrequently)
@app.route('/api/models')
@cache.cached(timeout=600)
def get_models():
    return jsonify(get_available_models())

# Cache user receipts with key based on user_id
@app.route('/api/receipts')
@cache.cached(timeout=60, key_prefix=lambda: f"receipts_{g.user_id}")
def list_receipts():
    receipts = Receipt.query.filter_by(user_id=g.user_id).all()
    return jsonify([r.to_dict() for r in receipts])

# Invalidate cache on update
@app.route('/api/receipts', methods=['POST'])
def create_receipt():
    receipt = create_new_receipt(request.json)
    cache.delete(f"receipts_{g.user_id}")  # Invalidate cache
    return jsonify(receipt.to_dict())
```

#### CDN for Static Assets

**CloudFlare (Recommended):**
- Free tier available
- Automatic HTTPS
- DDoS protection
- Global CDN

**Configuration:**
```bash
# Update DNS to point to CloudFlare
# Enable caching rules for:
- /static/*
- /images/*
- /assets/*

# Cache headers in application
@app.after_request
def add_cache_headers(response):
    if request.path.startswith('/static/'):
        response.cache_control.max_age = 31536000  # 1 year
    return response
```

#### Database Query Caching

**PostgreSQL query result caching:**
```sql
-- Enable pg_stat_statements
CREATE EXTENSION pg_stat_statements;

-- Identify slow queries for caching
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**Application-level query caching:**
```python
# Cache expensive aggregations
@cache.memoize(timeout=3600)
def get_user_statistics(user_id):
    return db.session.execute(text("""
        SELECT 
            COUNT(*) as total_receipts,
            AVG(confidence) as avg_confidence,
            SUM(items_count) as total_items
        FROM receipts
        WHERE user_id = :user_id
    """), {'user_id': user_id}).fetchone()
```

---

### Auto-Scaling Configuration

#### AWS Auto Scaling

```yaml
# CloudFormation template
AutoScalingGroup:
  Type: AWS::AutoScaling::AutoScalingGroup
  Properties:
    MinSize: 2
    MaxSize: 10
    DesiredCapacity: 2
    HealthCheckGracePeriod: 300
    HealthCheckType: ELB
    TargetGroupARNs:
      - !Ref TargetGroup
    
ScaleUpPolicy:
  Type: AWS::AutoScaling::ScalingPolicy
  Properties:
    AdjustmentType: ChangeInCapacity
    AutoScalingGroupName: !Ref AutoScalingGroup
    Cooldown: 300
    ScalingAdjustment: 2
    
CPUAlarmHigh:
  Type: AWS::CloudWatch::Alarm
  Properties:
    EvaluationPeriods: 2
    Statistic: Average
    Threshold: 70
    Period: 300
    AlarmActions:
      - !Ref ScaleUpPolicy
    MetricName: CPUUtilization
```

#### Kubernetes Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: receipt-extractor-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: receipt-extractor
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
```

---

### Capacity Planning

**Baseline metrics (single instance, t3.medium):**
- Concurrent users: ~50
- Requests/second: ~100
- Average response time: ~200ms
- Database connections: ~15

**Scaling formula:**
```
Required instances = (Peak concurrent users / 50) × 1.5 (buffer)
Database connections = Instances × DB_POOL_SIZE

Example:
- 500 peak users
- Required instances: (500 / 50) × 1.5 = 15 instances
- Database connections needed: 15 × 10 = 150
- Ensure max_connections >150 in PostgreSQL
```

**Growth planning:**
```
Month 1-3:   2-3 instances (startup)
Month 3-6:   4-6 instances (growth)
Month 6-12:  8-12 instances (established)
Month 12+:   Custom scaling based on metrics
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

## Monitoring & Observability

### OpenTelemetry Setup

The application includes OpenTelemetry instrumentation for comprehensive observability.

**Configuration (already implemented):**
```bash
# Environment variables
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_SERVICE_NAME=receipt-extractor
export OTEL_ENVIRONMENT=production
```

**Metrics collected:**
- `receipt.extractions` - Total extractions by model
- `extraction.duration` - Processing time by model
- `extraction.errors` - Errors by type
- `model.confidence` - AI model confidence scores
- HTTP request metrics (automatic)
- Database query metrics (automatic)

---

### Grafana Dashboard Setup

**Option 1: SigNoz (Recommended - All-in-One)**

SigNoz provides OpenTelemetry-native monitoring with built-in dashboards.

**Installation:**
```bash
# Clone SigNoz
git clone https://github.com/SigNoz/signoz.git
cd signoz/deploy

# Deploy with Docker Compose
./install.sh

# Access: http://localhost:3301
```

**Configure application:**
```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://signoz:4318
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
```

**Key Dashboards to Create:**
1. Application Performance Monitoring (APM)
   - Request rate
   - Error rate
   - P50/P95/P99 latency
   - Throughput

2. Receipt Processing Metrics
   - Extractions per minute
   - Model performance comparison
   - Success/failure rates
   - Average confidence scores

3. Infrastructure Metrics
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network throughput

**Option 2: Grafana + Prometheus + Loki**

**Installation:**
```bash
# Docker Compose setup
version: '3'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana
  
  loki:
    image: grafana/loki
    ports:
      - "3100:3100"

volumes:
  grafana-storage:
```

**Prometheus Configuration (prometheus.yml):**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'receipt-extractor'
    static_configs:
      - targets: ['app:5000']
    metrics_path: '/metrics'
```

**Grafana Data Sources:**
1. Add Prometheus: http://prometheus:9090
2. Add Loki: http://loki:3100
3. Add OpenTelemetry: Connect to OTLP endpoint

**Import Pre-built Dashboards:**
- Go to Grafana > Dashboards > Import
- Use dashboard ID: 12900 (OpenTelemetry APM)
- Customize for Receipt Extractor metrics

---

### Key Metrics Dashboard

**Create custom dashboard with these panels:**

#### 1. Application Health
```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

#### 2. Receipt Processing
```promql
# Extractions per minute
rate(receipt_extractions_total[1m])

# Average processing time by model
avg(extraction_duration_seconds) by (model)

# Success rate
sum(receipt_extractions_total{success="true"}) / sum(receipt_extractions_total)
```

#### 3. Database Performance
```promql
# Active connections
pg_stat_database_numbackends

# Query duration
rate(pg_stat_database_blk_read_time[5m])

# Connection pool usage
db_pool_connections / db_pool_size
```

#### 4. System Resources
```promql
# CPU usage
rate(process_cpu_seconds_total[5m]) * 100

# Memory usage
process_resident_memory_bytes / system_memory_bytes * 100

# Disk usage
(node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100
```

---

### Alert Configuration

**Critical Alerts (Immediate Response):**

```yaml
# Alertmanager configuration
groups:
- name: critical
  rules:
  # Application down
  - alert: ApplicationDown
    expr: up{job="receipt-extractor"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Application is down"
      description: "Receipt Extractor has been down for 1 minute"
  
  # High error rate
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value | humanizePercentage }}"
  
  # Database connection pool exhausted
  - alert: DatabasePoolExhausted
    expr: db_pool_connections / db_pool_size > 0.95
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Database connection pool nearly exhausted"
      description: "Pool usage at {{ $value | humanizePercentage }}"

- name: warning
  rules:
  # High response time
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time"
      description: "P95 latency is {{ $value }}s"
  
  # High memory usage
  - alert: HighMemoryUsage
    expr: process_resident_memory_bytes / system_memory_bytes > 0.85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage"
      description: "Memory usage at {{ $value | humanizePercentage }}"
  
  # Disk space low
  - alert: DiskSpaceLow
    expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.15
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Low disk space"
      description: "Only {{ $value | humanizePercentage }} free"
```

**Notification Channels:**
```yaml
# Alertmanager routes
route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'team-notifications'
  routes:
  - match:
      severity: critical
    receiver: 'pagerduty-critical'
  - match:
      severity: warning
    receiver: 'slack-warnings'

receivers:
- name: 'team-notifications'
  email_configs:
  - to: 'team@example.com'

- name: 'pagerduty-critical'
  pagerduty_configs:
  - service_key: '<PAGERDUTY_SERVICE_KEY>'

- name: 'slack-warnings'
  slack_configs:
  - api_url: '<SLACK_WEBHOOK_URL>'
    channel: '#alerts'
```

---

### Log Aggregation

**Loki Configuration:**

```yaml
# promtail-config.yml
server:
  http_listen_port: 9080

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: receipt-extractor
    static_configs:
    - targets:
        - localhost
      labels:
        job: receipt-extractor
        __path__: /var/log/receipt-extractor/*.log
```

**Log Query Examples:**
```logql
# All errors
{job="receipt-extractor"} |= "ERROR"

# Specific user logs
{job="receipt-extractor"} | json | user_id="123"

# Slow requests (>1s)
{job="receipt-extractor"} | json | duration > 1000

# Authentication failures
{job="receipt-extractor"} | json | event="auth_failed"
```

---

### Application Performance Monitoring (APM)

**Sentry Integration (Error Tracking):**

```bash
pip install sentry-sdk[flask]
```

```python
# In web/backend/app.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.1,  # 10% of transactions
    profiles_sample_rate=0.1,
    environment=os.getenv("FLASK_ENV", "production")
)
```

**Features enabled:**
- Automatic error capture
- Performance monitoring
- Release tracking
- User context in errors
- Breadcrumbs for debugging

---

### Uptime Monitoring

**External monitoring services:**

1. **Uptime Robot** (Free tier available)
   - Monitor: https://yourapp.com/api/health
   - Interval: 5 minutes
   - Alert: Email + SMS on downtime

2. **Pingdom**
   - HTTP checks
   - Transaction monitoring
   - Real user monitoring (RUM)

3. **StatusCake**
   - Uptime monitoring
   - Page speed monitoring
   - Virus scanning

**Configure alerts for:**
- HTTP status != 200
- Response time >5 seconds
- SSL certificate expiration (30 days warning)

---

### Monitoring Checklist

**Initial Setup:**
- [ ] OpenTelemetry exporter configured
- [ ] Grafana dashboards created and tested
- [ ] Alert rules configured
- [ ] Notification channels set up (email, Slack, PagerDuty)
- [ ] Log aggregation working
- [ ] Sentry error tracking enabled
- [ ] Uptime monitoring configured

**Daily Checks:**
- [ ] Review error rate (should be <1%)
- [ ] Check P95 latency (should be <500ms)
- [ ] Verify database connection pool usage (<80%)
- [ ] Review recent alerts

**Weekly Reviews:**
- [ ] Analyze slow query logs
- [ ] Review capacity metrics
- [ ] Check for memory leaks (increasing baseline)
- [ ] Review and update alert thresholds

---

## Pre-Deployment Checklist

Use this checklist before EVERY production deployment.

### Security Configuration

- [ ] JWT_SECRET is NOT default value (64+ characters, cryptographically random)
- [ ] SECRET_KEY is NOT default value (32+ characters)
- [ ] FLASK_DEBUG=False and FLASK_ENV=production
- [ ] HTTPS enforced (no HTTP)
- [ ] CORS_ORIGINS set to production domain only

### Database

- [ ] Using PostgreSQL (NOT SQLite)
- [ ] DATABASE_URL configured and tested
- [ ] Migrations run: `alembic upgrade head`
- [ ] Automated backups enabled (daily minimum)
- [ ] Backup restoration tested
- [ ] Connection pooling configured (DB_POOL_SIZE, DB_POOL_MAX_OVERFLOW)
- [ ] Database indexes optimized for common queries

### Domain & SSL

- [ ] Domain name registered and DNS configured
- [ ] SSL certificate active (HTTPS working)
- [ ] HTTP redirects to HTTPS
- [ ] SSL certificate auto-renewal configured

### Payments (if enabled)

- [ ] Using LIVE Stripe keys (sk_live_*, not sk_test_*)
- [ ] STRIPE_WEBHOOK_SECRET configured
- [ ] Webhook endpoint tested with test events
- [ ] Subscription plans configured in Stripe Dashboard

### Monitoring & Observability

- [ ] OpenTelemetry exporter configured (OTEL_EXPORTER_OTLP_ENDPOINT)
- [ ] Grafana dashboards created and tested
- [ ] Alert rules configured for critical metrics
- [ ] Notification channels set up (email, Slack, PagerDuty)
- [ ] Sentry error tracking enabled (SENTRY_DSN)
- [ ] Uptime monitoring active (external service)
- [ ] Log aggregation working (Loki or equivalent)
- [ ] Health check endpoint monitored

### Performance & Load Testing

- [ ] Load testing completed (100+ concurrent users)
- [ ] Performance benchmarks documented (baseline metrics)
- [ ] Response time targets met (<500ms for API endpoints)
- [ ] Database query performance optimized
- [ ] Stress testing completed (breaking point identified)
- [ ] Connection pool handles expected load
- [ ] No memory leaks detected during sustained load

### Operational Readiness

- [ ] Runbooks created for common issues
- [ ] Incident response procedures documented
- [ ] On-call rotation established
- [ ] Escalation procedures defined
- [ ] Disaster recovery plan documented and tested
- [ ] Rollback procedure documented and tested

### Capacity Planning

- [ ] Scaling strategy documented
- [ ] Resource limits configured (CPU, memory)
- [ ] Auto-scaling rules configured (if applicable)
- [ ] Database connection limits appropriate for scale
- [ ] CDN configured for static assets

### Testing

- [ ] All tests passing: `pytest tools/tests/ -v`
- [ ] Performance tests passing: `pytest tools/tests/performance/ -v`
- [ ] Complete user journey tested (registration → payment → extraction)
- [ ] Tested on mobile devices and different browsers
- [ ] Load testing results reviewed and acceptable

### Post-Deployment Validation

**First 15 minutes:**
- [ ] Monitor error rate (< 1%)
- [ ] Check response time (< 500ms)
- [ ] Verify all critical endpoints working
- [ ] Check database connectivity
- [ ] Verify authentication working
- [ ] Test payment flow (if enabled)

**First Hour:**
- [ ] Review application logs for errors
- [ ] Check Sentry for new errors
- [ ] Verify monitoring dashboards updating
- [ ] Test key user workflows
- [ ] Check system resource usage (CPU, memory, disk)

**First 24 Hours:**
- [ ] Monitor sustained performance under real load
- [ ] Review alert activity
- [ ] Check for memory leaks (increasing baseline)
- [ ] Verify backup completion
- [ ] Review slow query log

### Rollback Criteria

Rollback immediately if:
- [ ] Error rate exceeds 5%
- [ ] Critical endpoint non-functional
- [ ] Database corruption detected
- [ ] Security vulnerability exposed
- [ ] Payment processing failing

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
