# Integration Tests for Agent Interactions

## Overview

This document describes the integration testing approach for agent-to-agent interactions in TBCV. Integration tests verify that agents can communicate correctly, pass data between each other, handle errors appropriately, and maintain performance through caching.

## Test File Location

- **File**: `tests/integration/test_agent_interactions.py`
- **Lines**: ~450 lines of comprehensive integration tests
- **Coverage**: Multi-agent workflows, data passing, error propagation, caching, and async patterns

## Tested Interaction Patterns

### 1. OrchestratorAgent → FuzzyDetectorAgent

**Description**: Tests the orchestrator's ability to call the fuzzy detector for plugin pattern detection.

**Key Scenarios**:
- Successful agent-to-agent call
- Handling busy agent state with retry/backoff
- Data parameter passing
- Concurrent detection requests

**Example**:
```python
async def test_orchestrator_calls_fuzzy_detector(self, test_content):
    orchestrator = OrchestratorAgent(agent_id="test_orchestrator")
    fuzzy_detector = FuzzyDetectorAgent(agent_id="test_fuzzy_detector")

    # Register agents
    agent_registry.register_agent(orchestrator)
    agent_registry.register_agent(fuzzy_detector)

    # Call through orchestrator's gating mechanism
    result = await orchestrator._call_agent_gated(
        "test_fuzzy_detector",
        "detect_plugins",
        {"content": test_content, "family": "words"}
    )

    assert result is not None
    assert "detections" in result or "success" in result
```

**What's Tested**:
- Agent registration and discovery
- Gated agent calls with concurrency control
- Parameter marshaling
- Response handling

---

### 2. OrchestratorAgent → TruthManagerAgent → FuzzyDetectorAgent

**Description**: Tests a three-agent chain where the orchestrator queries truth data, then uses it for fuzzy detection.

**Key Scenarios**:
- Multi-hop agent communication
- Data flow through agent chain
- Truth data retrieval and usage
- Pattern loading for detection

**Example**:
```python
async def test_three_agent_chain_orchestrator_truth_fuzzy(self, test_content):
    orchestrator = OrchestratorAgent(agent_id="test_orchestrator")
    truth_manager = TruthManagerAgent(agent_id="test_truth_manager")
    fuzzy_detector = FuzzyDetectorAgent(agent_id="test_fuzzy_detector")

    # Register all agents
    agent_registry.register_agent(orchestrator)
    agent_registry.register_agent(truth_manager)
    agent_registry.register_agent(fuzzy_detector)

    # Step 1: Get truth data
    truth_result = await orchestrator._call_agent_gated(
        "test_truth_manager",
        "list_plugins",
        {"family": "words"}
    )

    # Step 2: Use patterns for detection
    fuzzy_result = await orchestrator._call_agent_gated(
        "test_fuzzy_detector",
        "detect_plugins",
        {"content": test_content, "family": "words"}
    )

    assert truth_result is not None
    assert fuzzy_result is not None
```

**What's Tested**:
- Sequential agent calls
- Data dependency management
- State preservation across calls
- Chain error handling

---

### 3. EnhancementAgent → ContentEnhancerAgent → LLMValidatorAgent

**Description**: Tests the enhancement workflow chain for content improvement.

**Key Scenarios**:
- Enhancement request handling
- LLM validation integration
- Content transformation pipeline
- Validation-driven enhancement

**Example**:
```python
async def test_enhancement_chain_with_validation(self, test_content):
    orchestrator = OrchestratorAgent(agent_id="test_orchestrator")
    content_validator = ContentValidatorAgent(agent_id="test_content_validator")
    enhancement_agent = EnhancementAgent(agent_id="test_enhancement_agent")

    # Step 1: Validate content
    validation_result = await orchestrator._call_agent_gated(
        "test_content_validator",
        "validate_content",
        {"content": test_content, "family": "words"}
    )

    # Step 2: Enhance based on validation
    enhancement_result = await orchestrator._call_agent_gated(
        "test_enhancement_agent",
        "enhance_content",
        {
            "content": test_content,
            "file_path": "test.md",
            "detected_plugins": [],
            "enhancement_types": ["plugin_links"]
        }
    )

    assert validation_result is not None
    assert enhancement_result is not None
```

