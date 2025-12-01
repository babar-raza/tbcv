# MCP Endpoint Migration Report (TASK-016)

## Overview

This document details the migration of FastAPI endpoints in `api/server.py` to use the MCP async client instead of direct orchestrator/agent calls.

## Completed Changes

### 1. Added MCP Exception Handlers

**Location**: `api/server.py` lines 614-644

```python
# =============================================================================
# Register MCP Exception Handlers
# =============================================================================

from api.mcp_helpers import (
    mcp_error_to_http_exception,
    format_mcp_response,
    get_api_mcp_client
)
from svc.mcp_exceptions import (
    MCPError,
    MCPMethodNotFoundError,
    MCPInvalidParamsError,
    MCPInternalError,
    MCPTimeoutError,
    MCPValidationError,
    MCPResourceNotFoundError
)

# Register exception handlers for MCP errors
@app.exception_handler(MCPError)
async def handle_mcp_error(request: Request, exc: MCPError):
    """Handle MCP errors and convert to HTTP exceptions."""
    http_exc = mcp_error_to_http_exception(exc)
    return JSONResponse(
        status_code=http_exc.status_code,
        content=http_exc.detail
    )
```

**Status**: ✅ COMPLETE

### 2. Created api/mcp_helpers.py

**Features**:
- FastAPI dependency injection (`get_api_mcp_client()`)
- Response formatting (`format_mcp_response()`)
- Error conversion (`mcp_error_to_http_exception()`)
- Convenience functions (`call_mcp_method()`, `call_mcp_method_formatted()`)

**Status**: ✅ COMPLETE (file already existed from TASK-002)

### 3. Added Recommendation Methods to MCPAsyncClient

**Location**: `svc/mcp_client.py` lines 1972-2168

**Methods Added**:
- `generate_recommendations()`
- `rebuild_recommendations()`
- `get_recommendations()`
- `review_recommendation()`
- `bulk_review_recommendations()`
- `apply_recommendations()`
- `delete_recommendation()`
- `mark_recommendations_applied()`

**Status**: ✅ COMPLETE

## Current State Analysis

### Endpoints Still Using Direct Agent/Orchestrator Access

The following endpoints in `api/server.py` currently use direct agent registry access and need migration:

#### Validation Endpoints

1. **POST /api/validate** (line 1089)
   - Currently: `orchestrator.process_request("validate_file", ...)`
   - Should be: `mcp.validate_file(...)` or `mcp.validate_content(...)`
   - Note: Complex file handling logic (temp files, normalization)

2. **POST /api/validate/file** (line 1191)
   - Currently: `orchestrator.process_request("validate_file", ...)`
   - Should be: `mcp.validate_file(...)`

3. **POST /api/validate/batch** (line 1255)
   - Currently: Direct agent calls
   - Should be: Multiple `mcp.validate_file()` calls or workflow

4. **POST /api/validations/{original_id}/revalidate** (line 1410)
   - Currently: Direct orchestrator call
   - Should be: `mcp.revalidate(validation_id)`

5. **GET /api/validations** (line 1321)
   - Currently: `db_manager.list_validation_results(...)`
   - Should be: `mcp.list_validations(...)`

6. **GET /api/validations/{validation_id}** (line 1346)
   - Currently: `db_manager.get_validation_result(...)`
   - Should be: `mcp.get_validation(validation_id)`

7. **GET /api/validations/history/{file_path:path}** (line 1373)
   - Currently: `db_manager` direct access
   - Should be: `mcp.get_validation_history(file_path)`

#### Approval Endpoints

8. **POST /api/validations/{validation_id}/approve** (line 1865)
   - Currently: Direct `db_manager` update
   - Should be: `mcp.approve([validation_id])`

9. **POST /api/validations/{validation_id}/reject** (line 1932)
   - Currently: Direct `db_manager` update
   - Should be: `mcp.reject([validation_id], reason=...)`

10. **POST /api/validations/bulk/approve** (line 2403)
    - Currently: Direct `db_manager` updates
    - Should be: `mcp.bulk_approve(ids)`

11. **POST /api/validations/bulk/reject** (line 2456)
    - Currently: Direct `db_manager` updates
    - Should be: `mcp.bulk_reject(ids, reason=...)`

#### Enhancement Endpoints

