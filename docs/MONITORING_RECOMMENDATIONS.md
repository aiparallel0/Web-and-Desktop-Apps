# Monitoring and Alerting Recommendations

## Overview
Based on log analysis, this document provides recommendations for monitoring and alerting to prevent future issues.

## Current Issues Identified

### 1. Celery Configuration Errors (HIGH PRIORITY) ✅ FIXED
- **Issue**: TypeError in beat_schedule configuration
- **Impact**: Celery Beat scheduler fails to start
- **Fix Applied**: Changed `beat_schedule` to `beat_schedule_filename` in celery_worker.py
- **Prevention**: Added configuration validator (config_validator.py)

### 2. Permission Errors (MEDIUM PRIORITY)
- **Issue**: Corrupted schedule file with permission denied errors
- **Recommendation**: Ensure proper directory permissions for `/app/celerybeat/`
  ```bash
  mkdir -p /app/celerybeat
  chmod 755 /app/celerybeat
  chown app:app /app/celerybeat
  ```

### 3. Module Import Errors (MEDIUM PRIORITY)
- **Issue**: 22 ModuleNotFoundError occurrences
- **Recommendation**: Add dependency verification to deployment pipeline
  ```python
  # Add to pre-deployment checks
  from web.backend.training.config_validator import check_celery_connectivity
  check_celery_connectivity()
  ```

### 4. Log File Management (MEDIUM PRIORITY) ✅ IMPLEMENTED
- **Issue**: Large log files (378KB+) accumulating in root directory
- **Fix Applied**: Created log_manager.py script for rotation and cleanup
- **Recommendation**: Set up automated log rotation via cron
  ```bash
  # Add to crontab
  0 3 * * * /usr/bin/python3 /path/to/scripts/log_manager.py --rotate --compress --clean
  ```

## Monitoring Strategy

### 1. Application Health Monitoring

#### Metrics to Monitor
- **Celery Worker Health**
  - Active workers count
  - Task queue depth
  - Task failure rate
  - Average task duration
  
- **Database Health**
  - Connection pool usage
  - Query performance
  - Deadlock occurrences
  
- **Memory Usage**
  - Worker memory consumption
  - Memory leak detection
  - OOM events

#### Tools Recommendation
- **Prometheus + Grafana**: For metrics collection and visualization
- **Celery Flower**: For Celery-specific monitoring
- **Sentry**: For error tracking and aggregation

### 2. Error Rate Alerting

#### Critical Alerts (Immediate Action)
```yaml
alerts:
  - name: CeleryWorkerDown
    condition: celery_worker_count == 0
    severity: critical
    notification: PagerDuty, Slack
    
  - name: HighErrorRate
    condition: error_rate > 10% over 5min
    severity: critical
    notification: PagerDuty, Slack
    
  - name: DatabaseConnectionFailure
    condition: db_connection_errors > 5 in 1min
    severity: critical
    notification: PagerDuty
```

#### Warning Alerts (Monitor Closely)
```yaml
alerts:
  - name: HighTaskQueueDepth
    condition: celery_queue_depth > 100
    severity: warning
    notification: Slack
    
  - name: SlowTaskExecution
    condition: avg_task_duration > 300s
    severity: warning
    notification: Slack
    
  - name: HighMemoryUsage
    condition: memory_usage > 80%
    severity: warning
    notification: Slack
```

### 3. Log Analysis & Aggregation

#### Setup Centralized Logging
```python
# Example: Ship logs to ELK Stack or CloudWatch
import logging
from pythonjsonlogger import jsonlogger

handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

#### Log Retention Policy
- **Production Logs**: 90 days
- **Error Logs**: 180 days
- **Audit Logs**: 1 year
- **Debug Logs**: 7 days

### 4. Configuration Validation

#### Pre-Deployment Checks
```python
# Add to deployment pipeline
from web.backend.training.config_validator import run_full_validation

if not run_full_validation():
    print("Configuration validation failed")
    sys.exit(1)
```

#### Runtime Validation
```python
# Add to application startup
from web.backend.training.config_validator import validate_celery_config

errors = validate_celery_config()
if errors:
    logger.error(f"Configuration errors: {errors}")
    # Either fail fast or run in degraded mode