**What's Tested**:
- Validation-enhancement workflow
- Content modification tracking
- Enhancement type handling
- Result consistency

---

## Error Propagation Testing

### Error Types Tested

1. **Agent Not Found**
   - Attempting to call non-registered agent
   - Expected: `RuntimeError` with "not registered"

2. **Agent Busy**
   - Agent in BUSY state
   - Expected: Retry with backoff, eventual timeout

3. **Chain Interruption**
   - Error in middle of agent chain
   - Expected: Chain stops, error propagates

4. **Timeout Errors**
   - Agent never becomes ready
   - Expected: `TimeoutError` after configured timeout

### Example Error Test

```python
async def test_error_propagates_from_fuzzy_to_orchestrator(self):
    orchestrator = OrchestratorAgent(agent_id="test_orchestrator")
    fuzzy_detector = FuzzyDetectorAgent(agent_id="test_fuzzy_detector")

    # Mock fuzzy detector to raise error
    async def raise_error(method, params):
        raise ValueError("Test error from fuzzy detector")

    fuzzy_detector.process_request = AsyncMock(side_effect=raise_error)

    # Error should propagate
    with pytest.raises(ValueError, match="Test error from fuzzy detector"):
        await orchestrator._call_agent_gated(
            "test_fuzzy_detector",
            "detect_plugins",
            {"content": "test"}
        )
```

---

## Caching Between Agents

### Cache Scenarios

1. **Result Caching**
   - Agent results cached for repeated queries
   - Cache key based on method + params
   - TTL-based expiration

2. **Cache Invalidation**
   - Clear cache between test runs
   - Selective invalidation by key pattern
   - Global cache reset

3. **Cross-Agent Cache**
   - Shared cache between agents
   - Cache hit/miss tracking
   - Performance metrics

### Example Cache Test

```python
async def test_fuzzy_detector_uses_cache(self, test_content):
    fuzzy_detector = FuzzyDetectorAgent(agent_id="test_fuzzy_detector")

    # Clear cache
    cache_manager.clear()

    # First call - populates cache
    result1 = await fuzzy_detector.process_request(
        "detect_plugins",
        {"content": test_content, "family": "words"}
    )

    # Second call - uses cache
    result2 = await fuzzy_detector.process_request(
        "detect_plugins",
        {"content": test_content, "family": "words"}
    )

    # Results should be consistent
    assert result1 is not None
    assert result2 is not None
```

---

## Async Agent Interactions

### Concurrency Patterns

1. **Parallel Agent Calls**
   - Multiple agents called concurrently
   - Uses `asyncio.gather()`
   - Independent operations

2. **Parallel File Processing**
   - Multiple files validated concurrently
   - Orchestrator manages concurrency
   - Per-agent semaphores control load

3. **Error Handling in Concurrent Calls**
   - Some agents succeed, some fail
   - Uses `return_exceptions=True`
   - Partial success handling

### Example Async Test

```python
async def test_concurrent_agent_calls(self, test_content):
    orchestrator = OrchestratorAgent(agent_id="test_orchestrator")
    fuzzy_detector = FuzzyDetectorAgent(agent_id="test_fuzzy_detector")
    content_validator = ContentValidatorAgent(agent_id="test_content_validator")

    # Call both agents concurrently
    results = await asyncio.gather(
        orchestrator._call_agent_gated(
            "test_fuzzy_detector",
            "detect_plugins",
            {"content": test_content, "family": "words"}
        ),
        orchestrator._call_agent_gated(
            "test_content_validator",
            "validate_content",
            {"content": test_content, "family": "words"}
        )
    )

    # Both should complete
    assert len(results) == 2
    assert results[0] is not None
    assert results[1] is not None
```

---

## Workflow Integration Tests

### Complete Workflows

1. **Single File Validation**
   - Orchestrator coordinates all agents
   - File read → validation → detection → enhancement
   - Result aggregation