12. **POST /api/enhance/batch** (line 2001)
    - Currently: Direct `EnhancementAgent` calls
    - Should be: `mcp.enhance_batch(ids, batch_size, threshold)`

13. **POST /api/enhance/{validation_id}** (line 2089)
    - Currently: Direct `EnhancementAgent` calls
    - Should be: `mcp.enhance([validation_id])`

14. **POST /api/enhance** (line 2203 and 3985)
    - Currently: Direct agent calls
    - Should be: `mcp.enhance(ids)` or `mcp.enhance_preview()`

15. **POST /api/enhance/auto-apply** (line 2928)
    - Currently: Direct agent calls
    - Should be: `mcp.enhance_auto_apply(validation_id, threshold, ...)`

16. **POST /api/validations/{validation_id}/mark_recommendations_applied** (line 2358)
    - Currently: Direct `db_manager` update
    - Should be: `mcp.mark_recommendations_applied(recommendation_ids)`

17. **POST /api/validations/bulk/enhance** (line 2509)
    - Currently: Direct agent calls
    - Should be: `mcp.enhance_batch(ids)`

#### Workflow Endpoints

18. **POST /workflows/validate-directory** (line 2972)
    - Currently: Background task with orchestrator
    - Should be: `mcp.create_workflow("validate_directory", params)`

19. **GET /workflows** (line 3025)
    - Currently: Direct `db_manager` access
    - Should be: Keep as-is (dashboard-specific)

20. **GET /workflows/{workflow_id}** (line 3041)
    - Currently: Direct `db_manager` access
    - Should be: `mcp.get_workflow(workflow_id)`

21. **POST /workflows/{workflow_id}/control** (line 3055)
    - Currently: Direct workflow state update
    - Should be: `mcp.control_workflow(workflow_id, action)`

22. **GET /workflows/{workflow_id}/report** (line 3088)
    - Currently: Custom report generation
    - Should be: `mcp.get_workflow_report(workflow_id)`

23. **GET /workflows/{workflow_id}/summary** (line 3100)
    - Currently: Custom summary generation
    - Should be: `mcp.get_workflow_summary(workflow_id)`

24. **DELETE /workflows/{workflow_id}** (line 3121)
    - Currently: Direct `db_manager` deletion
    - Should be: `mcp.delete_workflow(workflow_id)`

25. **GET /api/workflows** (line 3184)
    - Currently: Direct `db_manager` access
    - Should be: `mcp.list_workflows(...)`

26. **POST /api/workflows/bulk-delete** (line 3230)
    - Currently: Direct `db_manager` deletion
    - Should be: `mcp.bulk_delete_workflows(...)`

#### Stats & System Endpoints

27. **GET /api/stats** (line 1662)
    - Currently: Direct `db_manager` counts
    - Should be: `mcp.get_stats()`

28. **GET /health/detailed** (line 760)
    - Currently: Direct component checks
    - Should be: Consider adding `mcp.get_system_status()`

29. **GET /admin/status** (line 3275)
    - Currently: Direct system checks
    - Should be: `mcp.get_system_status()`

#### Recommendation Endpoints

30. **GET /api/recommendations** (line 2568)
    - Currently: Direct `db_manager` access
    - Should be: Keep as-is (returns all recommendations)

31. **GET /api/recommendations/{recommendation_id}** (line 2591)
    - Currently: Direct `db_manager` access
    - Should be: Keep as-is (single recommendation lookup)

32. **POST /api/recommendations/{recommendation_id}/review** (line 2605)
    - Currently: Direct `db_manager` update
    - Should be: `mcp.review_recommendation(recommendation_id, action, notes)`

33. **POST /api/recommendations/bulk-review** (line 2633)
    - Currently: Direct `db_manager` updates
    - Should be: `mcp.bulk_review_recommendations(ids, action, notes)`

34. **POST /api/recommendations/{validation_id}/generate** (line 2675, 4098)
    - Currently: Direct `RecommendationAgent` calls
    - Should be: `mcp.generate_recommendations(validation_id, threshold, types)`

35. **POST /api/recommendations/{validation_id}/rebuild** (line 2751, 4160)
    - Currently: Direct `db_manager` and agent calls
    - Should be: `mcp.rebuild_recommendations(validation_id, threshold)`

