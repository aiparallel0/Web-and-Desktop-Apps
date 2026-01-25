# Performance Testing Suite

Comprehensive performance, load, and stress testing for the Receipt Extractor application.

## Overview

This test suite validates system performance under various load conditions and identifies capacity limits.

**Testing Goals:**
- **Load Testing**: Verify system handles expected concurrent users (<500ms response time)
- **Stress Testing**: Find breaking points and capacity limits
- **Performance Benchmarking**: Measure and track performance metrics over time

## Test Structure

```
tools/tests/performance/
├── __init__.py
├── test_load.py          # Load testing (concurrent users)
├── test_stress.py        # Stress testing (breaking points)
└── README.md             # This file
```

## Prerequisites

### Required Packages

```bash
pip install pytest requests
```

### Environment Configuration

Set these environment variables before running tests:

```bash
# Required: Base URL of application to test
export TEST_BASE_URL=http://localhost:5000

# Optional: Authentication (for authenticated endpoint tests)
export TEST_USER_EMAIL=test@example.com
export TEST_USER_PASSWORD=testpass123
```

### Running the Application

Start the application before running performance tests:

```bash
# Terminal 1: Start backend
cd web/backend && python app.py

# Terminal 2: Run performance tests
pytest tools/tests/performance/ -v -s
```

## Running Tests

### Run All Performance Tests

```bash
pytest tools/tests/performance/ -v -s
```

### Run Specific Test Suites

**Load Tests Only:**
```bash
pytest tools/tests/performance/test_load.py -v -s
```

**Stress Tests Only:**
```bash
pytest tools/tests/performance/test_stress.py -v -s
```

### Run Specific Test Classes

```bash
# Basic load tests (no auth required)
pytest tools/tests/performance/test_load.py::TestLoadBasic -v -s

# Database load tests
pytest tools/tests/performance/test_load.py::TestDatabaseLoad -v -s

# Stress ramp-up tests
pytest tools/tests/performance/test_stress.py::TestStressRampUp -v -s
```

### Run with Markers

```bash
# All performance-marked tests
pytest -m performance -v -s

# All stress-marked tests
pytest -m stress -v -s

# Authenticated tests only
pytest -m authenticated -v -s
```

## Test Descriptions

### Load Tests (`test_load.py`)

**TestLoadBasic:**
- `test_health_endpoint_load`: 100 concurrent requests to /api/health
  - Target: 95%+ success rate, <1s average response time
- `test_models_endpoint_load`: 50 concurrent requests to /api/models
  - Target: 90%+ success rate, <500ms average response time

**TestLoadAuthenticated:**
- `test_receipts_list_load`: 100 concurrent authenticated requests
  - Target: 95%+ success rate, <500ms average response time
  - Requires: TEST_USER_EMAIL and TEST_USER_PASSWORD

**TestDatabaseLoad:**
- `test_concurrent_database_queries`: 50 concurrent database queries
  - Target: 0 connection pool errors, 95%+ success rate
  - Validates: Database connection pool configuration

### Stress Tests (`test_stress.py`)

**TestStressRampUp:**
- `test_health_endpoint_stress`: Ramps from 10 to 500 concurrent users
  - Finds: Breaking point where failure rate exceeds 10%
  - Target: System handles 50+ concurrent users
  
- `test_models_endpoint_stress`: Ramps from 5 to 100 concurrent users
  - Tests: Model loading and API under increasing load
  
- `test_sustained_load_stress`: Maintains 50 concurrent users for 60 seconds
  - Target: 95%+ success rate, <1s average response time
  - Validates: System stability under sustained load

**TestResourceStress:**
- `test_memory_stress_recovery`: Burst of 200 requests, then recovery test
  - Validates: System recovers after heavy load
  - Target: 95%+ success rate after recovery period

## Performance Targets

### Response Times (Production Targets)

| Endpoint | Target | Acceptable | Unacceptable |
|----------|--------|------------|--------------|
| /api/health | <100ms | <500ms | >1s |
| /api/models | <200ms | <500ms | >1s |
| /api/receipts (list) | <300ms | <500ms | >1s |
| /api/extract | <3s | <10s | >30s |

### Concurrent Users

| Load Level | Expected Behavior |
|------------|-------------------|
| 1-50 users | Normal operation, <500ms response |
| 50-100 users | Slight degradation acceptable, <1s response |
| 100-200 users | Degraded but functional, <2s response |
| 200+ users | May fail, breaking point investigation |

### Success Rates

- **Normal operation**: 99%+ success rate
- **Under load**: 95%+ success rate
- **Breaking point**: <90% success rate

## Interpreting Results