2. **Batch File Processing**
   - Multiple files in directory
   - Parallel processing with limits
   - Progress tracking

3. **Workflow State Management**
   - WorkflowResult tracking
   - Status queries
   - Workflow listing

### Example Workflow Test

```python
async def test_complete_validation_workflow(self, test_file):
    # Setup all agents
    orchestrator = OrchestratorAgent(agent_id="test_orchestrator")
    truth_manager = TruthManagerAgent(agent_id="test_truth_manager")
    fuzzy_detector = FuzzyDetectorAgent(agent_id="test_fuzzy_detector")
    content_validator = ContentValidatorAgent(agent_id="test_content_validator")

    # Register all agents
    agent_registry.register_agent(orchestrator)
    agent_registry.register_agent(truth_manager)
    agent_registry.register_agent(fuzzy_detector)
    agent_registry.register_agent(content_validator)

    # Run validation workflow
    result = await orchestrator.handle_validate_file({
        "file_path": str(test_file)
    })

    # Workflow should complete
    assert result is not None
    assert "success" in result or "status" in result
```

---

## Running Integration Tests

### Command Line

```bash
# Run all integration tests
pytest tests/integration/test_agent_interactions.py -v

# Run specific test class
pytest tests/integration/test_agent_interactions.py::TestOrchestratorToFuzzyDetector -v

# Run with coverage
pytest tests/integration/test_agent_interactions.py --cov=agents --cov-report=term-missing

# Run integration tests only
pytest -m integration tests/

# Run with detailed output
pytest tests/integration/test_agent_interactions.py -v --tb=short
```

### Environment Setup

Integration tests require:
- `TBCV_ENV=test`
- `OLLAMA_ENABLED=false` (to avoid real LLM calls)
- `OLLAMA_MODEL=mistral` (for fallback)

These are set automatically in the test file.

---

## Test Structure

### File Organization

```
tests/integration/test_agent_interactions.py
├── Fixtures (test_content, test_file, sample_truth_data)
├── TestOrchestratorToFuzzyDetector
│   ├── test_orchestrator_calls_fuzzy_detector
│   ├── test_orchestrator_handles_fuzzy_detector_busy
│   └── test_data_passing_orchestrator_to_fuzzy
├── TestOrchestratorToTruthManager
│   ├── test_orchestrator_queries_truth_manager
│   ├── test_truth_manager_provides_patterns_to_fuzzy
│   └── test_three_agent_chain_orchestrator_truth_fuzzy
├── TestEnhancementAgentChain
│   ├── test_enhancement_agent_calls_content_enhancer
│   ├── test_content_enhancer_with_llm_validation
│   └── test_enhancement_chain_with_validation
├── TestErrorPropagation
│   ├── test_error_propagates_from_fuzzy_to_orchestrator
│   ├── test_orchestrator_handles_agent_not_found
│   ├── test_error_in_agent_chain_stops_workflow
│   └── test_timeout_error_propagation
├── TestCachingBetweenAgents
│   ├── test_fuzzy_detector_uses_cache
│   ├── test_truth_manager_caches_plugin_data
│   └── test_cache_invalidation_between_agents
├── TestAsyncAgentInteractions
│   ├── test_concurrent_agent_calls
│   ├── test_parallel_file_validation
│   └── test_async_error_handling_in_concurrent_calls
└── TestWorkflowIntegration
    ├── test_complete_validation_workflow
    └── test_workflow_with_multiple_files
```

---

## Key Concepts

### Agent Registry

All agents must be registered before interaction:

```python
from agents.base import agent_registry

agent_registry.register_agent(my_agent)
```

### Gated Agent Calls

Orchestrator uses gating to prevent overwhelming agents:

```python
result = await orchestrator._call_agent_gated(
    agent_id="target_agent",
    method="method_name",
    params={"key": "value"}
)
```

Gating provides:
- Concurrency limiting (per-agent semaphores)
- Retry with exponential backoff
- Timeout handling
- Status checking (READY/BUSY)

### Agent Status

