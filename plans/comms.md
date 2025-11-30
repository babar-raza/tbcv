# MCP-First Architecture Migration Plan

**Date**: 2025-11-30
**Status**: Planning
**Objective**: Achieve 100% MCP coverage for all UI and CLI operations
**Current Coverage**: 7.1% (4/56 methods)
**Target Coverage**: 100% (56/56 methods)

---

## Executive Summary

This plan systematically migrates TBCV from a mixed-access architecture to a **MCP-first architecture** where all operations flow through the Model Context Protocol (MCP) server. This ensures consistency, maintainability, and a single source of truth for all business logic.

### Current State
- **4 MCP methods** implemented (validate_folder, approve, reject, enhance)
- **52 methods missing** across 7 operation categories
- **CLI**: 100% direct access (0% MCP coverage)
- **API**: ~96% direct access (~4% MCP coverage)
- **Risk**: Inconsistent behavior, duplicate logic, maintenance burden

### Target State
- **56 MCP methods** implemented (100% coverage)
- **CLI**: 100% MCP coverage (all 30+ commands)
- **API**: 100% MCP coverage (all 80+ endpoints)
- **Result**: Single source of truth, consistent behavior, maintainable codebase

---

## Scope & Constraints

### In Scope
- Expand MCP server with 52 new methods across 7 categories
- Create sync/async MCP client wrappers
- Refactor all CLI commands to use MCP
- Refactor all API endpoints to use MCP
- Implement runtime access guards to enforce MCP-only access
- Update all documentation
- Create comprehensive test coverage

### Out of Scope
- Network-based MCP communication (in-process only)
- Authentication/authorization (future enhancement)
- Rate limiting (future enhancement)
- GraphQL/gRPC interfaces (future enhancement)
- Database migration from SQLite (future enhancement)

### Constraints
- **Zero breaking changes** to public APIs during migration
- **Zero network calls** in unit tests
- **Zero mock data** in production paths
- **No new dependencies** without approval
- **Backward compatibility** maintained during transition
- **Performance overhead** must be <5ms per operation

---

## Gap Analysis

### Category 1: Validation Operations (8 gaps)

| Method | Description | Priority | Current Status |
|--------|-------------|----------|----------------|
| ✅ validate_folder | Validate markdown files in folder | P0 | **Implemented** |
| ❌ validate_file | Validate single file | P0 | **Missing** |
| ❌ validate_content | Validate content string | P0 | **Missing** |
| ❌ get_validation | Get validation by ID | P0 | **Missing** |
| ❌ list_validations | List validations with filters | P0 | **Missing** |
| ❌ update_validation | Update validation metadata | P1 | **Missing** |
| ❌ delete_validation | Delete validation record | P1 | **Missing** |
| ❌ revalidate | Re-run validation | P1 | **Missing** |

**Impact**: CLI and API cannot perform basic validation operations through MCP

### Category 2: Approval Operations (4 gaps)

| Method | Description | Priority | Current Status |
|--------|-------------|----------|----------------|
| ✅ approve | Approve validation(s) | P0 | **Implemented** |
| ✅ reject | Reject validation(s) | P0 | **Implemented** |
| ❌ bulk_approve | Approve multiple validations | P0 | **Missing** |
| ❌ bulk_reject | Reject multiple validations | P0 | **Missing** |

**Impact**: Bulk operations not available, inefficient for large batches

### Category 3: Enhancement Operations (5 gaps)

| Method | Description | Priority | Current Status |
|--------|-------------|----------|----------------|
| ✅ enhance | Enhance approved validation(s) | P0 | **Implemented** |
| ❌ enhance_batch | Enhance multiple with progress | P0 | **Missing** |
| ❌ enhance_preview | Preview enhancement without applying | P1 | **Missing** |
| ❌ enhance_auto_apply | Auto-apply recommendations | P1 | **Missing** |
| ❌ get_enhancement_comparison | Get before/after comparison | P1 | **Missing** |

**Impact**: Advanced enhancement features unavailable through MCP

### Category 4: Recommendation Operations (8 gaps)

