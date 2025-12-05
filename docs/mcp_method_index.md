# MCP Method Index

Complete index of all 52 MCP (Model Context Protocol) methods available in TBCV.

## Methods by Category

### Validation Methods (8 methods)

Core content validation operations.

| Method | Description | Creates Record |
|--------|-------------|----------------|
| `validate_folder` | Validate all files in folder | Yes (one per file) |
| `validate_file` | Validate single file | Yes |
| `validate_content` | Validate content string without file | Yes |
| `get_validation` | Retrieve validation by ID | No |
| `list_validations` | List validations with filtering/pagination | No |
| `update_validation` | Update validation metadata (notes, status) | No |
| `delete_validation` | Delete validation record | No |
| `revalidate` | Re-run validation on same file | Yes (new record) |

### Approval Methods (4 methods)

Approve or reject validation records.

| Method | Description | Supports Bulk |
|--------|-------------|---------------|
| `approve` | Approve validation(s) | Single or multiple |
| `reject` | Reject validation(s) with optional reason | Single or multiple |
| `bulk_approve` | Efficiently approve large batches | Yes (optimized) |
| `bulk_reject` | Efficiently reject large batches | Yes (optimized) |

### Enhancement Methods (5 methods)

Apply LLM-powered enhancements to approved content.

| Method | Description | Requires Ollama |
|--------|-------------|-----------------|
| `enhance` | Enhance approved validations | Yes |
| `enhance_batch` | Enhance multiple validations with progress | Yes |
| `enhance_preview` | Preview enhancement without applying (dry-run) | Yes |
| `enhance_auto_apply` | Auto-apply high-confidence recommendations | Yes |
| `get_enhancement_comparison` | Get before/after comparison with diff | No |

### Recommendation Methods (8 methods)

Complete recommendation lifecycle management.

| Method | Description | Use Case |
|--------|-------------|----------|
| `generate_recommendations` | Generate recommendations for validation | Initial recommendation creation |
| `rebuild_recommendations` | Rebuild after rules/validation changes | After rule updates |
| `get_recommendations` | Retrieve recommendations with filtering | Viewing recommendations |
| `review_recommendation` | Review (approve/reject) single recommendation | Manual review |
| `bulk_review_recommendations` | Review multiple recommendations | Batch review |
| `apply_recommendations` | Apply approved recommendations to files | File modification |
| `delete_recommendation` | Delete recommendation record | Cleanup |
| `mark_recommendations_applied` | Mark as applied without modifying files | Manual application tracking |

### Admin Methods (11 methods)

System administration and maintenance operations.

| Method | Description | Requires Restart |
|--------|-------------|------------------|
| `get_system_status` | Get comprehensive system health status | No |
| `clear_cache` | Clear all or specific cache types | No |
| `get_cache_stats` | Get cache statistics and hit rates | No |
| `cleanup_cache` | Clean up stale cache entries | No |
| `rebuild_cache` | Rebuild cache from scratch | No |
| `reload_agent` | Reload specific agent | No |
| `run_gc` | Run Python garbage collection | No |
| `enable_maintenance_mode` | Enable maintenance mode | No |
| `disable_maintenance_mode` | Disable maintenance mode | No |
| `create_checkpoint` | Create system checkpoint for backup | No |
| `get_admin_logs` | Get admin operation logs | No |

### Workflow Methods (8 methods)

Workflow orchestration and background operation control.

| Method | Description | Async Support |
|--------|-------------|---------------|
| `create_workflow` | Create and start new workflow | Yes (background) |
| `get_workflow` | Retrieve workflow details by ID | No |
| `list_workflows` | List workflows with filtering | No |
| `control_workflow` | Pause/resume/cancel workflows | Yes (async control) |
| `get_workflow_report` | Generate detailed workflow report | No |
| `get_workflow_summary` | Get workflow summary for dashboards | No |
| `delete_workflow` | Delete workflow record | No |
| `bulk_delete_workflows` | Delete multiple workflows with filtering | No |

### Query Methods (9 methods)

Statistics, analytics, and export operations.

| Method | Description | Export Format |
|--------|-------------|---------------|
| `get_stats` | Get comprehensive system statistics | JSON |
| `get_audit_log` | Get audit log with filtering | JSON |
| `get_performance_report` | Get performance metrics | JSON |
| `get_health_report` | Get detailed health report with recommendations | JSON |
| `get_validation_history` | Get validation history for specific file | JSON |
| `get_available_validators` | List available validators | JSON |
| `export_validation` | Export validation to JSON | JSON |
| `export_recommendations` | Export recommendations to JSON | JSON |
| `export_workflow` | Export workflow report to JSON | JSON |