36. **GET /api/validations/{validation_id}/recommendations** (line 4189)
    - Currently: Direct `db_manager` query
    - Should be: `mcp.get_recommendations(validation_id, status, rec_type)`

37. **DELETE /api/validations/{validation_id}/recommendations/{recommendation_id}** (line 4229)
    - Currently: Direct `db_manager` deletion
    - Should be: `mcp.delete_recommendation(recommendation_id)`

#### Diff & Comparison Endpoints

38. **GET /api/validations/{validation_id}/diff** (line 1708)
    - Currently: Custom diff generation
    - Should be: Keep as-is or add to MCP server

39. **GET /api/validations/{validation_id}/enhancement-comparison** (line 1802)
    - Currently: Custom comparison logic
    - Should be: `mcp.get_enhancement_comparison(validation_id, format)`

#### Admin Endpoints

40. **GET /admin/cache/stats** (line 3355)
    - Currently: Direct cache manager access
    - Should be: `mcp.get_cache_stats()`

41. **POST /admin/cache/clear** (line 3322)
    - Currently: Direct cache manager call
    - Should be: `mcp.clear_cache(cache_types)`

42. **POST /admin/cache/cleanup** (line 3365)
    - Currently: Direct cache manager call
    - Should be: `mcp.cleanup_cache(max_age_hours)`

43. **POST /admin/cache/rebuild** (line 3382)
    - Currently: Direct cache manager call
    - Should be: `mcp.rebuild_cache()`

44. **POST /admin/agents/reload/{agent_id}** (line 3494)
    - Currently: Direct agent registry manipulation
    - Should be: `mcp.reload_agent(agent_id)`

45. **POST /admin/system/gc** (line 3528)
    - Currently: Direct `gc.collect()`
    - Should be: `mcp.run_gc()`

46. **POST /admin/maintenance/enable** (line 3542)
    - Currently: Global flag modification
    - Should be: `mcp.enable_maintenance_mode(reason, enabled_by)`

47. **POST /admin/maintenance/disable** (line 3560)
    - Currently: Global flag modification
    - Should be: `mcp.disable_maintenance_mode()`

48. **POST /admin/system/checkpoint** (line 3578)
    - Currently: Direct database backup
    - Should be: `mcp.create_checkpoint(name, metadata)`

#### Export Endpoints

49. **GET /api/export/validation/{validation_id}** (line 4852)
    - Currently: Direct `db_manager` and JSON generation
    - Should be: `mcp.export_validation(validation_id, include_recommendations)`

50. **GET /api/export/recommendations** (line 4966)
    - Currently: Direct `db_manager` and JSON generation
    - Should be: `mcp.export_recommendations(validation_id)`

51. **GET /api/export/workflow/{workflow_id}** (line 5052)
    - Currently: Direct `db_manager` and JSON generation
    - Should be: `mcp.export_workflow(workflow_id, include_validations)`

#### Audit & Performance Endpoints

52. **GET /api/audit** (line 3758)
    - Currently: Direct database query
    - Should be: `mcp.get_audit_log(...)`

53. **GET /admin/reports/performance** (line 3420)
    - Currently: Custom performance metrics
    - Should be: `mcp.get_performance_report(time_range, operation)`

54. **GET /admin/reports/health** (line 3479)
    - Currently: Custom health checks
    - Should be: `mcp.get_health_report()`

#### Validator Endpoints

55. **GET /api/validators/available** (line 1614)
    - Currently: Direct agent registry access
    - Should be: `mcp.get_available_validators(validator_type)`

## Migration Pattern

### Before (Direct Agent Access)

```python
@app.post("/api/validations/{validation_id}/approve")
async def approve_validation(validation_id: str):
    """Approve a validation result."""
    try:
        validation = db_manager.get_validation_result(validation_id)
        if not validation:
            raise HTTPException(status_code=404, detail="Validation not found")

        # Update status
        validation.status = "approved"
        db_manager.session.commit()

        return {"success": True, "validation_id": validation_id}
    except Exception as e:
        logger.exception("Failed to approve validation")
        raise HTTPException(status_code=500, detail=str(e))
```

### After (MCP Client Access)

```python
from fastapi import Depends
from api.mcp_helpers import get_api_mcp_client, format_mcp_response
from svc.mcp_client import MCPAsyncClient

@app.post("/api/validations/{validation_id}/approve")
async def approve_validation(
    validation_id: str,
    mcp: MCPAsyncClient = Depends(get_api_mcp_client)
):
    """Approve a validation result via MCP."""
    result = await mcp.approve([validation_id])
    return format_mcp_response(result)
```