| Method | Description | Priority | Current Status |
|--------|-------------|----------|----------------|
| ❌ generate_recommendations | Generate recommendations for validation | P0 | **Missing** |
| ❌ rebuild_recommendations | Rebuild recommendations | P0 | **Missing** |
| ❌ get_recommendations | Get recommendations for validation | P0 | **Missing** |
| ❌ review_recommendation | Review (approve/reject) recommendation | P0 | **Missing** |
| ❌ bulk_review_recommendations | Bulk review recommendations | P1 | **Missing** |
| ❌ apply_recommendations | Apply recommendations to content | P0 | **Missing** |
| ❌ delete_recommendation | Delete recommendation | P1 | **Missing** |
| ❌ mark_recommendations_applied | Mark recommendations as applied | P1 | **Missing** |

**Impact**: No recommendation workflow available through MCP

### Category 5: Workflow Operations (8 gaps)

| Method | Description | Priority | Current Status |
|--------|-------------|----------|----------------|
| ❌ create_workflow | Create new workflow | P0 | **Missing** |
| ❌ get_workflow | Get workflow by ID | P0 | **Missing** |
| ❌ list_workflows | List workflows with filters | P0 | **Missing** |
| ❌ control_workflow | Control (pause/resume/cancel) workflow | P0 | **Missing** |
| ❌ get_workflow_report | Get workflow report | P1 | **Missing** |
| ❌ get_workflow_summary | Get workflow summary | P1 | **Missing** |
| ❌ delete_workflow | Delete workflow | P1 | **Missing** |
| ❌ bulk_delete_workflows | Bulk delete workflows | P1 | **Missing** |

**Impact**: No workflow management available through MCP

### Category 6: Admin/Maintenance Operations (10 gaps)

| Method | Description | Priority | Current Status |
|--------|-------------|----------|----------------|
| ❌ get_system_status | Get system health status | P0 | **Missing** |
| ❌ clear_cache | Clear all caches | P1 | **Missing** |
| ❌ get_cache_stats | Get cache statistics | P1 | **Missing** |
| ❌ cleanup_cache | Clean up stale cache entries | P1 | **Missing** |
| ❌ rebuild_cache | Rebuild cache from scratch | P1 | **Missing** |
| ❌ reload_agent | Reload specific agent | P2 | **Missing** |
| ❌ run_gc | Run garbage collection | P2 | **Missing** |
| ❌ enable_maintenance_mode | Enable maintenance mode | P2 | **Missing** |
| ❌ disable_maintenance_mode | Disable maintenance mode | P2 | **Missing** |
| ❌ create_checkpoint | Create system checkpoint | P2 | **Missing** |

**Impact**: No admin/maintenance operations available through MCP

### Category 7: Query/Stats/Export Operations (9 gaps)

| Method | Description | Priority | Current Status |
|--------|-------------|----------|----------------|
| ❌ get_stats | Get system statistics | P0 | **Missing** |
| ❌ get_audit_log | Get audit log entries | P1 | **Missing** |
| ❌ get_performance_report | Get performance metrics | P1 | **Missing** |
| ❌ get_health_report | Get detailed health report | P0 | **Missing** |
| ❌ get_validation_history | Get validation history for file | P1 | **Missing** |
| ❌ get_available_validators | Get list of available validators | P1 | **Missing** |
| ❌ export_validation | Export validation to JSON | P1 | **Missing** |
| ❌ export_recommendations | Export recommendations to JSON | P1 | **Missing** |
| ❌ export_workflow | Export workflow report | P1 | **Missing** |

**Impact**: No query/reporting operations available through MCP

---

## Task Breakdown

### Total Tasks: 18 task cards

| Phase | Tasks | Estimated Effort | Priority |
|-------|-------|------------------|----------|
| Phase 1: Foundation | 3 tasks | 2 weeks | P0 |
| Phase 2: Core Operations | 7 tasks | 3 weeks | P0 |
| Phase 3: Advanced Operations | 4 tasks | 2 weeks | P1 |
| Phase 4: Integration | 2 tasks | 1 week | P0 |
| Phase 5: Enforcement & Testing | 2 tasks | 1 week | P0 |
| **TOTAL** | **18 tasks** | **9 weeks** | - |