## Complete Method List (Alphabetical)

All 52 methods sorted alphabetically for quick reference.

1. `apply_recommendations` - Apply approved recommendations to files
2. `approve` - Approve validation(s)
3. `bulk_approve` - Bulk approve validations efficiently
4. `bulk_delete_workflows` - Delete multiple workflows with filtering
5. `bulk_reject` - Bulk reject validations efficiently
6. `bulk_review_recommendations` - Review multiple recommendations
7. `cleanup_cache` - Clean up stale cache entries
8. `clear_cache` - Clear all or specific cache types
9. `control_workflow` - Pause/resume/cancel workflows
10. `create_checkpoint` - Create system checkpoint for backup
11. `create_workflow` - Create and start new workflow
12. `delete_recommendation` - Delete recommendation record
13. `delete_validation` - Delete validation record
14. `delete_workflow` - Delete workflow record
15. `disable_maintenance_mode` - Disable maintenance mode
16. `enable_maintenance_mode` - Enable maintenance mode
17. `enhance` - Enhance approved validations
18. `enhance_auto_apply` - Auto-apply high-confidence recommendations
19. `enhance_batch` - Enhance multiple validations with progress
20. `enhance_preview` - Preview enhancement without applying
21. `export_recommendations` - Export recommendations to JSON
22. `export_validation` - Export validation to JSON
23. `export_workflow` - Export workflow report to JSON
24. `generate_recommendations` - Generate recommendations for validation
25. `get_audit_log` - Get audit log with filtering
26. `get_available_validators` - List available validators
27. `get_cache_stats` - Get cache statistics
28. `get_enhancement_comparison` - Get before/after comparison
29. `get_health_report` - Get detailed health report
30. `get_performance_report` - Get performance metrics
31. `get_recommendations` - Retrieve recommendations with filtering
32. `get_stats` - Get comprehensive system statistics
33. `get_system_status` - Get system health status
34. `get_validation` - Retrieve validation by ID
35. `get_validation_history` - Get validation history for file
36. `get_workflow` - Retrieve workflow by ID
37. `get_workflow_report` - Generate detailed workflow report
38. `get_workflow_summary` - Get workflow summary for dashboards
39. `list_validations` - List validations with filtering
40. `list_workflows` - List workflows with filtering
41. `mark_recommendations_applied` - Mark recommendations as applied
42. `rebuild_cache` - Rebuild cache from scratch
43. `rebuild_recommendations` - Rebuild recommendations after changes
44. `reject` - Reject validation(s)
45. `reload_agent` - Reload specific agent
46. `revalidate` - Re-run validation on same file
47. `review_recommendation` - Review (approve/reject) recommendation
48. `run_gc` - Run garbage collection
49. `update_validation` - Update validation metadata
50. `validate_content` - Validate content string without file
51. `validate_file` - Validate single file
52. `validate_folder` - Validate all files in folder

## Method Categories Summary

| Category | Count | Primary Use Case |
|----------|-------|------------------|
| Validation | 8 | Content validation and record management |
| Approval | 4 | Validation approval/rejection workflow |
| Enhancement | 5 | LLM-powered content improvement |
| Recommendation | 8 | Recommendation lifecycle from generation to application |
| Admin | 11 | System administration and maintenance |
| Workflow | 8 | Background operation orchestration |
| Query | 9 | Analytics, statistics, and data export |
| **Total** | **52** | Complete MCP interface |

## Usage Patterns

### Typical Workflow Pattern

```
1. validate_folder/validate_file → Create validation records
2. list_validations → Review validation results
3. approve/reject → Mark validations for enhancement
4. generate_recommendations → Create improvement recommendations
5. review_recommendation → Approve/reject recommendations
6. apply_recommendations → Apply approved changes to files
```

### Bulk Operations Pattern

```
1. validate_folder → Validate many files
2. bulk_approve → Approve passing validations efficiently
3. bulk_review_recommendations → Review recommendations in batch
4. apply_recommendations → Apply all approved recommendations
```

## Usage Examples

### Validation Methods