### Example Output

```
--- Health Endpoint Load Test Results ---
Total Requests: 100
Success Rate: 99.00%
Avg Response Time: 0.245s
Median Response Time: 0.221s
P95 Response Time: 0.412s
P99 Response Time: 0.587s
```

### Key Metrics

- **Success Rate**: Percentage of requests that completed successfully (HTTP <400)
- **Avg Response Time**: Mean response time across all successful requests
- **Median Response Time**: 50th percentile (typical user experience)
- **P95 Response Time**: 95th percentile (slowest 5% of requests)
- **P99 Response Time**: 99th percentile (worst-case latency)

### Red Flags

🚨 **Investigate immediately if:**
- Success rate drops below 95%
- Average response time exceeds 1s for simple endpoints
- P95 response time exceeds 2s
- Connection pool errors occur
- Breaking point is below 50 concurrent users

## Troubleshooting

### Common Issues

**1. Connection Refused**
```
Error: Connection refused
```
**Solution**: Start the application first (`python web/backend/app.py`)

**2. Timeout Errors**
```
Error: Read timed out
```
**Solution**: 
- Application may be overloaded
- Increase timeout in test configuration
- Check system resources (CPU, memory)

**3. Connection Pool Exhausted**
```
Error: QueuePool limit exceeded
```
**Solution**: 
- Increase DB_POOL_SIZE in .env
- Increase DB_POOL_MAX_OVERFLOW in .env
- Check for connection leaks in application code

**4. Tests Skip (requests not installed)**
```
SKIPPED [1] test_load.py: requests library not installed
```
**Solution**: `pip install requests`

### Performance Degradation

If tests show degraded performance:

1. **Check system resources:**
   ```bash
   # CPU and memory usage
   top
   
   # Database connections
   psql -c "SELECT count(*) FROM pg_stat_activity;"
   ```

2. **Review application logs:**
   ```bash
   tail -f logs/app.log
   ```

3. **Profile slow endpoints:**
   - Enable Flask profiling
   - Add timing logs
   - Use application monitoring tools

4. **Database optimization:**
   - Run EXPLAIN ANALYZE on slow queries
   - Add missing indexes
   - Optimize query patterns

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Performance Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  performance:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest requests
    
    - name: Start application
      run: |
        cd web/backend
        python app.py &
        sleep 10  # Wait for startup
    
    - name: Run performance tests
      run: |
        pytest tools/tests/performance/ -v --tb=short
      env:
        TEST_BASE_URL: http://localhost:5000
```

## Performance Monitoring

### Continuous Monitoring

For production monitoring, integrate with:

- **OpenTelemetry**: Already configured in `web/backend/telemetry/`
- **Grafana**: Create dashboards for metrics visualization
- **Prometheus**: Collect and store metrics over time
- **DataDog/New Relic**: APM for detailed performance analysis

### Key Metrics to Track

1. **Response Times**: P50, P95, P99 for all endpoints
2. **Error Rates**: 4xx and 5xx response rates
3. **Throughput**: Requests per second
4. **Database**: Query time, connection pool usage
5. **System Resources**: CPU, memory, disk I/O

## Best Practices

### Before Running Tests

- ✅ Start application in production mode (not debug mode)
- ✅ Use production-like database (PostgreSQL, not SQLite)
- ✅ Clear logs and temporary files
- ✅ Close unnecessary applications (free up resources)
- ✅ Run on consistent hardware (avoid laptop during battery mode)

### Test Design

- ✅ Start with load tests, then stress tests
- ✅ Allow system recovery time between test runs
- ✅ Use realistic data and scenarios
- ✅ Run multiple iterations for statistical significance
- ✅ Document baseline performance for comparison

### Interpreting Results

- ✅ Compare against baseline performance
- ✅ Look for trends over time, not single data points
- ✅ Consider system resources and external factors
- ✅ Investigate outliers and anomalies
- ✅ Document findings and action items

## Next Steps

After running performance tests:

1. **Document Baseline**: Record initial performance metrics
2. **Set Alerts**: Configure monitoring alerts for production
3. **Optimize**: Address any identified bottlenecks
4. **Capacity Planning**: Use results for infrastructure sizing
5. **Regular Testing**: Run tests before each major release

## Resources

- [Flask Performance Best Practices](https://flask.palletsprojects.com/en/latest/deploying/)
- [Gunicorn Optimization](https://docs.gunicorn.org/en/stable/design.html)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Load Testing Best Practices](https://locust.io/)

---

**Last Updated**: 2026-01-25  
**Test Coverage**: Load, Stress, Database Connection Pool  
**Status**: Production Ready