---

## Phase 1: Foundation (2 weeks)

### TASK-001: MCP Server Architecture & Base Infrastructure
**Priority**: P0
**Effort**: 3 days
**Dependencies**: None

### TASK-002: MCP Client Wrappers (Sync & Async)
**Priority**: P0
**Effort**: 2 days
**Dependencies**: TASK-001

### TASK-003: Testing Infrastructure for MCP
**Priority**: P0
**Effort**: 3 days
**Dependencies**: TASK-001, TASK-002

---

## Phase 2: Core Operations (3 weeks)

### TASK-004: Validation Methods (8 methods)
**Priority**: P0
**Effort**: 4 days
**Dependencies**: TASK-001

### TASK-005: Approval Methods (2 bulk methods)
**Priority**: P0
**Effort**: 1 day
**Dependencies**: TASK-001

### TASK-006: Enhancement Methods (4 methods)
**Priority**: P0
**Effort**: 3 days
**Dependencies**: TASK-001

### TASK-007: Recommendation Methods (8 methods)
**Priority**: P0
**Effort**: 5 days
**Dependencies**: TASK-001

### TASK-008: Workflow Methods (8 methods)
**Priority**: P0
**Effort**: 4 days
**Dependencies**: TASK-001

### TASK-009: Query/Stats Methods (6 methods)
**Priority**: P0
**Effort**: 2 days
**Dependencies**: TASK-001

### TASK-010: Admin/Maintenance Methods (10 methods)
**Priority**: P1
**Effort**: 3 days
**Dependencies**: TASK-001

---

## Phase 3: Advanced Operations (2 weeks)

### TASK-011: Export Methods (3 methods)
**Priority**: P1
**Effort**: 2 days
**Dependencies**: TASK-001

### TASK-012: Batch Operation Optimization
**Priority**: P1
**Effort**: 3 days
**Dependencies**: TASK-004, TASK-005, TASK-006

### TASK-013: Error Handling & Retry Logic
**Priority**: P0
**Effort**: 2 days
**Dependencies**: TASK-002

### TASK-014: Performance Monitoring & Metrics
**Priority**: P1
**Effort**: 3 days
**Dependencies**: TASK-001, TASK-002

---

## Phase 4: Integration (1 week)

### TASK-015: CLI Integration (Refactor all commands)
**Priority**: P0
**Effort**: 3 days
**Dependencies**: All Phase 2 tasks

### TASK-016: API Integration (Refactor all endpoints)
**Priority**: P0
**Effort**: 4 days
**Dependencies**: All Phase 2 tasks

---

## Phase 5: Enforcement & Testing (1 week)

### TASK-017: Access Guards & MCP-Only Enforcement
**Priority**: P0
**Effort**: 2 days
**Dependencies**: TASK-015, TASK-016

### TASK-018: Comprehensive Integration Testing & Validation
**Priority**: P0
**Effort**: 3 days
**Dependencies**: All tasks

---

## Success Criteria

### Coverage Metrics
- [ ] 56/56 MCP methods implemented (100%)
- [ ] 30+ CLI commands using MCP (100%)
- [ ] 80+ API endpoints using MCP (100%)
- [ ] 0 direct database imports in CLI
- [ ] 0 direct database imports in API
- [ ] 0 direct agent imports in CLI (except tests)
- [ ] 0 direct agent imports in API (except tests)

### Quality Metrics
- [ ] Test coverage >90% for all MCP methods
- [ ] MCP operation latency overhead <5ms (P95)
- [ ] Zero direct access violations detected
- [ ] All documentation updated
- [ ] All tests passing (unit + integration + e2e)
- [ ] No regression in existing functionality

### Operational Metrics
- [ ] CLI commands work identically via MCP
- [ ] API endpoints work identically via MCP
- [ ] Error messages preserved and enhanced
- [ ] Performance maintained or improved
- [ ] Backward compatibility maintained

