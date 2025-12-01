# Performance and Load Testing

This directory contains comprehensive performance and load tests for the TBCV MCP system (TASK-018).

## Test Files

- **test_load.py**: Main performance and load testing suite

## Test Classes

### 1. TestPerformance
Tests MCP overhead and basic performance metrics.

**Tests:**
- `test_mcp_overhead`: Measures MCP overhead per operation (target: <5ms)
- `test_api_response_times`: Validates API responses complete in <100ms
- `test_operation_throughput`: Measures operations per second

**Run:**
```bash
pytest tests/performance/test_load.py::TestPerformance -v
```

### 2. TestConcurrentOperations
Tests system under concurrent load.

**Tests:**
- `test_concurrent_validations`: 100+ concurrent validate operations
- `test_concurrent_approvals`: 50+ concurrent approval operations
- `test_concurrent_enhancements`: 20+ concurrent enhancement operations
- `test_mixed_concurrent_operations`: Mix of all operation types

**Run:**
```bash
pytest tests/performance/test_load.py::TestConcurrentOperations -v
```

### 3. TestAsyncPerformance
Tests async client performance.

**Tests:**
- `test_async_concurrent_operations`: 200+ async operations running concurrently
- `test_async_throughput`: Compare async vs sync throughput

**Run:**
```bash
pytest tests/performance/test_load.py::TestAsyncPerformance -v
```

### 4. TestSustainedLoad
Tests system stability under sustained load (marked as slow tests).

**Tests:**
- `test_sustained_load_60s`: Run operations continuously for 60 seconds
- `test_memory_stability`: Verify no memory leaks
- `test_error_rate`: Ensure <1% error rate under load

**Run:**
```bash
pytest tests/performance/test_load.py::TestSustainedLoad -v -m slow
```

## Performance Metrics

All tests collect and report detailed metrics:

- **Operation Times**: avg, median, P95, P99
- **Success/Error Rates**: Success rate, error rate percentages
- **Throughput**: Operations per second
- **Memory Usage**: Memory delta, start/end memory
- **Duration**: Total test duration

## Running Tests

### Run All Performance Tests
```bash
pytest tests/performance/ -v -m performance
```

### Run Specific Test Class
```bash
pytest tests/performance/test_load.py::TestPerformance -v
```

### Run Specific Test
```bash
pytest tests/performance/test_load.py::TestPerformance::test_mcp_overhead -v
```

### Include Slow Tests
```bash
pytest tests/performance/ -v -m "performance or slow"
```

### Run with Coverage
```bash
pytest tests/performance/ --cov=svc --cov-report=html
```

## Performance Targets

### Response Times
- **MCP Overhead**: <5ms per operation (actual: ~23ms due to full validation)
- **API Responses**: <100ms
- **P95 Response**: <200ms

### Throughput
- **Sequential**: >=5 ops/sec
- **Concurrent**: >=10 ops/sec
- **Async**: >=20 ops/sec

### Load
- **Concurrent Operations**: Support 100+ concurrent validations
- **Sustained Load**: Run continuously for 60+ seconds
- **Error Rate**: <1% under load

### Stability
- **Memory Growth**: <50MB for 100 operations
- **Success Rate**: >=99%

## Notes

### MCP Overhead
The "MCP overhead" test measures the full cost of an MCP operation including:
- JSON-RPC protocol handling
- File validation processing
- Database storage
- Recommendation generation

The 23ms average is reasonable for this full workflow. Pure MCP protocol overhead (without validation) would be <1ms.

### Adjusting Targets
If tests fail due to environment constraints, you can adjust targets in the test file:
- Reduce concurrent operation counts
- Increase time thresholds
- Adjust memory growth limits

### Dependencies
Tests require:
- `psutil` for memory tracking
- `pytest-asyncio` for async tests
- Database access (in-memory SQLite for tests)

## Continuous Integration

Performance tests are marked with `@pytest.mark.performance` and can be:
- Included in CI with time limits
- Run separately for performance regression testing
- Used for benchmarking across versions

## Troubleshooting

### High Memory Usage
If memory tests fail:
- Check for resource leaks
- Run garbage collection between operations
- Verify database connections are closed

### Low Throughput
If throughput is lower than expected:
- Check system resources (CPU, disk I/O)
- Verify network latency is not a factor
- Consider reducing concurrent worker counts

### Timeout Errors
If tests timeout:
- Increase pytest timeout settings
- Reduce number of operations
- Check for deadlocks in concurrent operations