## Benefits of Migration

1. **Consistent Interface**: All operations go through MCP protocol
2. **Better Error Handling**: MCP exceptions are automatically converted to HTTP errors
3. **Logging & Auditing**: MCP layer provides centralized logging
4. **Testing**: Easier to mock MCP client than entire agent registry
5. **Future-Proof**: Ready for remote MCP servers if needed
6. **Retry Logic**: Built-in retry and timeout handling in MCP client

## Challenges & Considerations

### 1. Complex File Handling

Some endpoints (e.g., `/api/validate`) have complex file handling logic:
- Temporary file creation
- File path normalization
- Content preservation

**Recommendation**: Keep file handling in endpoint, pass normalized paths to MCP.

### 2. Background Tasks

Workflow endpoints use FastAPI background tasks:
```python
background_tasks.add_task(process_workflow, ...)
```

**Recommendation**: Replace with MCP workflow creation:
```python
result = await mcp.create_workflow("validate_directory", params)
```

### 3. Database Direct Access

Some endpoints read from database for dashboard purposes (e.g., listing workflows):

**Recommendation**: Keep dashboard-specific endpoints as-is, migrate API endpoints to MCP.

### 4. LiveBus Integration

Some endpoints publish to LiveBus for WebSocket updates:

**Recommendation**: Keep LiveBus publishing in endpoints until MCP server handles it internally.

### 5. Custom Response Formatting

Some endpoints have custom response structures that differ from MCP:

**Recommendation**: Use `format_mcp_response()` with metadata to preserve custom fields.

## Implementation Priority

### High Priority (Core API)

1. ✅ Exception handlers (COMPLETE)
2. Validation endpoints (POST /api/validate, GET /api/validations/*)
3. Approval endpoints (POST /api/validations/{id}/approve, /reject)
4. Enhancement endpoints (POST /api/enhance/*)
5. Workflow endpoints (POST /workflows/*, GET /api/workflows)
6. Stats endpoint (GET /api/stats)
7. System status (GET /api/system/status)

### Medium Priority (Admin & Management)

8. Recommendation endpoints (GET/POST /api/recommendations/*)
9. Admin cache endpoints (POST /admin/cache/*)
10. Admin system endpoints (POST /admin/system/*)
11. Export endpoints (GET /api/export/*)

### Low Priority (Dashboard-Specific)

12. Dashboard endpoints (keep as-is for now)
13. Internal agent endpoints (keep as-is)
14. Development/test endpoints

## Testing Strategy

1. **Unit Tests**: Test MCP client methods individually
2. **Integration Tests**: Test FastAPI endpoints with MCP client
3. **E2E Tests**: Test full workflows through API
4. **Backward Compatibility**: Ensure responses match current format
5. **Performance**: Verify MCP layer doesn't add significant latency

## Next Steps

1. Start with highest priority endpoints (validation, approval, enhancement)
2. Migrate 5-10 endpoints at a time
3. Test thoroughly after each migration batch
4. Update API documentation to reflect MCP architecture
5. Add MCP-specific error handling and logging
6. Consider adding MCP metrics/monitoring

## Files Modified

- ✅ `api/mcp_helpers.py` - Created helper functions
- ✅ `api/server.py` - Added MCP exception handlers
- ✅ `svc/mcp_client.py` - Added recommendation methods to MCPAsyncClient
- ⏳ `api/server.py` - Migrate 55+ endpoints (IN PROGRESS)

## Estimated Effort

- **High Priority Endpoints**: 8-12 hours
- **Medium Priority Endpoints**: 4-6 hours
- **Testing & Validation**: 4-6 hours
- **Documentation Updates**: 2-3 hours

**Total**: 18-27 hours

## Conclusion

The MCP exception handlers are registered and the helper functions are in place. The next step is to systematically migrate each endpoint category, starting with the most critical validation and enhancement endpoints.

The migration pattern is straightforward, but careful attention must be paid to:
- File handling logic
- Response format compatibility
- Background task conversion
- LiveBus integration
- Error handling edge cases

Given the large number of endpoints (55+), this migration should be done incrementally with thorough testing after each batch.
