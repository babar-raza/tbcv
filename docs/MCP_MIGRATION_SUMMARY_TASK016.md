# TASK-016: MCP Endpoint Migration Summary

## Task Description

Migrate FastAPI endpoints in `api/server.py` to use MCP async client instead of direct orchestrator/agent calls.

## Completed Work

### 1. Infrastructure Setup ✅

#### api/mcp_helpers.py
**Status**: Already exists from TASK-002, verified complete

**Key Features**:
- `get_api_mcp_client()` - Singleton MCP client instance for FastAPI
- `MCPClientDependency()` - FastAPI dependency injection class
- `mcp_error_to_http_exception()` - Error conversion
- `format_mcp_response()` - Consistent response formatting
- `call_mcp_method()` / `call_mcp_method_formatted()` - Convenience functions

#### svc/mcp_client.py
**Status**: Extended with recommendation methods ✅

**Added Methods to MCPAsyncClient** (lines 1972-2168):
```python
async def generate_recommendations(validation_id, threshold, types)
async def rebuild_recommendations(validation_id, threshold)
async def get_recommendations(validation_id, status, rec_type)
async def review_recommendation(recommendation_id, action, notes)
async def bulk_review_recommendations(recommendation_ids, action, notes)
async def apply_recommendations(validation_id, recommendation_ids, dry_run, create_backup)
async def delete_recommendation(recommendation_id)
async def mark_recommendations_applied(recommendation_ids)
```

All recommendation methods now available in MCPAsyncClient for use in API endpoints.

### 2. Exception Handling ✅

#### api/server.py Modifications

**Import Block** (lines 618-632):
```python
from api.mcp_helpers import (
    mcp_error_to_http_exception,
    format_mcp_response,
    get_api_mcp_client
)
from svc.mcp_client import MCPAsyncClient
from svc.mcp_exceptions import (
    MCPError,
    MCPMethodNotFoundError,
    MCPInvalidParamsError,
    MCPInternalError,
    MCPTimeoutError,
    MCPValidationError,
    MCPResourceNotFoundError
)
```

**Exception Handler** (lines 635-643):
```python
@app.exception_handler(MCPError)
async def handle_mcp_error(request: Request, exc: MCPError):
    """Handle MCP errors and convert to HTTP exceptions."""
    http_exc = mcp_error_to_http_exception(exc)
    return JSONResponse(
        status_code=http_exc.status_code,
        content=http_exc.detail
    )
```

**Added Depends Import** (line 24):
```python
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Query, Response, status, WebSocket, Depends
```

### 3. Example Endpoint Migration ✅

#### GET /api/stats

**Before** (43 lines of code):
```python
@app.get("/api/stats")
async def get_dashboard_stats():
    try:
        # Get all validations count
        all_validations = db_manager.list_validation_results(limit=10000)
        total_validations = len(all_validations)

        # Get all recommendations and calculate stats
        all_recommendations = db_manager.list_recommendations(limit=10000)
        total_recommendations = len(all_recommendations)

        # Count by status
        pending_count = len([r for r in all_recommendations if r.status.value == "pending"])
        # ... more counting logic ...

        return {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_validations": total_validations,
            # ... more fields ...
        }
    except Exception as e:
        logger.exception("Failed to get dashboard stats")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")
```

**After** (7 lines of code):
```python
@app.get("/api/stats")
async def get_dashboard_stats(
    mcp: MCPAsyncClient = Depends(get_api_mcp_client)
):
    """Get dashboard statistics for real-time metrics via MCP."""
    result = await mcp.get_stats()
    return format_mcp_response(result)
```

**Benefits**:
- 86% code reduction (43 lines → 7 lines)
- Automatic error handling via MCP exception handler
- Consistent response format via `format_mcp_response()`
- Testable via mocking `get_api_mcp_client()`
- Retry logic built into MCP client

## Remaining Work

### Endpoints Requiring Migration

According to the comprehensive analysis in `docs/MCP_ENDPOINT_MIGRATION_TASK016.md`:

- **55 endpoints** require migration to MCP
- **18 high-priority** endpoints (validation, approval, enhancement, workflows, stats, system)
- **17 medium-priority** endpoints (recommendations, admin, exports)
- **20 low-priority** endpoints (dashboard-specific, internal, development)

### Migration Pattern

All endpoints should follow this pattern:

```python
# OLD:
@app.get("/api/resource/{id}")
async def get_resource(id: str):
    try:
        result = db_manager.get_resource(id)
        if not result:
            raise HTTPException(status_code=404, detail="Not found")
        return {"data": result}
    except Exception as e:
        logger.exception("Failed")
        raise HTTPException(status_code=500, detail=str(e))

# NEW:
@app.get("/api/resource/{id}")
async def get_resource(
    id: str,
    mcp: MCPAsyncClient = Depends(get_api_mcp_client)
):
    """Get resource via MCP."""
    result = await mcp.get_resource(id)
    return format_mcp_response(result)
```

### High Priority Endpoints (Next Steps)

1. **Validation Endpoints**:
   - POST /api/validate
   - POST /api/validate/file
   - POST /api/validate/batch
   - GET /api/validations
   - GET /api/validations/{id}
   - GET /api/validations/history/{file_path}
   - POST /api/validations/{id}/revalidate

2. **Approval Endpoints**:
   - POST /api/validations/{id}/approve
   - POST /api/validations/{id}/reject
   - POST /api/validations/bulk/approve
   - POST /api/validations/bulk/reject

3. **Enhancement Endpoints**:
   - POST /api/enhance
   - POST /api/enhance/{id}
   - POST /api/enhance/batch
   - POST /api/enhance/auto-apply