```python
import asyncio
from svc.mcp_server import MCPServer

async def validate_single_file():
    """Example: validate_file method."""
    server = MCPServer()

    result = await server.process_request(
        method='validate_file',
        params={
            'file_path': 'docs/tutorial.md',
            'content': '# Tutorial\n\nContent here',
            'family': 'words',
            'validation_types': ['yaml', 'markdown', 'truth']
        }
    )

    print(f"Validation ID: {result['validation_id']}")
    print(f"Issues: {len(result['issues'])}")
    return result

async def validate_folder():
    """Example: validate_folder method for batch processing."""
    server = MCPServer()

    result = await server.process_request(
        method='validate_folder',
        params={
            'directory_path': './docs',
            'file_pattern': '*.md',
            'family': 'words',
            'max_workers': 4,
            'recursive': True
        }
    )

    print(f"Validated {result['total_files']} files")
    print(f"Passed: {result['pass_count']}, Failed: {result['fail_count']}")
    return result

# Run
result = asyncio.run(validate_single_file())
```

### Approval Methods

```python
import asyncio
from svc.mcp_server import MCPServer

async def approve_validations():
    """Example: approve method."""
    server = MCPServer()

    # Approve single validation
    result = await server.process_request(
        method='approve',
        params={
            'validation_ids': ['val-123'],
            'notes': 'Approved for enhancement'
        }
    )

    print(f"Approved: {result['approved_count']}")

async def bulk_approve():
    """Example: bulk_approve method for efficiency."""
    server = MCPServer()

    result = await server.process_request(
        method='bulk_approve',
        params={
            'validation_ids': ['val-123', 'val-456', 'val-789'],
            'notes': 'Bulk approval for release'
        }
    )

    print(f"Efficiently approved {result['approved_count']} validations")
    return result

# Run
result = asyncio.run(bulk_approve())
```

### Recommendation Methods

```python
import asyncio
from svc.mcp_server import MCPServer

async def generate_recommendations():
    """Example: generate_recommendations method."""
    server = MCPServer()

    result = await server.process_request(
        method='generate_recommendations',
        params={
            'validation_id': 'val-123',
            'regenerate': False
        }
    )

    print(f"Generated {result['recommendations_count']} recommendations")
    return result

async def review_recommendations():
    """Example: review_recommendation method."""
    server = MCPServer()

    result = await server.process_request(
        method='review_recommendation',
        params={
            'recommendation_id': 'rec-456',
            'status': 'approved',
            'reviewer': 'admin@example.com',
            'notes': 'Looks good'
        }
    )

    print(f"Recommendation status: {result['status']}")
    return result

async def bulk_review():
    """Example: bulk_review_recommendations method."""
    server = MCPServer()

    result = await server.process_request(
        method='bulk_review_recommendations',
        params={
            'recommendation_ids': ['rec-123', 'rec-456', 'rec-789'],
            'action': 'accepted',
            'reviewer': 'admin@example.com'
        }
    )

    print(f"Reviewed {result['processed']} recommendations")
    return result

# Run
result = asyncio.run(bulk_review())
```

### Enhancement Methods

```python
import asyncio
from svc.mcp_server import MCPServer

async def enhance_content():
    """Example: enhance method."""
    server = MCPServer()

    result = await server.process_request(
        method='enhance',
        params={
            'validation_id': 'val-123',
            'content': '# Tutorial\n\nContent here',
            'file_path': 'tutorial.md'
        }
    )

    print(f"Applied {result['applied_count']} enhancements")
    print(f"Enhanced content length: {len(result['enhanced_content'])} chars")
    return result

async def preview_enhancement():
    """Example: enhance_preview method (dry-run)."""
    server = MCPServer()

    result = await server.process_request(
        method='enhance_preview',
        params={
            'validation_id': 'val-123',
            'content': '# Tutorial\n\nContent here',
            'file_path': 'tutorial.md'
        }
    )

    print(f"Would apply {result['applied_count']} changes")
    print(f"Diff:\n{result['diff']}")
    return result

async def auto_apply_recommendations():
    """Example: enhance_auto_apply method."""
    server = MCPServer()

    result = await server.process_request(
        method='enhance_auto_apply',
        params={
            'validation_id': 'val-123',
            'content': '# Tutorial\n\nContent here',
            'confidence_threshold': 0.9,
            'max_recommendations': 10
        }
    )

    print(f"Auto-applied {result['applied_count']} high-confidence changes")
    return result

# Run
result = asyncio.run(enhance_content())
```

### Admin Methods

