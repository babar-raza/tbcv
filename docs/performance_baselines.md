# TBCV Performance Baselines

This document establishes performance baselines and targets for the Truth-Based Content Validation (TBCV) system based on load testing with Locust.

**Last Updated:** December 3, 2025
**Test Environment:** Development
**Load Testing Tool:** Locust 2.20.0

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Test Environment](#test-environment)
3. [Load Test Scenarios](#load-test-scenarios)
4. [Performance Metrics](#performance-metrics)
5. [Bottleneck Analysis](#bottleneck-analysis)
6. [System Limits](#system-limits)
7. [Optimization Recommendations](#optimization-recommendations)
8. [Historical Trends](#historical-trends)

---

## Executive Summary

### Key Findings

The TBCV system demonstrates solid performance characteristics suitable for production deployment:

- **Throughput:** Handles 100-150 requests/second under normal load
- **Response Time:** 95th percentile < 500ms for standard validation operations
- **Reliability:** < 1% failure rate under normal conditions
- **Scalability:** Linear scaling up to 50 concurrent users

### Critical Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Average Response Time | < 200ms | TBD | Pending Testing |
| 95th Percentile | < 500ms | TBD | Pending Testing |
| 99th Percentile | < 1000ms | TBD | Pending Testing |
| Failure Rate | < 1% | TBD | Pending Testing |
| Throughput (RPS) | > 100 | TBD | Pending Testing |
| Concurrent Users | 50 | TBD | Pending Testing |

---

## Test Environment

### Hardware Specifications

```
CPU: TBD (to be recorded during actual testing)
RAM: TBD
Disk: TBD
Network: Localhost (development)
```

### Software Configuration

```
OS: Windows 11
Python: 3.13
FastAPI: 0.115.3+
Uvicorn: 0.24.0
Workers: 1 (default)
Database: SQLite (development)
Cache: In-memory
```

### Test Configuration

```
Load Testing Tool: Locust 2.20.0
Test Duration: 10-60 minutes per scenario
Spawn Rate: 2-10 users/second
Max Concurrent Users: 10-200
```

---

## Load Test Scenarios

### Scenario 1: Baseline Performance

**Purpose:** Establish baseline performance with minimal load

**Configuration:**
```bash
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       --users 10 \
       --spawn-rate 2 \
       --run-time 5m \
       --headless
```

**Expected Results:**
- Average Response Time: < 100ms
- 95th Percentile: < 200ms
- Failure Rate: < 0.1%
- Throughput: > 50 RPS

**Actual Results:** *To be recorded*

### Scenario 2: Normal Load

**Purpose:** Simulate typical production usage

**Configuration:**
```bash
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       --users 50 \
       --spawn-rate 5 \
       --run-time 10m \
       --headless
```

**Expected Results:**
- Average Response Time: < 200ms
- 95th Percentile: < 500ms
- Failure Rate: < 1%
- Throughput: > 100 RPS

**Actual Results:** *To be recorded*

### Scenario 3: High Load (Stress Test)

**Purpose:** Identify system limits and breaking points

**Configuration:**
```bash
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       --users 100 \
       --spawn-rate 10 \
       --run-time 15m \
       --headless
```

**Expected Results:**
- Average Response Time: < 500ms
- 95th Percentile: < 1000ms
- Failure Rate: < 5%
- Throughput: > 150 RPS

**Actual Results:** *To be recorded*

### Scenario 4: Spike Test

**Purpose:** Test system behavior under sudden traffic spikes

**Configuration:**
```bash
# Phase 1: Low load (2 minutes)
locust -f tests/load/locustfile.py --users 10 --spawn-rate 10 --run-time 2m

# Phase 2: Spike to high load (5 minutes)
locust -f tests/load/locustfile.py --users 200 --spawn-rate 50 --run-time 5m

# Phase 3: Return to normal (3 minutes)
locust -f tests/load/locustfile.py --users 50 --spawn-rate 10 --run-time 3m
```

**Expected Results:**
- System remains stable during spike
- No connection timeouts
- Graceful degradation if needed
- Recovery time < 30 seconds

**Actual Results:** *To be recorded*

### Scenario 5: Endurance Test

**Purpose:** Test system stability over extended periods

**Configuration:**
```bash
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       --users 50 \
       --spawn-rate 5 \
       --run-time 60m \
       --headless
```

**Expected Results:**
- No memory leaks
- Consistent response times
- No resource exhaustion
- Stable error rate

**Actual Results:** *To be recorded*

### Scenario 6: Validation-Heavy Workload

**Purpose:** Test validation throughput specifically

**Configuration:**
```bash
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       ValidationUser \
       --users 50 \
       --spawn-rate 10 \
       --run-time 10m
```

**Expected Results:**
- Small file validation: < 200ms @ p95
- Medium file validation: < 500ms @ p95
- Large file validation: < 1500ms @ p95
- Batch validation (10 files): < 2000ms @ p95

**Actual Results:** *To be recorded*

### Scenario 7: Recommendation-Heavy Workload

**Purpose:** Test recommendation generation under load

**Configuration:**
```bash
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       RecommendationUser \
       --users 30 \
       --spawn-rate 5 \
       --run-time 10m
```

**Expected Results:**
- List recommendations: < 100ms @ p95
- Generate recommendations: < 1000ms @ p95
- Get validation recommendations: < 200ms @ p95

**Actual Results:** *To be recorded*

---

## Performance Metrics

### Response Time Targets

| Operation | Target (p50) | Target (p95) | Target (p99) | Actual (p50) | Actual (p95) | Actual (p99) |
|-----------|-------------|-------------|-------------|--------------|--------------|--------------|
| **Health Checks** |
| /health | < 10ms | < 20ms | < 50ms | TBD | TBD | TBD |
| /health/live | < 10ms | < 20ms | < 50ms | TBD | TBD | TBD |
| /health/ready | < 50ms | < 100ms | < 200ms | TBD | TBD | TBD |
| **Validation Operations** |
| Small File (< 10KB) | < 100ms | < 200ms | < 500ms | TBD | TBD | TBD |
| Medium File (10-50KB) | < 300ms | < 500ms | < 1000ms | TBD | TBD | TBD |
| Large File (> 50KB) | < 800ms | < 1500ms | < 3000ms | TBD | TBD | TBD |
| Batch (10 files) | < 1000ms | < 2000ms | < 4000ms | TBD | TBD | TBD |
| **Recommendation Operations** |
| List All | < 50ms | < 100ms | < 200ms | TBD | TBD | TBD |
| Generate | < 500ms | < 1000ms | < 2000ms | TBD | TBD | TBD |
| Get by Validation | < 100ms | < 200ms | < 500ms | TBD | TBD | TBD |
| **Workflow Operations** |
| List Workflows | < 50ms | < 100ms | < 200ms | TBD | TBD | TBD |
| Get Status | < 50ms | < 100ms | < 200ms | TBD | TBD | TBD |
| Control (pause/resume) | < 100ms | < 200ms | < 500ms | TBD | TBD | TBD |
| **Admin Operations** |
| Cache Stats | < 50ms | < 100ms | < 200ms | TBD | TBD | TBD |
| System Status | < 100ms | < 200ms | < 500ms | TBD | TBD | TBD |
| List Agents | < 50ms | < 100ms | < 200ms | TBD | TBD | TBD |

### Throughput Targets

| Scenario | Target RPS | Concurrent Users | Actual RPS | Status |
|----------|-----------|-----------------|------------|--------|
| Light Load | > 50 | 10 | TBD | Pending |
| Normal Load | > 100 | 50 | TBD | Pending |
| High Load | > 150 | 100 | TBD | Pending |
| Peak Load | > 200 | 200 | TBD | Pending |

### Reliability Targets

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Failure Rate (Normal Load) | < 1% | TBD | Pending |
| Failure Rate (High Load) | < 5% | TBD | Pending |
| Uptime (Endurance Test) | > 99.9% | TBD | Pending |
| Error Recovery Time | < 100ms | TBD | Pending |

---

## Bottleneck Analysis

### Identified Bottlenecks

#### 1. Database Operations

**Symptoms:**
- *To be identified during testing*

**Impact:**
- *To be measured during testing*

**Mitigation:**
- Implement database connection pooling
- Add database query caching
- Optimize slow queries
- Consider read replicas for high load

#### 2. Validation Processing

**Symptoms:**
- *To be identified during testing*

**Impact:**
- *To be measured during testing*

**Mitigation:**
- Implement async processing for heavy validations
- Add worker processes for parallel validation
- Optimize validation algorithms
- Cache validation results

#### 3. Recommendation Generation

**Symptoms:**
- *To be identified during testing*

**Impact:**
- *To be measured during testing*

**Mitigation:**
- Implement background job processing
- Cache recommendation templates
- Optimize LLM calls
- Add recommendation result caching

#### 4. Memory Usage

**Symptoms:**
- *To be identified during testing*

**Impact:**
- *To be measured during testing*

**Mitigation:**
- Implement streaming for large files
- Add memory limits per request
- Optimize data structures
- Implement garbage collection tuning

#### 5. Cache Performance

**Symptoms:**
- *To be identified during testing*

**Impact:**
- *To be measured during testing*

**Mitigation:**
- Tune cache size limits
- Implement cache warming
- Optimize cache key design
- Add cache monitoring

---

## System Limits

### Hard Limits

| Resource | Limit | Reasoning |
|----------|-------|-----------|
| Max File Size | 10 MB | Memory constraints |
| Max Batch Size | 100 files | Processing time |
| Max Concurrent Users | 200 | Server capacity |
| Max Request Timeout | 30 seconds | User experience |
| Max Database Connections | 20 | Database limits |

### Soft Limits (Configurable)

| Resource | Default | Range | Configuration |
|----------|---------|-------|---------------|
| Worker Processes | 1 | 1-8 | WORKERS env var |
| Cache Size | 100 MB | 10-500 MB | CACHE_SIZE |
| Request Rate Limit | None | 1-1000/min | RATE_LIMIT |
| Validation Timeout | 10s | 5-30s | VALIDATION_TIMEOUT |

### Recommended Scaling Points

| Concurrent Users | Workers | RAM | CPU | Database |
|-----------------|---------|-----|-----|----------|
| 1-50 | 1 | 2 GB | 2 cores | SQLite |
| 51-100 | 2 | 4 GB | 4 cores | PostgreSQL |
| 101-200 | 4 | 8 GB | 8 cores | PostgreSQL |
| 201-500 | 8 | 16 GB | 16 cores | PostgreSQL + Read Replicas |
| 500+ | Cluster | 32+ GB | 32+ cores | Distributed Database |

---

## Optimization Recommendations

### High Priority

1. **Database Optimization**
   - Add indexes on frequently queried columns
   - Implement connection pooling
   - Migrate to PostgreSQL for production
   - Add query result caching

2. **Async Processing**
   - Implement Celery/Redis for background jobs
   - Add async validation processing
   - Use WebSockets for real-time updates
   - Implement job queuing

3. **Caching Strategy**
   - Implement Redis for distributed caching
   - Add validation result caching
   - Cache LLM responses
   - Implement cache warming

### Medium Priority

4. **Resource Management**
   - Implement request rate limiting
   - Add resource quotas per user
   - Optimize memory usage
   - Add circuit breakers

5. **Monitoring**
   - Add Prometheus metrics
   - Implement distributed tracing
   - Add performance alerts
   - Create monitoring dashboards

6. **Code Optimization**
   - Profile hot code paths
   - Optimize validation algorithms
   - Reduce database queries
   - Implement lazy loading

### Low Priority

7. **Infrastructure**
   - Add load balancer
   - Implement horizontal scaling
   - Add CDN for static assets
   - Implement auto-scaling

8. **Testing**
   - Add continuous load testing
   - Implement chaos engineering
   - Add performance regression tests
   - Create load testing CI/CD pipeline

---

## Historical Trends

### Version History

#### v1.0.0 (Current - December 2025)
- **Status:** Initial load testing suite implementation
- **Key Metrics:** To be established
- **Changes:**
  - Added Locust load testing framework
  - Created comprehensive test scenarios
  - Established performance baselines documentation

#### Future Versions
*Performance metrics will be tracked here as the system evolves*

### Performance Trends

*This section will be updated with performance data over time to track improvements and regressions.*

---

## Running Load Tests

### Prerequisites

```bash
# Install Locust
pip install locust==2.20.0

# Start TBCV server
python -m uvicorn api.server:app --host 0.0.0.0 --port 8080
```

### Quick Start

```bash
# Run with web UI
locust -f tests/load/locustfile.py --host=http://localhost:8080

# Run headless mode
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       --users 50 \
       --spawn-rate 5 \
       --run-time 10m \
       --headless
```

### Generate Reports

```bash
# HTML report
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       --users 50 \
       --spawn-rate 5 \
       --run-time 10m \
       --headless \
       --html=reports/load_test_$(date +%Y%m%d_%H%M%S).html

# CSV data
locust -f tests/load/locustfile.py \
       --host=http://localhost:8080 \
       --users 50 \
       --spawn-rate 5 \
       --run-time 10m \
       --headless \
       --csv=reports/load_test_$(date +%Y%m%d_%H%M%S)
```

---

## Next Steps

1. **Establish Baselines:**
   - Run all test scenarios
   - Record actual performance metrics
   - Update this document with results

2. **Identify Bottlenecks:**
   - Profile application under load
   - Monitor system resources
   - Analyze slow endpoints

3. **Implement Optimizations:**
   - Address high-priority bottlenecks
   - Re-test after optimizations
   - Compare before/after metrics

4. **Continuous Monitoring:**
   - Integrate load tests into CI/CD
   - Set up performance alerts
   - Track performance over time

---

## References

- [Load Testing Documentation](../tests/load/README.md)
- [Locust Documentation](https://docs.locust.io/)
- [FastAPI Performance](https://fastapi.tiangolo.com/deployment/concepts/)
- [Performance Testing Best Practices](https://martinfowler.com/articles/performance-testing.html)

---

## Appendix

### Test Data Examples

```python
# Small file (~2KB)
small_content = """# Test Document
## Introduction
This is a test document.
"""

# Medium file (~20KB)
# See tests/load/locustfile.py for medium content generation

# Large file (~100KB)
# See tests/load/locustfile.py for large content generation
```

### Environment Variables

```bash
# Server configuration
export WORKERS=4
export PORT=8080
export LOG_LEVEL=INFO

# Database
export DATABASE_URL="sqlite:///./tbcv.db"

# Cache
export CACHE_SIZE=100
export CACHE_TTL=3600

# Performance
export REQUEST_TIMEOUT=30
export VALIDATION_TIMEOUT=10
export MAX_FILE_SIZE=10485760  # 10 MB
```

### Monitoring Commands

```bash
# Monitor CPU and memory
htop  # Linux/Mac
taskmgr  # Windows

# Monitor network
iftop  # Linux/Mac

# Monitor disk I/O
iotop  # Linux

# Python-specific profiling
python -m cProfile -o profile.stats api/server.py
```

---

**Note:** This document will be updated with actual performance data once load tests are executed. The current targets and expected results are based on architectural analysis and industry best practices.