4. **Workflow Endpoints**:
   - POST /workflows/validate-directory
   - GET /api/workflows
   - GET /workflows/{id}
   - POST /workflows/{id}/control
   - GET /workflows/{id}/report
   - GET /workflows/{id}/summary
   - DELETE /workflows/{id}
   - POST /api/workflows/bulk-delete

5. **System Endpoints**:
   - ✅ GET /api/stats (COMPLETE)
   - GET /health/detailed
   - GET /admin/status

## Implementation Strategy

### Phase 1: Critical Path (Est. 4-6 hours)
- [ ] Validation endpoints (7 endpoints)
- [ ] Approval endpoints (4 endpoints)
- [ ] System stats (1 endpoint - DONE)

### Phase 2: Core Features (Est. 4-6 hours)
- [ ] Enhancement endpoints (4 endpoints)
- [ ] Workflow endpoints (8 endpoints)

### Phase 3: Management & Admin (Est. 3-4 hours)
- [ ] Recommendation endpoints (9 endpoints)
- [ ] Admin cache endpoints (4 endpoints)
- [ ] Admin system endpoints (4 endpoints)

### Phase 4: Export & Reporting (Est. 2-3 hours)
- [ ] Export endpoints (3 endpoints)
- [ ] Audit & performance endpoints (2 endpoints)
- [ ] Validator discovery endpoint (1 endpoint)

### Phase 5: Testing & Documentation (Est. 4-6 hours)
- [ ] Unit tests for migrated endpoints
- [ ] Integration tests with MCP client
- [ ] Update API documentation
- [ ] Performance benchmarking

## Special Considerations

### 1. Complex File Handling

Some endpoints (POST /api/validate) have intricate file handling:
- Temporary file creation
- Path normalization
- Content preservation

**Strategy**: Keep file handling in endpoint, pass normalized paths to MCP.

### 2. Background Tasks

Workflow endpoints use FastAPI `BackgroundTasks`:

```python
background_tasks.add_task(process_workflow, ...)
```

**Strategy**: Replace with MCP workflow creation:

```python
result = await mcp.create_workflow("validate_directory", params)
```

### 3. LiveBus Publishing

Many endpoints publish to LiveBus for WebSocket updates:

```python
await live_bus.publish_validation_update(validation_id, event, data)
```

**Strategy**: Keep LiveBus in endpoints until MCP server handles internally.

### 4. Dashboard-Specific Logic

Some endpoints have UI-specific response formatting.

**Strategy**: Use `format_mcp_response()` with metadata to preserve custom fields.

## Testing Plan

### 1. Unit Tests
- Test individual MCP client methods
- Mock MCP server responses
- Verify error handling

### 2. Integration Tests
- Test FastAPI endpoints with real MCP client
- Verify dependency injection works
- Test exception handling flow

### 3. E2E Tests
- Full workflow through API
- WebSocket updates
- Background task processing

### 4. Performance Tests
- Measure MCP layer overhead
- Compare before/after latency
- Load testing with concurrent requests

### 5. Backward Compatibility
- Verify response formats match current API
- Check existing clients still work
- Validate error messages unchanged

## Metrics & Success Criteria

### Code Quality
- ✅ Reduced code duplication
- ✅ Consistent error handling
- ✅ Improved testability

### Performance
- Target: < 10ms additional latency from MCP layer
- Maintain current throughput
- No degradation in error rates

### Coverage
- **Phase 1**: 12/55 endpoints migrated (22%)
- **Phase 2**: 24/55 endpoints migrated (44%)
- **Phase 3**: 41/55 endpoints migrated (75%)
- **Phase 4**: 55/55 endpoints migrated (100%)

## Files Modified

| File | Status | Lines Changed |
|------|--------|---------------|
| `api/mcp_helpers.py` | ✅ Complete | N/A (existed) |
| `svc/mcp_client.py` | ✅ Complete | +198 (added recommendation methods) |
| `api/server.py` | 🔄 In Progress | +16 (imports & exception handler), -36 (stats endpoint) |

## Next Steps

1. **Immediate**: Migrate high-priority validation endpoints
2. **Short-term**: Complete approval and enhancement endpoints
3. **Medium-term**: Migrate workflow and admin endpoints
4. **Long-term**: Complete export/reporting endpoints and comprehensive testing

## Estimated Effort

Based on the example migration (GET /api/stats):

- **Simple endpoint** (like stats): 10-15 minutes
- **Complex endpoint** (like validate): 30-45 minutes
- **Testing per endpoint**: 15-20 minutes

**Total Remaining Effort**:
- High priority (11 endpoints): 4-6 hours
- Medium priority (21 endpoints): 6-9 hours
- Low priority (23 endpoints): 4-6 hours
- Testing & Documentation: 4-6 hours

**Grand Total**: 18-27 hours

## Conclusion

The foundation for MCP endpoint migration is complete:
- ✅ MCP client with all required methods
- ✅ Exception handling framework
- ✅ Helper functions for dependency injection and response formatting
- ✅ One endpoint successfully migrated as example

The remaining work follows a clear pattern and can be completed incrementally, testing after each batch of migrations. The example GET /api/stats migration demonstrates an 86% code reduction while improving error handling, testability, and maintainability.

## References

- Detailed endpoint analysis: `docs/MCP_ENDPOINT_MIGRATION_TASK016.md`
- MCP client implementation: `svc/mcp_client.py`
- Helper functions: `api/mcp_helpers.py`
- Server implementation: `api/server.py`