```python
import asyncio
from svc.mcp_server import MCPServer

async def get_system_status():
    """Example: get_system_status method."""
    server = MCPServer()

    result = await server.process_request(
        method='get_system_status',
        params={}
    )

    print(f"Status: {result['status']}")
    print(f"Agents: {result['agents_registered']}")
    print(f"Database: {'connected' if result['database_connected'] else 'disconnected'}")
    return result

async def clear_cache():
    """Example: clear_cache method."""
    server = MCPServer()

    result = await server.process_request(
        method='clear_cache',
        params={
            'cache_level': 'all'  # or 'l1', 'l2'
        }
    )

    print(f"Cache cleared: {result['cleared_entries']} entries")
    return result

async def get_cache_stats():
    """Example: get_cache_stats method."""
    server = MCPServer()

    result = await server.process_request(
        method='get_cache_stats',
        params={}
    )

    print(f"L1 hit rate: {result['l1_hit_rate']:.2%}")
    print(f"L2 hit rate: {result['l2_hit_rate']:.2%}")
    return result

# Run
result = asyncio.run(get_system_status())
```

### Query Methods

```python
import asyncio
from svc.mcp_server import MCPServer

async def get_statistics():
    """Example: get_stats method."""
    server = MCPServer()

    result = await server.process_request(
        method='get_stats',
        params={
            'days': 7  # Last 7 days
        }
    )

    print(f"Total validations: {result['total_validations']}")
    print(f"Passed: {result['pass_count']}")
    print(f"Failed: {result['fail_count']}")
    return result

async def get_validation_history():
    """Example: get_validation_history method."""
    server = MCPServer()

    result = await server.process_request(
        method='get_validation_history',
        params={
            'file_path': 'docs/tutorial.md'
        }
    )

    print(f"Found {len(result['history'])} validations for file")
    for val in result['history']:
        print(f"  - {val['created_at']}: {val['status']}")
    return result

async def export_validation():
    """Example: export_validation method."""
    server = MCPServer()

    result = await server.process_request(
        method='export_validation',
        params={
            'validation_id': 'val-123',
            'format': 'json'  # or 'yaml', 'csv'
        }
    )

    print(f"Exported validation: {len(result['content'])} bytes")
    return result

# Run
result = asyncio.run(get_statistics())
```

### Workflow Methods

```python
import asyncio
from svc.mcp_server import MCPServer

async def create_workflow():
    """Example: create_workflow method."""
    server = MCPServer()

    result = await server.process_request(
        method='create_workflow',
        params={
            'type': 'validate_directory',
            'input_params': {
                'directory_path': './docs',
                'file_pattern': '*.md'
            }
        }
    )

    print(f"Workflow created: {result['workflow_id']}")
    return result

async def get_workflow():
    """Example: get_workflow method."""
    server = MCPServer()

    result = await server.process_request(
        method='get_workflow',
        params={
            'workflow_id': 'wf-123'
        }
    )

    print(f"Workflow: {result['type']}")
    print(f"State: {result['state']}")
    print(f"Progress: {result['progress_percent']}%")
    return result

async def control_workflow():
    """Example: control_workflow method."""
    server = MCPServer()

    # Pause workflow
    result = await server.process_request(
        method='control_workflow',
        params={
            'workflow_id': 'wf-123',
            'action': 'pause'  # or 'resume', 'cancel'
        }
    )

    print(f"Workflow state: {result['state']}")
    return result

# Run
result = asyncio.run(create_workflow())
```

### Monitoring Pattern

```
1. get_system_status → Check system health
2. get_stats → View system statistics
3. get_performance_report → Analyze performance metrics
4. get_audit_log → Review system operations
5. get_health_report → Get health recommendations
```

## Related Documentation

- **[MCP Integration](./mcp_integration.md)** - Complete MCP documentation with examples
- **[Architecture](./architecture.md)** - System architecture including MCP layer
- **[API Reference](./api_reference.md)** - REST API documentation

## Method Implementation

All methods are implemented in:
- `svc/mcp_server.py` - Main MCP server and method registry
- `svc/mcp_methods/` - Method implementations organized by category:
  - `validation_methods.py` - Validation operations
  - `approval_methods.py` - Approval/rejection operations
  - `enhancement_methods.py` - Enhancement operations
  - `recommendation_methods.py` - Recommendation lifecycle
  - `admin_methods.py` - Administration operations
  - `workflow_methods.py` - Workflow management
  - `query_methods.py` - Query and analytics operations

## Testing

All MCP methods are tested in:
- `tests/svc/test_mcp_comprehensive.py` - Comprehensive method tests (46 tests)
- `tests/svc/test_mcp_client.py` - Client functionality tests
- `tests/integration/test_mcp_end_to_end.py` - End-to-end integration tests

Run tests:
```bash
pytest tests/svc/test_mcp_comprehensive.py -v
```