```

## Implementation Checklist

### Immediate Actions (Week 1)
- [x] Fix Celery beat_schedule configuration bug
- [x] Add configuration validator
- [x] Create log management script
- [ ] Set up log rotation cron job
- [ ] Verify beat schedule directory permissions
- [ ] Add configuration validation to startup

### Short-term Actions (Week 2-4)
- [ ] Implement Celery Flower for monitoring
- [ ] Set up basic alerting (email/Slack)
- [ ] Add health check endpoints
- [ ] Create deployment checklist with validation
- [ ] Document configuration requirements

### Long-term Actions (Month 2-3)
- [ ] Deploy full monitoring stack (Prometheus/Grafana)
- [ ] Implement distributed tracing (OpenTelemetry)
- [ ] Set up error tracking (Sentry)
- [ ] Create monitoring dashboard
- [ ] Implement automated remediation for common issues

## Testing & Validation

### Configuration Testing
```bash
# Test Celery configuration
python web/backend/training/config_validator.py

# Expected output:
# ✅ Configuration validation passed
# ✅ Celery broker connectivity OK
```

### Log Management Testing
```bash
# Test log rotation
python scripts/log_manager.py --rotate --analyze

# Test log compression
python scripts/log_manager.py --compress --analyze

# Test log cleanup (dry run first!)
python scripts/log_manager.py --clean --retention-days 90
```

### Monitoring Testing
```bash
# Test health endpoints
curl http://localhost:5000/health

# Test Celery worker status
celery -A web.backend.training.celery_worker inspect active

# Test task submission
celery -A web.backend.training.celery_worker call training.check_job_status
```

## Cost Considerations

### Monitoring Infrastructure
- **CloudWatch Logs**: ~$0.50/GB ingested + $0.03/GB stored
- **Prometheus + Grafana**: Self-hosted or managed (DigitalOcean ~$15/month)
- **Sentry**: Free tier (5K events/month), Pro ($26/month for 50K events)
- **PagerDuty**: Essential plan ($21/user/month)

### Estimated Monthly Costs
- **Basic Setup** (CloudWatch + Email): ~$10-20/month
- **Standard Setup** (Prometheus + Sentry + Slack): ~$50-75/month
- **Enterprise Setup** (Full stack + PagerDuty): ~$150-200/month

## Documentation Updates

### Files to Update
1. `README.md`: Add monitoring section
2. `DEPLOYMENT.md`: Add configuration validation steps
3. `.env.example`: Document all required environment variables
4. `docker-compose.yml`: Add monitoring services

### Example .env Documentation
```bash
# Celery Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Celery Beat (only enable on one instance)
CELERY_BEAT_ENABLED=false  # Set to true only on scheduler instance
CELERY_BEAT_SCHEDULE=/app/celerybeat/schedule.db

# Training Configuration
TRAINING_POLL_INTERVAL=30  # Seconds between job status polls
TRAINING_MAX_POLL_COUNT=720  # Maximum polls (~6 hours)
TRAINING_ERROR_POLL_INTERVAL=60  # Wait time after errors

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

## Rollback Plan

If issues arise after implementing these changes:

1. **Configuration Issues**:
   ```bash
   # Revert celery_worker.py changes
   git revert <commit-hash>
   
   # Restart workers
   supervisorctl restart celery-worker
   ```

2. **Log Management Issues**:
   ```bash
   # Disable log rotation cron job
   crontab -e  # Comment out log_manager.py line
   
   # Restore logs from backup if needed
   ```

3. **Monitoring Issues**:
   ```bash
   # Disable monitoring temporarily
   export ENABLE_METRICS=false
   
   # Restart application
   ```

## Success Metrics

Track these metrics to measure improvement:

1. **Error Rate**: Reduce from current baseline by 50% in 30 days
2. **Mean Time to Detection (MTTD)**: < 5 minutes for critical errors
3. **Mean Time to Resolution (MTTR)**: < 30 minutes for configuration issues
4. **Log Storage**: Stay under 1GB for 30 days of logs
5. **Configuration Failures**: 0 deployment failures due to configuration

## Next Steps

1. Review this document with the team
2. Prioritize implementation based on business impact
3. Assign owners for each action item
4. Set up bi-weekly reviews to track progress
5. Update runbooks with new procedures

## Support & Resources

- **Celery Documentation**: https://docs.celeryproject.org/
- **Prometheus Documentation**: https://prometheus.io/docs/
- **Configuration Validator**: `web/backend/training/config_validator.py`
- **Log Manager**: `scripts/log_manager.py`
- **Log Analysis**: `analyze_logs.py`

---

*Document Version: 1.0*  
*Last Updated: 2026-02-05*  
*Author: Log Analysis System*