---

## Risk Management

### Risk 1: Performance Degradation
**Probability**: Medium
**Impact**: High
**Mitigation**:
- Benchmark before/after for all operations
- Use in-process MCP client (no network overhead)
- Implement connection pooling where needed
- Add performance tests to CI/CD
- Set SLA for <5ms overhead per operation

### Risk 2: Breaking Changes
**Probability**: Medium
**Impact**: High
**Mitigation**:
- Maintain backward compatibility layer during transition
- Feature flags for gradual rollout
- Comprehensive regression testing
- Rollback plan for each phase
- User communication plan

### Risk 3: Incomplete Migration
**Probability**: Low
**Impact**: High
**Mitigation**:
- Task tracking with clear acceptance criteria
- Automated checks for direct access
- Code review checklist
- Runtime guards to detect violations
- Incremental delivery with validation gates

### Risk 4: Test Coverage Gaps
**Probability**: Medium
**Impact**: Medium
**Mitigation**:
- Mandate >90% coverage for new code
- Both unit and integration tests required
- Manual testing checklist per task
- Automated regression suite
- Test review in PR process

### Risk 5: Documentation Drift
**Probability**: High
**Impact**: Medium
**Mitigation**:
- Documentation update in every task card
- Documentation review in PR checklist
- Automated doc generation where possible
- Examples and runbooks for each feature
- Regular documentation audits

---

## Rollback Plan

Each task must have a clear rollback strategy:

1. **Feature Flags**: All new MCP paths behind feature flags
2. **Fallback Logic**: Keep old paths available during transition
3. **Database Compatibility**: No breaking schema changes
4. **Version Control**: Tag each phase completion
5. **Monitoring**: Alert on MCP error rates
6. **Quick Revert**: Documented revert commands per phase

---

## Communication Plan

### Stakeholders
- Development team
- QA team
- Operations team
- End users (CLI/API consumers)

### Updates
- **Weekly**: Progress update in standup
- **Per Phase**: Phase completion report
- **Blockers**: Immediate escalation
- **Final**: Migration completion summary

### Documentation
- [ ] Architecture documentation updated
- [ ] API reference updated
- [ ] CLI reference updated
- [ ] MCP protocol documentation updated
- [ ] Migration guide for external users
- [ ] Troubleshooting guide

---

## Next Steps

1. **Review & Approve Plan** (1 day)
2. **Set Up Project Tracking** (1 day)
   - Create GitHub project/issues
   - Assign owners to tasks
   - Set up CI/CD pipeline
3. **Begin Phase 1** (Start TASK-001)
4. **Weekly Progress Reviews**
5. **Phase Gates** (review before next phase)

---

## Appendix: Task Card Template

Each task card follows this structure:

```markdown
# TASK-XXX: [Task Name]

## Metadata
- **Priority**: P0/P1/P2
- **Effort**: X days
- **Owner**: TBD
- **Status**: Not Started / In Progress / In Review / Done
- **Dependencies**: [List of task IDs]

## Objective
[Clear, concise objective statement]

## Scope
### In Scope
- [Specific items included]

### Out of Scope
- [Specific items excluded]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Code reviewed

## Implementation Plan

### Files to Create
- [List new files with purpose]

### Files to Modify
- [List files to modify with changes]

### Files to Delete
- [List files to remove]

## Testing Requirements

### Unit Tests
- [Test scenarios]

### Integration Tests
- [Integration scenarios]

### Manual Testing
- [Manual test steps]

## Documentation Updates
- [ ] Update [specific doc file]
- [ ] Add examples
- [ ] Update API reference

## Runbook
```bash
# Step 1: [Description]
command1

# Step 2: [Description]
command2
```

## Rollback Plan
[Steps to revert this task]

## Definition of Done
- [ ] All acceptance criteria met
- [ ] Tests passing (>90% coverage)
- [ ] Documentation updated
- [ ] Code reviewed and approved
- [ ] No regressions detected
- [ ] Performance validated (<5ms overhead)
```

---

**End of Plan**
