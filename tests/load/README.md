# TBCV Load Testing Suite

This directory contains comprehensive load testing scenarios for the Truth-Based Content Validation (TBCV) system using [Locust](https://locust.io/).

## Overview

The load testing suite provides:
- **Validation throughput testing** - Single file and batch validation performance
- **Recommendation generation testing** - Performance under recommendation workloads
- **Workflow management testing** - Concurrent workflow processing capabilities
- **Cache performance testing** - Cache behavior under load
- **Database performance testing** - Database scalability assessment
- **System health monitoring** - Health endpoint performance

## Quick Start

### Prerequisites

1. Install Locust (if not already installed):
```bash
pip install locust
```

2. Start the TBCV server:
```bash
# Start the API server
python -m uvicorn api.server:app --host 0.0.0.0 --port 8080
```

### Running Load Tests

#### Option 1: Web UI (Recommended for Interactive Testing)

```bash
locust -f tests/load/locustfile.py --host=http://localhost:8080
```

Then open your browser to http://localhost:8089 and configure:
- Number of users (peak concurrency)
- Spawn rate (users added per second)
- Host URL (already set)

#### Option 2: Headless Mode (Automated Testing)

```bash
# Run with 50 concurrent users, spawning 5 per second, for 5 minutes
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       --users 50 \
       --spawn-rate 5 \
       --run-time 5m \
       --headless
```

#### Option 3: Specific User Classes

Run only validation workload:
```bash
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       ValidationUser \
       --users 20 \
       --spawn-rate 2
```

Run multiple user classes:
```bash
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       ValidationUser RecommendationUser \
       --users 30 \
       --spawn-rate 3
```

#### Option 4: Generate Reports

```bash
# Run test and save HTML report
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       --users 50 \
       --spawn-rate 5 \
       --run-time 10m \
       --headless \
       --html=reports/load_test_$(date +%Y%m%d_%H%M%S).html

# Run test and save CSV results
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       --users 50 \
       --spawn-rate 5 \
       --run-time 10m \
       --headless \
       --csv=reports/load_test_$(date +%Y%m%d_%H%M%S)
```

## User Classes

The load testing suite includes multiple user classes representing different usage patterns:

### 1. ValidationUser (Weight: 5)
**Purpose:** Simulates content creators validating their work.

**Behaviors:**
- Small file validation (most common)
- Medium file validation
- Large file validation (stress test)
- Batch validation (5-10 files)
- List validations

**Wait time:** 1-3 seconds between requests

### 2. RecommendationUser (Weight: 3)
**Purpose:** Simulates users reviewing and managing recommendations.

**Behaviors:**
- List all recommendations
- Generate recommendations for validation
- Get recommendations for specific validation

**Wait time:** 2-4 seconds between requests

### 3. WorkflowUser (Weight: 2)
**Purpose:** Simulates administrators monitoring batch operations.

**Behaviors:**
- List all workflows
- Get workflow status
- Monitor workflow progress

**Wait time:** 3-5 seconds between requests

### 4. SystemMonitorUser (Weight: 1)
**Purpose:** Simulates monitoring systems checking system health.

**Behaviors:**
- Health checks
- Liveness probes
- Readiness probes
- List agents
- Cache statistics

**Wait time:** 5-10 seconds between requests

### 5. MixedWorkloadUser (Weight: 10)
**Purpose:** Simulates typical user behavior with varied tasks.

**Behaviors:**
- Combination of validation, recommendations, workflows, and health checks
- Most realistic workload pattern

**Wait time:** 1-5 seconds between requests

## Load Test Scenarios

### Scenario 1: Light Load (Baseline)
**Purpose:** Establish baseline performance metrics.

```bash
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       --users 10 \
       --spawn-rate 2 \
       --run-time 5m \
       --headless
```

**Expected Results:**
- < 100ms average response time
- < 200ms @ 95th percentile
- < 1% failure rate
- \> 50 requests/second

### Scenario 2: Normal Load
**Purpose:** Simulate typical production usage.

```bash
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       --users 50 \
       --spawn-rate 5 \
       --run-time 10m \
       --headless
```

**Expected Results:**
- < 200ms average response time
- < 500ms @ 95th percentile
- < 2% failure rate
- \> 100 requests/second

### Scenario 3: High Load (Stress Test)
**Purpose:** Identify system limits and bottlenecks.

```bash
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       --users 100 \
       --spawn-rate 10 \
       --run-time 15m \
       --headless
```

**Expected Results:**
- < 500ms average response time
- < 1000ms @ 95th percentile
- < 5% failure rate
- \> 150 requests/second

### Scenario 4: Spike Test
**Purpose:** Test system behavior under sudden traffic spikes.

```bash
# Start with low load
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       --users 10 \
       --spawn-rate 10 \
       --run-time 2m \
       --headless

# Then spike to high load
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       --users 200 \
       --spawn-rate 50 \
       --run-time 5m \
       --headless
```

### Scenario 5: Endurance Test
**Purpose:** Test system stability over extended periods.

```bash
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       --users 50 \
       --spawn-rate 5 \
       --run-time 60m \
       --headless
```

**Monitor for:**
- Memory leaks
- Resource exhaustion
- Degraded performance over time
- Connection pool issues

### Scenario 6: Validation-Heavy Load
**Purpose:** Test validation throughput specifically.

```bash
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       ValidationUser \
       --users 50 \
       --spawn-rate 10 \
       --run-time 10m \
       --headless
```

### Scenario 7: Recommendation-Heavy Load
**Purpose:** Test recommendation generation under load.

```bash
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       RecommendationUser \
       --users 30 \
       --spawn-rate 5 \
       --run-time 10m \
       --headless
```

## Performance Targets

### Response Time Targets
| Operation | Target (p50) | Target (p95) | Target (p99) |
|-----------|-------------|-------------|-------------|
| Health Check | < 10ms | < 20ms | < 50ms |
| Small File Validation | < 100ms | < 200ms | < 500ms |
| Medium File Validation | < 300ms | < 500ms | < 1000ms |
| Large File Validation | < 800ms | < 1500ms | < 3000ms |
| Batch Validation (10 files) | < 1000ms | < 2000ms | < 4000ms |
| Recommendation Generation | < 500ms | < 1000ms | < 2000ms |
| List Operations | < 50ms | < 100ms | < 200ms |

### Throughput Targets
| Scenario | Target RPS | Concurrent Users |
|----------|-----------|-----------------|
| Light Load | > 50 | 10 |
| Normal Load | > 100 | 50 |
| High Load | > 150 | 100 |
| Peak Load | > 200 | 200 |

### Reliability Targets
- Failure Rate: < 1% under normal load
- Failure Rate: < 5% under high load
- Availability: > 99.9% uptime
- Error Recovery: < 100ms for cached responses

## Monitoring During Tests

### System Metrics to Monitor

1. **Server Metrics:**
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network I/O

2. **Application Metrics:**
   - Request latency
   - Error rate
   - Active connections
   - Queue depth

3. **Database Metrics:**
   - Query performance
   - Connection pool usage
   - Lock contention
   - Transaction throughput

4. **Cache Metrics:**
   - Hit rate
   - Miss rate
   - Eviction rate
   - Memory usage

### Using System Monitoring Tools

#### Linux/Mac:
```bash
# CPU and memory
htop

# Network
iftop

# Disk I/O
iotop

# All-in-one monitoring
docker stats  # If running in container
```

#### Windows:
```powershell
# Task Manager (GUI)
taskmgr

# PowerShell monitoring
Get-Process uvicorn | Format-Table CPU, WS -AutoSize
```

## Analyzing Results

### Key Metrics to Examine

1. **Response Time Distribution:**
   - Average response time
   - 50th percentile (median)
   - 95th percentile
   - 99th percentile
   - Maximum response time

2. **Request Statistics:**
   - Total requests
   - Requests per second (RPS)
   - Failed requests
   - Failure rate (%)

3. **User Behavior:**
   - Active users over time
   - Request rate over time
   - User spawn/stop events

### Identifying Bottlenecks

#### High Response Times
**Symptoms:**
- p95 > 1000ms
- p99 > 5000ms

**Possible Causes:**
- Slow database queries
- Inefficient algorithms
- Blocking I/O operations
- Resource contention

**Investigation:**
- Check database query logs
- Profile application code
- Review cache hit rates
- Monitor system resources

#### High Failure Rates
**Symptoms:**
- Failure rate > 5%
- Connection timeouts
- 500 errors

**Possible Causes:**
- Connection pool exhaustion
- Database connection limits
- Memory issues
- Unhandled exceptions

**Investigation:**
- Check error logs
- Review connection pool settings
- Monitor memory usage
- Analyze error patterns

#### Low Throughput
**Symptoms:**
- RPS < expected
- CPU not maxed out
- Low user count tolerance

**Possible Causes:**
- Thread/process limits
- I/O bottlenecks
- Lock contention
- Configuration limits

**Investigation:**
- Check worker configuration
- Review async operations
- Monitor lock wait times
- Tune thread pools

## Troubleshooting

### Common Issues

#### Issue: Locust won't start
**Solution:**
```bash
# Check if Locust is installed
pip show locust

# Reinstall if necessary
pip install --upgrade locust
```

#### Issue: Connection refused
**Solution:**
```bash
# Verify server is running
curl http://localhost:8080/health

# Check if port is correct
netstat -an | grep 8080  # Linux/Mac
netstat -an | findstr 8080  # Windows
```

#### Issue: High failure rate immediately
**Solution:**
- Reduce spawn rate
- Increase server resources
- Check server logs for errors
- Verify test data is valid

#### Issue: Memory errors during test
**Solution:**
- Reduce concurrent users
- Increase server memory
- Check for memory leaks
- Enable garbage collection logging

## Best Practices

1. **Start Small:** Begin with light load and gradually increase
2. **Monitor Continuously:** Watch system metrics during tests
3. **Document Results:** Save reports and metrics for comparison
4. **Test Regularly:** Run load tests on schedule (e.g., weekly)
5. **Use Realistic Data:** Generate test data similar to production
6. **Isolate Tests:** Run load tests in isolated environment
7. **Version Control:** Track load test configurations and results
8. **Set Baselines:** Establish performance baselines for comparison
9. **Test Different Scenarios:** Cover various usage patterns
10. **Automate:** Integrate load tests into CI/CD pipeline

## Advanced Usage

### Distributed Load Testing

For higher load, run Locust in distributed mode:

1. **Start master:**
```bash
locust -f tests/load/locustfile.py \
       --master \
       --expect-workers 3
```

2. **Start workers (on same or different machines):**
```bash
locust -f tests/load/locustfile.py \
       --worker \
       --master-host=localhost
```

### Custom Metrics

Add custom metrics in locustfile.py:
```python
from locust import events

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    # Custom metric logic
    pass
```

### Integration with CI/CD

Example GitHub Actions workflow:
```yaml
name: Load Test
on: [push]
jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start server
        run: python -m uvicorn api.server:app --host 0.0.0.0 --port 8080 &
      - name: Run load test
        run: |
          locust -f tests/load/locustfile.py \
                 --host=http://localhost:8080 \
                 --users 50 \
                 --spawn-rate 5 \
                 --run-time 5m \
                 --headless \
                 --html=load_test_report.html
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: load-test-results
          path: load_test_report.html
```

## References

- [Locust Documentation](https://docs.locust.io/)
- [Performance Testing Best Practices](https://martinfowler.com/articles/performance-testing.html)
- [FastAPI Performance Tips](https://fastapi.tiangolo.com/deployment/concepts/)
- [TBCV Performance Baselines](../../docs/performance_baselines.md)

## Support

For issues or questions about load testing:
1. Check server logs: `logs/tbcv.log`
2. Review test output for errors
3. Consult performance baseline documentation
4. Open an issue with test results and configuration