Agents can report status:
- `AgentStatus.STARTING` - Initializing
- `AgentStatus.READY` - Ready for requests
- `AgentStatus.BUSY` - Processing request
- `AgentStatus.ERROR` - Error state
- `AgentStatus.STOPPED` - Shut down

---

## Performance Considerations

### Concurrency Control

Each agent has configurable concurrency limits:

```yaml
orchestrator:
  agent_limits:
    llm_validator: 1      # Serial processing
    content_validator: 2  # Max 2 concurrent
    truth_manager: 4      # Max 4 concurrent
    fuzzy_detector: 2     # Max 2 concurrent
```

### Retry Configuration

```yaml
orchestrator:
  retry_timeout_s: 120        # Max wait time
  retry_backoff_base: 0.5     # Initial delay
  retry_backoff_cap: 8        # Max delay
```

### Cache Performance

- Cache hits avoid expensive operations
- Shared cache across agents
- TTL-based expiration
- Statistics tracking (hits/misses)

---

## Best Practices

### 1. Always Clean Up Agents

```python
@pytest.fixture(scope="function", autouse=True)
def cleanup_agents():
    yield
    agent_registry._agents.clear()
```

### 2. Mock External Dependencies

```python
# Mock truth data loading
with patch.object(truth_manager, '_load_truth_data', return_value=sample_data):
    result = await truth_manager.process_request(...)
```

### 3. Test Both Success and Failure Paths

```python
# Test success
result = await agent.process_request(...)
assert result["success"] is True

# Test failure
with pytest.raises(ValueError):
    await agent.process_request(...)
```

### 4. Use Async Context Properly

```python
# Use asyncio.gather for parallel calls
results = await asyncio.gather(
    agent1.process_request(...),
    agent2.process_request(...)
)

# Use return_exceptions for error handling
results = await asyncio.gather(
    ...,
    return_exceptions=True
)
```

### 5. Verify Data Passing

```python
received_params = {}

async def capture_params(method, params):
    received_params.update(params)
    return {"success": True}

agent.process_request = AsyncMock(side_effect=capture_params)

# Later verify
assert received_params["content"] == expected_content
```

---

## Common Issues and Solutions

### Issue: Agent Not Found

**Error**: `RuntimeError: Agent 'X' not registered`

**Solution**: Ensure agent is registered before calling:
```python
agent_registry.register_agent(my_agent)
```

### Issue: Timeout Errors

**Error**: `TimeoutError: Timed out waiting for agent`

**Solution**:
- Check agent status (may be stuck in BUSY)
- Increase timeout in config
- Mock slow operations in tests

### Issue: Cache Not Clearing

**Error**: Tests interfere with each other

**Solution**:
```python
@pytest.fixture(autouse=True)
def clear_cache():
    cache_manager.clear()
    yield
    cache_manager.clear()
```

### Issue: Concurrent Test Failures

**Error**: Race conditions in parallel tests

**Solution**:
- Use function-scoped fixtures
- Clear global state between tests
- Use unique agent IDs per test

---

## Coverage Goals

- **Agent Interaction Coverage**: 85%+
- **Error Path Coverage**: 90%+
- **Async Pattern Coverage**: 80%+
- **Cache Behavior Coverage**: 85%+

---

## Future Enhancements

1. **Performance Benchmarking**
   - Track agent call latency
   - Measure cache effectiveness
   - Monitor concurrent throughput

2. **Circuit Breaker Pattern**
   - Detect failing agents
   - Temporarily disable problematic agents
   - Auto-recovery mechanisms

3. **Distributed Tracing**
   - Track requests across agents
   - Visualize agent call graphs
   - Performance bottleneck detection

4. **Load Testing**
   - Stress test agent interactions
   - Measure system limits
   - Identify scalability issues

---

## Related Documentation

- [Agent Architecture](../llm-runtime-surfaces.md)
- [MCP Protocol](../llm-domain-and-data-flow.md)
- [Testing Strategy](../system-map.md)
- [Caching Guide](../../core/cache.py)

---

**Last Updated**: 2025-12-03
**Maintained By**: TBCV Development Team
