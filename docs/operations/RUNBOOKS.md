# Operational Runbooks

Incident response procedures and troubleshooting guides for common production issues.

## Overview

This directory contains runbooks for diagnosing and resolving common operational issues in the Receipt Extractor application.

## Quick Index

### Critical Issues
- [Database Connection Pool Exhaustion](#database-connection-pool-exhaustion)
- [Application Not Responding](#application-not-responding)
- [JWT Signature Verification Failed](#jwt-signature-verification-failed)
- [Stripe Webhook Failures](#stripe-webhook-failures)

### Performance Issues
- [Slow API Response Times](#slow-api-response-times)
- [High Memory Usage](#high-memory-usage)
- [Database Query Timeout](#database-query-timeout)

### Integration Issues
- [Cloud Storage Upload Failures](#cloud-storage-upload-failures)
- [Model Loading Failures](#model-loading-failures)
- [Email Delivery Failures](#email-delivery-failures)

---

## Critical Issues

### Database Connection Pool Exhaustion

**Symptoms:**
- `QueuePool limit exceeded` errors in logs
- `TimeoutError: Connection pool is exhausted` 
- 500 errors on all database-dependent endpoints
- Requests timing out after 30 seconds

**Root Causes:**
- Too many concurrent connections
- Connection leaks (connections not properly closed)
- DB_POOL_SIZE too small for traffic
- Long-running queries holding connections

**Diagnosis:**

```bash
# Check active database connections
psql -d receipt_extractor -c "SELECT count(*) FROM pg_stat_activity;"

# Check connection pool configuration
grep -E "DB_POOL_SIZE|DB_POOL_MAX_OVERFLOW" .env

# Check for long-running queries
psql -d receipt_extractor -c "
SELECT pid, now() - query_start as duration, query, state
FROM pg_stat_activity
WHERE state != 'idle' AND query_start < now() - interval '30 seconds'
ORDER BY duration DESC;
"

# Check application logs for connection errors
grep -i "pool\|connection" logs/app.log | tail -50
```

**Resolution:**

1. **Immediate (Emergency):**
   ```bash
   # Restart application to release connections
   systemctl restart receipt-extractor
   # OR for Railway/cloud deployment
   railway restart
   ```

2. **Short-term (Within 1 hour):**
   ```bash
   # Increase connection pool size
   # Edit .env or set environment variable
   export DB_POOL_SIZE=20
   export DB_POOL_MAX_OVERFLOW=10
   
   # Restart application
   systemctl restart receipt-extractor
   ```

3. **Long-term (Within 24 hours):**
   - Review code for connection leaks
   - Add connection pool monitoring
   - Implement query timeout enforcement
   - Consider using PgBouncer for connection pooling

**Prevention:**
- Set `DB_POOL_SIZE` to `(2 * num_cores) + effective_spindle_count`
- Use context managers for database sessions
- Add connection pool metrics to monitoring dashboard
- Set up alerts when pool usage exceeds 80%

**Related Metrics:**
- Database active connections: `pg_stat_activity`
- Connection pool size: Application logs
- Request timeout rate: OpenTelemetry metrics

---

### Application Not Responding

**Symptoms:**
- Health check endpoint returns 503 or times out
- No response from any endpoint
- Load balancer marks instances as unhealthy
- CloudWatch/monitoring shows no metrics

**Root Causes:**
- Application crashed or exited
- Out of memory (OOM killer)
- Deadlock or infinite loop
- Process killed by system
- Gunicorn workers stuck

**Diagnosis:**

```bash
# Check if process is running
ps aux | grep "gunicorn\|python.*app.py"

# Check system logs for OOM kills
dmesg | grep -i "killed process"
journalctl -u receipt-extractor | tail -50

# Check application logs
tail -100 logs/app.log

# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Check for deadlocks (if app is running)
kill -SIGQUIT <gunicorn_master_pid>  # Generates stack trace
cat /tmp/gunicorn_stack_trace.txt
```

**Resolution:**

1. **Immediate:**
   ```bash
   # Restart application
   systemctl restart receipt-extractor
   
   # Or for cloud deployment
   railway restart
   
   # Or manually
   pkill -f "gunicorn.*app:app"
   cd web/backend && gunicorn -w 4 -b :5000 app:app
   ```

2. **If OOM occurred:**
   ```bash
   # Increase memory allocation (cloud deployment)
   # Railway: Update service settings to 2GB or 4GB
   
   # Reduce worker count temporarily
   export GUNICORN_WORKERS=2
   systemctl restart receipt-extractor
   ```

3. **If workers are stuck:**
   ```bash
   # Reload workers gracefully
   kill -HUP <gunicorn_master_pid>
   
   # Or restart with timeout
   export GUNICORN_TIMEOUT=30
   systemctl restart receipt-extractor
   ```

**Prevention:**
- Set memory limits for application
- Configure health checks with appropriate timeout
- Use process manager (systemd, supervisor)
- Enable auto-restart on failure
- Set up memory usage alerts

**Monitoring:**
```bash
# Add to monitoring dashboard
- Application process status
- Memory usage percentage
- CPU usage
- Worker count and status
- Health check success rate
```

---

### JWT Signature Verification Failed

**Symptoms:**
- Users unable to login despite correct credentials
- "Invalid token" or "Signature verification failed" errors
- Authentication works on one server but not others (multi-instance)
- Authentication breaks after deployment

**Root Causes:**
- JWT_SECRET mismatch between instances
- JWT_SECRET changed without invalidating old tokens
- Clock skew between servers
- Token corruption during transmission

**Diagnosis:**

```bash
# Check JWT_SECRET configuration
grep JWT_SECRET .env

# Check if JWT_SECRET is consistent across instances
ssh instance1 "grep JWT_SECRET /path/to/.env"
ssh instance2 "grep JWT_SECRET /path/to/.env"

# Check system time synchronization
timedatectl status
ntpq -p

# Test token generation and verification
python3 << 'EOF'
import os
from web.backend.auth import create_access_token, verify_token

# Generate test token
token = create_access_token({'user_id': 1})
print(f"Generated token: {token[:50]}...")

# Verify token
try:
    payload = verify_token(token)
    print(f"Verification successful: {payload}")
except Exception as e:
    print(f"Verification failed: {e}")
EOF
```

**Resolution:**

1. **Immediate (Users affected):**
   ```bash
   # Have users log out and log back in
   # Clear authentication state
   
   # If urgent, invalidate all tokens by rotating JWT_SECRET
   # WARNING: This logs out all users
   python generate-secrets.py  # Generate new JWT_SECRET
   # Update JWT_SECRET in .env
   systemctl restart receipt-extractor
   ```

2. **For configuration mismatch:**
   ```bash
   # Ensure same JWT_SECRET on all instances
   export JWT_SECRET="<consistent-secret-key-64-chars>"
   
   # Update on all instances
   for instance in instance1 instance2 instance3; do
       ssh $instance "export JWT_SECRET='<secret>' && systemctl restart receipt-extractor"
   done
   ```

3. **For clock skew:**
   ```bash
   # Enable NTP synchronization
   timedatectl set-ntp true
   
   # Force time sync
   systemctl restart systemd-timesyncd
   
   # Verify sync
   timedatectl status
   ```

**Prevention:**
- Store JWT_SECRET in centralized secret manager (AWS Secrets Manager, HashiCorp Vault)
- Use same JWT_SECRET across all instances
- Enable NTP synchronization on all servers
- Add JWT_SECRET validation check to deployment pipeline
- Document JWT_SECRET rotation procedure

**Configuration Check:**
```bash
# Add to deployment checklist
- [ ] JWT_SECRET is 64+ characters
- [ ] JWT_SECRET matches across all instances
- [ ] System time is synchronized (NTP enabled)
- [ ] JWT expiration times are appropriate (15 min access, 30 days refresh)
```

---

### Stripe Webhook Failures

**Symptoms:**
- "Webhook signature verification failed" in logs
- Subscription status not updating after payment
- Users charged but subscription not activated
- 400 errors on `/api/billing/webhook`

**Root Causes:**
- STRIPE_WEBHOOK_SECRET mismatch
- Webhook endpoint not receiving raw request body
- Webhook signature expired (>5 minutes old)
- Network issues between Stripe and application

**Diagnosis:**

```bash
# Check webhook secret configuration
grep STRIPE_WEBHOOK_SECRET .env

# Check webhook logs
grep "webhook" logs/app.log | tail -50

# Test webhook signature verification
curl -X POST http://localhost:5000/api/billing/webhook \
  -H "Content-Type: application/json" \
  -H "Stripe-Signature: test" \
  -d '{"type": "test"}'

# Check Stripe Dashboard
# Go to Developers > Webhooks
# Check webhook attempts and responses
```

**Resolution:**

1. **Immediate (Fix webhook secret):**
   ```bash
   # Get correct webhook secret from Stripe Dashboard
   # Developers > Webhooks > [Your Endpoint] > Signing secret
   
   # Update environment variable
   export STRIPE_WEBHOOK_SECRET="whsec_..."
   
   # Restart application
   systemctl restart receipt-extractor
   ```

2. **For raw body issue:**
   ```python
   # Verify webhook route uses raw request body
   # In web/backend/billing/routes.py:
   
   @app.route('/api/billing/webhook', methods=['POST'])
   def stripe_webhook():
       payload = request.data  # Use request.data, NOT request.json
       sig_header = request.headers.get('Stripe-Signature')
       # ... rest of verification
   ```

3. **Retry failed webhooks:**
   ```bash
   # In Stripe Dashboard:
   # Developers > Webhooks > [Your Endpoint]
   # Find failed events and click "Resend"
   
   # Or use Stripe CLI
   stripe events resend evt_xxxxx
   ```

**Prevention:**
- Store STRIPE_WEBHOOK_SECRET in secret manager
- Add webhook endpoint monitoring
- Set up alerts for webhook failures
- Test webhooks in staging before production
- Document webhook secret rotation procedure

**Testing Webhooks Locally:**
```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login to Stripe
stripe login

# Forward webhooks to local endpoint
stripe listen --forward-to localhost:5000/api/billing/webhook

# Trigger test webhook
stripe trigger payment_intent.succeeded
```

**Webhook Validation Checklist:**
- [ ] STRIPE_WEBHOOK_SECRET matches Stripe Dashboard
- [ ] Webhook endpoint uses request.data (raw body)
- [ ] HTTPS enabled in production (required by Stripe)
- [ ] Webhook signature verification is enabled
- [ ] Idempotency keys handled properly

---

## Performance Issues

### Slow API Response Times

**Symptoms:**
- Requests taking >1 second
- Timeout errors
- Users reporting slow page loads
- P95 latency above targets

**Diagnosis:**

```bash
# Check current response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5000/api/health

# Create curl-format.txt:
cat > curl-format.txt << 'EOF'
time_namelookup:  %{time_namelookup}s\n
time_connect:  %{time_connect}s\n
time_appconnect:  %{time_appconnect}s\n
time_pretransfer:  %{time_pretransfer}s\n
time_redirect:  %{time_redirect}s\n
time_starttransfer:  %{time_starttransfer}s\n
----------\n
time_total:  %{time_total}s\n
EOF

# Check database query times
psql -d receipt_extractor -c "
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
"

# Check application logs for slow requests
grep "took.*[0-9]\{4,\}ms" logs/app.log
```

**Quick Fixes:**
- Enable response caching for frequently accessed endpoints
- Add database indexes for common queries
- Reduce payload size (pagination)
- Use CDN for static assets

---

### High Memory Usage

**Symptoms:**
- Application using >80% of allocated memory
- OOM kills occurring
- Swap usage increasing
- Performance degradation over time

**Quick Fixes:**

```bash
# Identify memory hogs
ps aux --sort=-%mem | head -20

# Check for memory leaks
# Monitor over time
watch -n 5 'ps aux | grep python | awk "{sum+=\$6} END {print sum/1024 \" MB\"}"'

# Restart application to free memory
systemctl restart receipt-extractor

# Reduce worker count
export GUNICORN_WORKERS=2
systemctl restart receipt-extractor
```

---

## Integration Issues

### Cloud Storage Upload Failures

**Symptoms:**
- "Failed to upload to S3/GDrive/Dropbox"
- Uploads timeout
- Authentication errors

**Quick Checks:**

```bash
# Test AWS S3 credentials
aws s3 ls s3://your-bucket-name

# Test with curl
curl -X POST http://localhost:5000/api/cloud-storage/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.jpg"

# Check logs
grep -i "storage\|upload" logs/app.log | tail -50
```

**Common Solutions:**
- Verify API credentials in .env
- Check network connectivity
- Verify bucket/folder permissions
- Check storage quotas

---

### Model Loading Failures

**Symptoms:**
- "Failed to load model" errors
- Extraction requests failing
- Long model load times

**Quick Fixes:**

```bash
# Check model files exist
ls -lh ~/.cache/huggingface/
ls -lh shared/models/

# Test model loading
python3 << 'EOF'
from shared.models.manager import ModelManager
manager = ModelManager()
result = manager.load_model('ocr_tesseract')
print(f"Model load: {'success' if result else 'failed'}")
EOF

# Check disk space
df -h
```

---

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Application Health:**
   - Health check endpoint uptime: >99.9%
   - Response time P95: <500ms
   - Error rate: <1%

2. **Database:**
   - Connection pool usage: <80%
   - Query time P95: <100ms
   - Active connections: <50

3. **System Resources:**
   - CPU usage: <70%
   - Memory usage: <80%
   - Disk usage: <85%

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Error rate | >2% | >5% |
| Response time | >1s | >3s |
| Memory usage | >80% | >90% |
| Connection pool | >80% | >95% |
| Disk space | >80% | >90% |

---

## Escalation Procedures

### Severity Levels

**SEV1 (Critical):** Application down, users unable to access
- Response time: Immediate
- Escalate to: On-call engineer + DevOps lead

**SEV2 (High):** Major feature broken, some users affected
- Response time: 15 minutes
- Escalate to: On-call engineer

**SEV3 (Medium):** Minor issues, workaround available
- Response time: 2 hours
- Escalate to: Development team

**SEV4 (Low):** Cosmetic issues, enhancement requests
- Response time: Next business day
- Escalate to: Development backlog

---

## Post-Incident Review

After resolving an incident:

1. **Document what happened:** Timeline, root cause, impact
2. **Document resolution:** Steps taken, time to resolve
3. **Identify action items:** Prevent recurrence
4. **Update runbooks:** Add new scenarios
5. **Review monitoring:** Add missing metrics/alerts

---

**Last Updated**: 2026-01-25  
**Version**: 1.0  
**Maintained by**: DevOps Team
