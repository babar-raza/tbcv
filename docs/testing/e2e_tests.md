# End-to-End Workflow Tests Documentation

**TASK-MED-011 Implementation**
**Author:** TBCV Team
**Date:** 2025-12-03
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Test Architecture](#test-architecture)
3. [Test Suites](#test-suites)
4. [Running E2E Tests](#running-e2e-tests)
5. [Test Scenarios](#test-scenarios)
6. [Error Recovery Testing](#error-recovery-testing)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The End-to-End (E2E) workflow tests validate complete user workflows through the TBCV system, ensuring that all components work together correctly from start to finish.

### Purpose

E2E tests verify:
- Complete workflow execution from user input to final output
- Integration between multiple agents and services
- Database persistence and state management
- Error recovery and checkpoint mechanisms
- Multi-file and batch processing capabilities

### Coverage

The E2E test suite includes three main test files:

1. **test_validation_workflow.py** (~300 lines)
   - Single file validation
   - Directory validation
   - Batch validation
   - Error recovery
   - Checkpoint recovery
   - Pause/resume workflows

2. **test_enhancement_workflow.py** (~300 lines)
   - Single file enhancement
   - Validation to enhancement flow
   - Enhancement with recommendations
   - Batch enhancement
   - Progressive enhancement
   - Error recovery

3. **test_approval_workflow.py** (~200 lines)
   - Recommendation approval
   - Reject workflow
   - Batch approval
   - Audit trail verification
   - Complete approval to application flow

**Total:** ~800 lines of comprehensive E2E test coverage

---

## Test Architecture

### Test Structure

```
tests/
├── e2e/
│   ├── __init__.py
│   ├── test_validation_workflow.py      # Validation workflows
│   ├── test_enhancement_workflow.py     # Enhancement workflows
│   ├── test_approval_workflow.py        # Approval workflows
│   ├── test_complete_workflows.py       # Existing MCP workflows
│   └── test_dashboard_flows.py          # Dashboard integration
├── conftest.py                          # Shared fixtures
└── pytest.ini                           # Test configuration
```

### Test Markers

E2E tests use pytest markers for categorization:

```python
@pytest.mark.e2e              # All E2E tests
@pytest.mark.asyncio          # Async tests
@pytest.mark.integration      # Integration tests
@pytest.mark.timeout(60)      # Tests with timeout
```

### Fixtures

Common fixtures available in all E2E tests:

```python
# Database
db_manager                    # Database manager instance

# File system
tmp_path                      # Temporary directory
sample_file                   # Single test markdown file
sample_directory              # Directory with multiple files
large_directory              # Large directory for concurrent tests

# Checkpoint management
checkpoint_manager            # Checkpoint manager for recovery tests

# Agents (auto-registered/unregistered)
# Tests handle agent lifecycle management
```

---

## Test Suites

### 1. Validation Workflow Tests

**File:** `tests/e2e/test_validation_workflow.py`

#### Test Classes

##### TestSingleFileValidationWorkflow
Tests complete single file validation workflows.

**Key Tests:**
- `test_basic_file_validation_end_to_end` - File → Validation → Results
- `test_validation_with_yaml_frontmatter` - YAML parsing and validation
- `test_validation_with_markdown_issues` - Markdown issue detection

**Example:**
```python
async def test_basic_file_validation_end_to_end(self, db_manager, sample_file):
    validator = ContentValidatorAgent("validator")
    agent_registry.register_agent(validator)

    try:
        content = sample_file.read_text()

        result = await validator.process_request("validate_content", {
            "content": content,
            "file_path": str(sample_file),
            "family": "words"
        })

        assert result is not None
        assert "confidence" in result
        assert "issues" in result
    finally:
        agent_registry.unregister_agent("validator")
```

##### TestDirectoryValidationWorkflow
Tests directory-level validation workflows.

**Key Tests:**
- `test_basic_directory_validation` - Validate entire directory
- `test_directory_validation_with_pattern` - Pattern-based file filtering

##### TestBatchValidationWorkflow
Tests batch file validation workflows.

**Key Tests:**
- `test_batch_validation_sequential` - Sequential batch processing
- `test_batch_validation_concurrent` - Concurrent batch processing

##### TestValidationErrorRecovery
Tests error recovery during validation.

**Key Tests:**
- `test_recovery_from_invalid_content` - Handle invalid content gracefully
- `test_recovery_from_file_not_found` - Handle missing files
- `test_recovery_from_checkpoint` - Recover from checkpoint

##### TestPauseResumeWorkflow
Tests workflow pause and resume functionality.

**Key Tests:**
- `test_pause_workflow` - Pause running workflow
- `test_resume_workflow` - Resume paused workflow
- `test_workflow_progress_tracking` - Track workflow progress

### 2. Enhancement Workflow Tests

**File:** `tests/e2e/test_enhancement_workflow.py`

#### Test Classes

##### TestSingleFileEnhancementWorkflow
Tests complete single file enhancement workflows.

**Key Tests:**
- `test_validation_to_enhancement_workflow` - File → Validation → Enhancement → Apply
- `test_enhancement_with_recommendations` - Apply specific recommendations
- `test_enhancement_preview_mode` - Preview without applying

**Example:**
```python
async def test_validation_to_enhancement_workflow(self, db_manager, sample_file):
    validator = ContentValidatorAgent("validator")
    enhancer = EnhancementAgent("enhancer")

    agent_registry.register_agent(validator)
    agent_registry.register_agent(enhancer)

    try:
        content = sample_file.read_text()

        # Step 1: Validate
        validation_result = await validator.process_request("validate_content", {
            "content": content,
            "file_path": str(sample_file),
            "family": "words"
        })

        # Step 2: Enhance
        enhancement_result = await enhancer.process_request("enhance_content", {
            "content": content,
            "file_path": str(sample_file),
            "detected_plugins": [],
            "enhancement_types": ["format_fixes"]
        })

        assert enhancement_result is not None
    finally:
        agent_registry.unregister_agent("validator")
        agent_registry.unregister_agent("enhancer")
```

##### TestBatchEnhancementWorkflow
Tests batch file enhancement workflows.

**Key Tests:**
- `test_batch_enhancement_sequential` - Sequential enhancement
- `test_batch_enhancement_concurrent` - Concurrent enhancement
- `test_batch_enhancement_with_validation_ids` - Enhance based on validation IDs

##### TestEnhancementErrorRecovery
Tests error recovery during enhancement.

**Key Tests:**
- `test_recovery_from_invalid_recommendation` - Handle invalid recommendations
- `test_recovery_from_enhancement_failure` - Recover from failures
- `test_recovery_from_checkpoint` - Resume from checkpoint

##### TestMultiFileEnhancementWorkflows
Tests complex multi-file enhancement scenarios.

**Key Tests:**
- `test_directory_enhancement_workflow` - Enhance entire directory
- `test_selective_file_enhancement` - Enhance only files with issues
- `test_progressive_enhancement_workflow` - Multi-stage enhancement

### 3. Approval Workflow Tests

**File:** `tests/e2e/test_approval_workflow.py`

#### Test Classes

##### TestSingleRecommendationApprovalWorkflow
Tests complete single recommendation approval workflows.

**Key Tests:**
- `test_approve_recommendation_workflow` - Recommendations → Review → Approve → Apply
- `test_reject_recommendation_workflow` - Rejection workflow
- `test_approve_and_apply_workflow` - Complete approval and application
- `test_recommendation_with_confidence_threshold` - Auto-approval based on confidence

**Example:**
```python
def test_approve_recommendation_workflow(self, db_manager):
    # Create recommendation
    validation, recommendation = create_recommendation_for_approval(db_manager)

    # Approve
    updated_rec = db_manager.update_recommendation_status(
        recommendation.id,
        "approved",
        reviewer="test_reviewer",
        review_notes="Looks good"
    )

    # Verify
    assert updated_rec.status == RecommendationStatus.APPROVED
    assert updated_rec.reviewed_by == "test_reviewer"
```

##### TestBatchApprovalWorkflow
Tests batch recommendation approval workflows.

**Key Tests:**
- `test_batch_approve_recommendations` - Batch approval
- `test_selective_batch_approval` - Mixed approval/rejection
- `test_batch_approval_with_conditions` - Conditional approval

##### TestApprovalWorkflowErrorRecovery
Tests error recovery during approval workflows.

**Key Tests:**
- `test_recovery_from_invalid_status_transition` - Handle invalid transitions
- `test_recovery_from_missing_reviewer` - Handle missing reviewer
- `test_recovery_from_concurrent_approval` - Handle race conditions

##### TestApprovalAuditTrail
Tests audit trail during approval workflows.

**Key Tests:**
- `test_audit_trail_creation` - Verify audit logging
- `test_approval_history_tracking` - Track status changes
- `test_reviewer_attribution` - Verify reviewer tracking

##### TestCompleteApprovalToApplicationFlow
Tests complete flow from approval to enhancement application.

**Key Tests:**
- `test_end_to_end_approval_and_enhancement` - Complete workflow validation

---

## Running E2E Tests

### Run All E2E Tests

```bash
# Run all E2E tests
pytest tests/e2e/ -v -m e2e

# Run with coverage
pytest tests/e2e/ -v -m e2e --cov=agents --cov=core --cov=api

# Run specific test file
pytest tests/e2e/test_validation_workflow.py -v

# Run specific test class
pytest tests/e2e/test_validation_workflow.py::TestSingleFileValidationWorkflow -v

# Run specific test
pytest tests/e2e/test_validation_workflow.py::TestSingleFileValidationWorkflow::test_basic_file_validation_end_to_end -v
```

### Run by Category

```bash
# Run only validation tests
pytest tests/e2e/test_validation_workflow.py -v -m e2e

# Run only enhancement tests
pytest tests/e2e/test_enhancement_workflow.py -v -m e2e

# Run only approval tests
pytest tests/e2e/test_approval_workflow.py -v -m e2e

# Run async tests only
pytest tests/e2e/ -v -m asyncio

# Run integration tests
pytest tests/e2e/ -v -m integration
```

### Parallel Execution

```bash
# Run tests in parallel (requires pytest-xdist)
pytest tests/e2e/ -v -m e2e -n auto

# Run with specific number of workers
pytest tests/e2e/ -v -m e2e -n 4
```

### Continuous Integration

```bash
# CI-friendly command with XML output
pytest tests/e2e/ -v -m e2e \
  --junitxml=test-results/e2e-results.xml \
  --cov=agents --cov=core --cov=api \
  --cov-report=xml:coverage.xml \
  --cov-report=html:htmlcov
```

---

## Test Scenarios

### Validation Workflow Scenarios

#### Scenario 1: Single File Validation
**Flow:** File → Validation → Results → Database

**Steps:**
1. Create test markdown file
2. Validate content through ContentValidatorAgent
3. Verify validation results structure
4. Verify database persistence
5. Check for generated recommendations

**Expected Results:**
- Validation result contains confidence score
- Issues are properly identified
- Results are persisted to database
- Recommendations are generated for issues

#### Scenario 2: Directory Validation
**Flow:** Directory → Batch Validation → Results

**Steps:**
1. Create directory with multiple files
2. Validate directory through OrchestratorAgent
3. Verify workflow creation
4. Check all files are processed
5. Verify results aggregation

**Expected Results:**
- Workflow is created and tracked
- All files are validated
- Results are properly aggregated
- Progress is tracked

#### Scenario 3: Checkpoint Recovery
**Flow:** Start Workflow → Interrupt → Resume from Checkpoint

**Steps:**
1. Start batch validation workflow
2. Process some files
3. Create checkpoint
4. Simulate interruption
5. Resume from checkpoint
6. Complete remaining files

**Expected Results:**
- Checkpoint is saved correctly
- Workflow resumes from correct position
- No duplicate processing
- All files are validated

### Enhancement Workflow Scenarios

#### Scenario 1: Validation to Enhancement
**Flow:** File → Validation → Enhancement → Apply

**Steps:**
1. Validate file and detect issues
2. Generate recommendations
3. Approve recommendations
4. Apply enhancements
5. Verify enhanced content

**Expected Results:**
- Validation detects issues
- Recommendations are generated
- Enhancements are applied correctly
- Enhanced content is valid

#### Scenario 2: Batch Enhancement
**Flow:** Multiple Files → Concurrent Enhancement → Results

**Steps:**
1. Create batch of files
2. Validate all files
3. Enhance files concurrently
4. Collect results
5. Verify all enhancements

**Expected Results:**
- All files are enhanced
- Concurrent execution succeeds
- No race conditions
- Results are consistent

#### Scenario 3: Progressive Enhancement
**Flow:** File → Multiple Enhancement Passes → Final Result

**Steps:**
1. Start with base content
2. Apply format fixes
3. Apply info text enhancements
4. Apply plugin link enhancements
5. Verify cumulative improvements

**Expected Results:**
- Each pass improves content
- No conflicts between passes
- Final result is valid
- All enhancements are applied

### Approval Workflow Scenarios

#### Scenario 1: Single Recommendation Approval
**Flow:** Recommendation → Review → Approve → Apply

**Steps:**
1. Create recommendation
2. Review recommendation
3. Approve with notes
4. Apply enhancement
5. Mark as applied
6. Verify audit trail

**Expected Results:**
- Status transitions are valid
- Reviewer is tracked
- Audit trail is complete
- Enhancement is applied

#### Scenario 2: Batch Approval
**Flow:** Multiple Recommendations → Batch Review → Mixed Actions

**Steps:**
1. Create batch of recommendations
2. Review all recommendations
3. Approve some, reject others
4. Apply approved enhancements
5. Verify all statuses

**Expected Results:**
- All recommendations are processed
- Statuses are correct
- Only approved ones are applied
- Audit trail is complete

#### Scenario 3: Conditional Approval
**Flow:** Recommendations → Filter by Criteria → Auto-approve

**Steps:**
1. Create recommendations with varying confidence
2. Apply confidence threshold (e.g., >0.90)
3. Auto-approve high confidence
4. Flag low confidence for review
5. Verify filtering logic

**Expected Results:**
- High confidence auto-approved
- Low confidence requires review
- Threshold is applied correctly
- Audit shows auto-approval

---

## Error Recovery Testing

### Validation Error Recovery

#### Invalid Content
**Test:** `test_recovery_from_invalid_content`

Validates handling of:
- Empty files
- Invalid UTF-8
- Malformed YAML
- Broken markdown

**Expected:** Graceful error handling, no crashes

#### Missing Files
**Test:** `test_recovery_from_file_not_found`

Validates handling of:
- Non-existent files
- Permission denied
- Invalid paths

**Expected:** Clear error messages, workflow continues

#### Checkpoint Recovery
**Test:** `test_recovery_from_checkpoint`

Validates:
- Checkpoint saving
- Checkpoint loading
- Workflow resumption
- No duplicate processing

**Expected:** Complete recovery, consistent state

### Enhancement Error Recovery

#### Invalid Recommendations
**Test:** `test_recovery_from_invalid_recommendation`

Validates handling of:
- Invalid recommendation types
- Malformed content
- Missing required fields

**Expected:** Skip invalid recommendations, continue workflow

#### Enhancement Failures
**Test:** `test_recovery_from_enhancement_failure`

Validates handling of:
- Empty content
- Invalid enhancements
- Application failures

**Expected:** Graceful degradation, error reporting

### Approval Error Recovery

#### Invalid Status Transitions
**Test:** `test_recovery_from_invalid_status_transition`

Validates:
- Status validation
- Transition rules
- State consistency

**Expected:** Invalid transitions prevented

#### Concurrent Approval
**Test:** `test_recovery_from_concurrent_approval`

Validates handling of:
- Race conditions
- Concurrent updates
- State consistency

**Expected:** Consistent final state

---

## Best Practices

### Writing E2E Tests

#### 1. Test Complete Workflows
```python
# Good: Tests complete user workflow
async def test_validation_to_enhancement_workflow(self):
    # Step 1: Validate
    validation_result = await validator.validate(content)

    # Step 2: Generate recommendations
    recommendations = await recommender.generate(validation_result)

    # Step 3: Apply enhancements
    enhanced = await enhancer.enhance(content, recommendations)

    # Verify complete flow
    assert enhanced is not None
```

#### 2. Use Fixtures for Setup
```python
# Good: Use fixtures for reusable setup
@pytest.fixture
def sample_file(tmp_path):
    content = create_test_content()
    file_path = tmp_path / "test.md"
    file_path.write_text(content)
    return file_path

def test_workflow(sample_file):
    # Test uses fixture
    result = validate(sample_file)
```

#### 3. Clean Up Resources
```python
# Good: Always clean up agents
async def test_something(self):
    agent = SomeAgent("agent")
    agent_registry.register_agent(agent)

    try:
        # Test code here
        result = await agent.process_request(...)
        assert result is not None
    finally:
        # Always unregister
        agent_registry.unregister_agent("agent")
```

#### 4. Verify Database State
```python
# Good: Verify persistence
async def test_workflow_persistence(self, db_manager):
    # Execute workflow
    result = await execute_workflow()

    # Verify database
    with db_manager.get_session() as session:
        records = session.query(Model).all()
        assert len(records) > 0
```

#### 5. Test Error Cases
```python
# Good: Test both success and failure
async def test_with_error_handling(self):
    # Test success case
    result = await process_valid_input()
    assert result is not None

    # Test error case
    result = await process_invalid_input()
    # Verify graceful handling
```

### Test Organization

#### File Structure
```
tests/e2e/
├── test_validation_workflow.py     # All validation tests
├── test_enhancement_workflow.py    # All enhancement tests
├── test_approval_workflow.py       # All approval tests
└── README.md                       # Test documentation
```

#### Class Organization
```python
# Organize by workflow type
class TestSingleFileValidationWorkflow:
    """Single file validation tests."""
    pass

class TestBatchValidationWorkflow:
    """Batch validation tests."""
    pass

class TestValidationErrorRecovery:
    """Error recovery tests."""
    pass
```

### Naming Conventions

#### Test Names
```python
# Pattern: test_<what>_<scenario>
test_basic_file_validation_end_to_end
test_validation_to_enhancement_workflow
test_approve_recommendation_workflow
test_recovery_from_invalid_content
```

#### Fixture Names
```python
# Pattern: <resource>_<variant>
sample_file
sample_directory
large_directory
checkpoint_manager
```

---

## Troubleshooting

### Common Issues

#### Issue: Tests Hang
**Symptom:** Tests never complete

**Possible Causes:**
- Event loop issues
- Deadlock in async code
- Missing timeout

**Solutions:**
```python
# Add timeout
@pytest.mark.timeout(60)
async def test_something(self):
    ...

# Use asyncio.wait_for
result = await asyncio.wait_for(
    some_async_operation(),
    timeout=30.0
)
```

#### Issue: Agent Not Found
**Symptom:** `Agent not registered` errors

**Possible Causes:**
- Agent not registered
- Agent unregistered too early
- Name mismatch

**Solutions:**
```python
# Verify registration
agent = SomeAgent("agent_id")
agent_registry.register_agent(agent)

# Verify name matches
result = await agent_registry.get_agent("agent_id")

# Always unregister in finally
try:
    # Test code
    pass
finally:
    agent_registry.unregister_agent("agent_id")
```

#### Issue: Database State Contamination
**Symptom:** Tests fail when run together but pass individually

**Possible Causes:**
- Shared database state
- Transaction not rolled back
- Fixtures not properly cleaned

**Solutions:**
```python
# Use function-scoped fixtures
@pytest.fixture(scope="function")
def db_manager():
    # Setup
    yield manager
    # Cleanup

# Use transactions
with db_manager.get_session() as session:
    # Operations in transaction
    session.commit()  # or rollback()
```

#### Issue: Concurrent Test Failures
**Symptom:** Tests fail with race conditions

**Possible Causes:**
- Shared resources
- Global state
- Concurrent access

**Solutions:**
```python
# Use locks for shared resources
import asyncio
lock = asyncio.Lock()

async with lock:
    # Protected operation
    pass

# Avoid global state
# Use fixtures for isolated state
```

#### Issue: Checkpoint Not Found
**Symptom:** Checkpoint recovery fails

**Possible Causes:**
- Checkpoint not saved
- Wrong workflow ID
- Checkpoint expired

**Solutions:**
```python
# Verify checkpoint saved
checkpoint_manager.save_checkpoint(workflow_id, data)
loaded = checkpoint_manager.load_checkpoint(workflow_id)
assert loaded is not None

# Use consistent IDs
workflow_id = f"test_workflow_{int(time.time())}"
```

### Debug Tips

#### Enable Verbose Logging
```bash
# Run with verbose output
pytest tests/e2e/ -v -s

# Show log output
pytest tests/e2e/ -v --log-cli-level=DEBUG
```

#### Use pdb for Debugging
```python
# Add breakpoint
async def test_something(self):
    result = await some_operation()
    import pdb; pdb.set_trace()  # Debugger stops here
    assert result is not None
```

#### Check Database State
```python
# Print database contents
def test_something(self, db_manager):
    with db_manager.get_session() as session:
        records = session.query(Model).all()
        print(f"Found {len(records)} records")
        for record in records:
            print(f"  {record.to_dict()}")
```

#### Isolate Failing Tests
```bash
# Run single test
pytest tests/e2e/test_validation_workflow.py::TestSingleFileValidationWorkflow::test_basic_file_validation_end_to_end -v

# Run with maximum verbosity
pytest tests/e2e/test_validation_workflow.py -vvv
```

---

## Maintenance

### Adding New Tests

When adding new E2E tests:

1. **Identify the workflow type** (validation, enhancement, approval)
2. **Add to appropriate file** (test_validation_workflow.py, etc.)
3. **Follow naming conventions** (test_<what>_<scenario>)
4. **Use existing fixtures** when possible
5. **Clean up resources** in finally blocks
6. **Document the test** with clear docstrings
7. **Update this documentation** with new scenarios

### Updating Tests

When modifying E2E tests:

1. **Verify backward compatibility** - don't break existing tests
2. **Update documentation** - keep this file in sync
3. **Run full test suite** - ensure no regressions
4. **Review error handling** - tests should handle failures gracefully

### Test Maintenance Schedule

- **Weekly:** Run full E2E test suite
- **Monthly:** Review test coverage
- **Quarterly:** Update documentation
- **Annually:** Refactor and optimize tests

---

## Related Documentation

- [Testing Strategy](../architecture/testing_strategy.md)
- [Agent Architecture](../architecture/agents.md)
- [Database Schema](../architecture/database.md)
- [Workflow Design](../architecture/workflows.md)
- [API Documentation](../api/README.md)

---

## Conclusion

The E2E workflow tests provide comprehensive validation of TBCV system workflows, ensuring that all components work together correctly. By testing complete user journeys from start to finish, these tests catch integration issues that unit tests might miss.

**Key Takeaways:**
- E2E tests validate complete workflows
- Tests cover validation, enhancement, and approval flows
- Error recovery is thoroughly tested
- Checkpoint mechanisms ensure workflow resumption
- Comprehensive audit trail verification

**Next Steps:**
1. Run the E2E test suite
2. Review test results
3. Address any failures
4. Expand coverage as needed
5. Keep documentation updated

---

**Document Version:** 1.0
**Last Updated:** 2025-12-03
**Maintained By:** TBCV Development Team
