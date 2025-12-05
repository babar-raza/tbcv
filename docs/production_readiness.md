# Production Readiness Checklist

**Purpose**: Validate that TBCV MCP migration is ready for production deployment.
**Version**: 1.0
**Date**: 2025-12-01

Complete all sections before deploying to production. Each checkbox represents a required validation step.

---

## Technical Readiness

### Code Quality

#### Tests
- [ ] All 500+ tests passing without failures
- [ ] Test coverage >90% for MCP code (`svc/`, `core/`)
- [ ] No skipped or xfailed tests in core functionality
- [ ] All integration tests passing
- [ ] All end-to-end tests passing
- [ ] Performance tests passing and meeting targets
- [ ] Security tests passing (access guards validated)

**Validation Command**:
```bash
pytest tests/ -v --cov=svc --cov=core --cov-report=html
# Expected: PASSED, coverage >90%
```

#### Code Standards
- [ ] No linting errors (flake8, pylint)
- [ ] No type checking errors (mypy)
- [ ] Code formatted consistently (black)
- [ ] No TODO/FIXME comments in production code
- [ ] All docstrings present and accurate
- [ ] Type hints on all public functions

**Validation Commands**:
```bash
black --check svc/ core/ api/ cli/
mypy svc/ core/
flake8 svc/ core/ api/ cli/ --max-line-length=120
```

#### Code Review
- [ ] All PRs reviewed and approved
- [ ] No outstanding review comments
- [ ] Security review completed
- [ ] Performance review completed
- [ ] Architecture review completed

**Validation**: Check GitHub PR history for approvals.

---

### Functionality

#### MCP Methods (56 Total)
- [ ] All validation methods tested (8 methods)
- [ ] All approval methods tested (4 methods)
- [ ] All enhancement methods tested (8 methods)
- [ ] All recommendation methods tested (9 methods)
- [ ] All workflow methods tested (8 methods)
- [ ] All admin methods tested (14 methods)
- [ ] All query/analytics methods tested (5 methods)

**Validation**: Review test results for `tests/svc/test_mcp_*.py`

#### CLI Commands
- [ ] All validation commands work via MCP
- [ ] All approval commands work via MCP
- [ ] All enhancement commands work via MCP
- [ ] All recommendation commands work via MCP
- [ ] All workflow commands work via MCP
- [ ] All admin commands work via MCP
- [ ] Help text displays correctly
- [ ] Error messages clear and actionable

**Validation Commands**:
```bash
python cli/main.py validate-file README.md
python cli/main.py validations list
python cli/main.py recommendations generate <validation-id>
python cli/main.py workflows create validate_directory .
python cli/main.py admin stats
```

#### API Endpoints
- [ ] All validation endpoints responding (200 status)
- [ ] All approval endpoints responding
- [ ] All enhancement endpoints responding
- [ ] All recommendation endpoints responding
- [ ] All workflow endpoints responding
- [ ] All admin endpoints responding
- [ ] Health check endpoint responding
- [ ] OpenAPI docs accessible at `/docs`

**Validation Commands**:
```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/validations?limit=10
curl http://localhost:8000/docs
```

#### WebSocket & Real-time
- [ ] WebSocket connections stable
- [ ] Workflow progress updates streaming
- [ ] Live event bus functional
- [ ] No connection drops under load
- [ ] Reconnection logic working

**Validation**: Test dashboard live updates during workflow execution.

#### Export & Reporting
- [ ] Validation export working (JSON format)
- [ ] Recommendation export working
- [ ] Workflow export working
- [ ] Report generation working
- [ ] Export schema validated

**Validation Commands**:
```bash
python cli/main.py export validation <validation-id> --format json
python cli/main.py export workflow <workflow-id>
```

---

### Performance

#### MCP Overhead
- [ ] MCP overhead <5ms per operation (target met)
- [ ] Baseline performance measured
- [ ] No performance regressions vs direct access
- [ ] Overhead consistent across operations

**Validation**:
```bash
pytest tests/performance/test_mcp_overhead.py -v
```

**Expected Output**:
```
test_mcp_overhead ... PASSED (avg: 2.3ms) ✓
```

#### API Response Times
- [ ] Simple operations <50ms (GET /api/validations/{id})
- [ ] Complex operations <100ms (POST /api/validate/file)
- [ ] Bulk operations <500ms (bulk approve 100 validations)
- [ ] Workflow operations <1000ms (create workflow)

**Validation**:
```bash
pytest tests/performance/test_api_response_times.py -v
```

#### Concurrent Operations
- [ ] 100+ concurrent operations tested
- [ ] 200+ async operations tested
- [ ] No errors under concurrent load
- [ ] Throughput meets targets (>10 ops/sec)
- [ ] Connection pooling working correctly

**Validation**:
```bash
pytest tests/performance/test_concurrent_operations.py -v
```

#### Sustained Load
- [ ] System stable under 60s sustained load
- [ ] No memory leaks detected
- [ ] No resource exhaustion
- [ ] Error rate <1% under load
- [ ] Performance consistent throughout test

**Validation**:
```bash
pytest tests/performance/test_sustained_load.py -v
```

#### Database Performance
- [ ] Query performance optimized
- [ ] Indexes present on key columns
- [ ] Connection pooling configured
- [ ] No N+1 query patterns
- [ ] Bulk operations use batching

**Validation**: Review slow query logs, run EXPLAIN on key queries.

---

### Security

#### Access Guards
- [ ] Access guards enabled in all environments (block mode)
- [ ] CLI cannot access business logic directly
- [ ] API cannot access business logic directly
- [ ] MCP server can access all operations
- [ ] Violations logged with full context
- [ ] No bypass mechanisms exist

**Validation**:
```bash
pytest tests/security/test_access_guards.py -v
```

**Manual Test** (should fail):
```bash
python -c "from core.database import DatabaseManager; DatabaseManager()"
# Expected: RuntimeError: Direct access not allowed
```

**Manual Test** (should succeed):
```bash
python -c "from svc.mcp_client import MCPSyncClient; client = MCPSyncClient(); print(client.get_stats())"
# Expected: System statistics printed
```

#### Security Vulnerabilities
- [ ] No SQL injection vectors
- [ ] No path traversal vulnerabilities
- [ ] Input validation on all MCP methods
- [ ] No secrets in code or logs
- [ ] Dependencies scanned for vulnerabilities

**Validation**:
```bash
bandit -r svc/ core/ -ll
safety check
```

#### Authentication & Authorization
- [ ] API endpoints require authentication (if enabled)
- [ ] Role-based access control working (if enabled)
- [ ] Token validation working
- [ ] Session management secure

**Note**: Authentication may not be implemented yet - mark N/A if not applicable.

---

## Operational Readiness

### Documentation

#### Technical Documentation
- [ ] Architecture documentation updated (`docs/architecture.md`)
- [ ] MCP integration guide complete (`docs/mcp_integration.md`)
- [ ] Migration guide complete (`docs/migration_guide.md`)
- [ ] API reference updated (`docs/api_reference.md`)
- [ ] CLI usage guide updated (`docs/cli_usage.md`)
- [ ] Testing guide updated (`docs/testing.md`)

**Validation**: Review each document for accuracy and completeness.

#### Operational Documentation
- [ ] Deployment guide updated (`docs/deployment.md`)
- [ ] Runbook complete with step-by-step procedures
- [ ] Troubleshooting guide complete
- [ ] Rollback procedures documented and tested
- [ ] Disaster recovery procedures documented

**Validation**: Execute procedures from documentation to verify accuracy.

#### Code Documentation
- [ ] All MCP methods documented with examples
- [ ] Client usage documented
- [ ] Error handling documented
- [ ] Configuration options documented
- [ ] Environment variables documented

**Validation**: Review docstrings in `svc/mcp_server.py` and `svc/mcp_client.py`.

---

### Deployment

#### Deployment Runbook
- [ ] Runbook created with detailed steps
- [ ] Pre-deployment checklist complete
- [ ] Deployment steps documented
- [ ] Post-deployment validation steps documented
- [ ] Emergency procedures documented

**Validation**: Review `docs/migration_guide.md` deployment section.

#### Environment Configuration
- [ ] Development environment configured
- [ ] Staging environment configured
- [ ] Production environment configured
- [ ] Environment variables documented
- [ ] Configuration files prepared for each environment

**Required Environment Variables**:
```bash
# Core
DATABASE_URL=sqlite:///data/tbcv.db
ENVIRONMENT=production

# MCP
MCP_ENFORCE=true

# Optional
OLLAMA_BASE_URL=http://localhost:11434
LOG_LEVEL=info
```

#### Configuration Management
- [ ] All config files in version control
- [ ] Sensitive data not in configs (use env vars)
- [ ] Config validation implemented
- [ ] Default values documented
- [ ] Override mechanisms documented

**Files**:
- `config/access_guards.yaml`
- `config/cache.yaml`
- `config/llm.yaml`
- `config/validation_flow.yaml`

#### Database Management
- [ ] Database migrations tested
- [ ] Backup procedures documented
- [ ] Restore procedures tested
- [ ] Migration rollback tested
- [ ] Database monitoring configured

**Validation**:
```bash
# Test backup
python scripts/backup_database.py

# Test restore
python scripts/restore_database.py backup/tbcv.db.backup
```

#### Deployment Testing
- [ ] Deployment tested in staging environment
- [ ] Rollback tested in staging environment
- [ ] Zero-downtime deployment possible
- [ ] Database migrations non-blocking
- [ ] Service restart procedures tested

#### Optional Services Configuration
- [ ] Ollama configuration validated (if using LLM validation)
- [ ] ChromaDB configuration validated (if using RAG)
- [ ] PostgreSQL configuration validated (if using for production)
- [ ] Redis configuration validated (if using distributed cache)
- [ ] Prometheus configuration validated (if implemented)
- [ ] Sentry configuration validated (if using error tracking)
- [ ] Google GenAI configuration validated (if using LLM fallback)

**Service Selection Guide**:

All external services are **optional**. Choose based on your deployment scenario:

| Scenario | Ollama | ChromaDB | PostgreSQL | Redis | Prometheus | Sentry |
|----------|--------|----------|------------|-------|------------|--------|
| **Local Development** | Optional | Optional | No | No | No | No |
| **Single-node Production** | Optional | Optional | Recommended | No | Recommended | Recommended |
| **Multi-node Production** | Optional | Optional | Required | Required | Required | Required |
| **High-volume Validation** | Recommended | Recommended | Required | Required | Required | Required |

**Configuration Examples**:

Local development (defaults):
```bash
# No special configuration needed - uses SQLite, no LLM
python main.py --mode api
```

Single-node production with SQLite:
```bash
export TBCV_SYSTEM_ENVIRONMENT=production
export TBCV_SYSTEM_LOG_LEVEL=info
# Optional: Enable LLM validation
export TBCV_LLM_VALIDATOR__ENABLED=true
export TBCV_LLM_VALIDATOR__MODEL=qwen2.5:latest
```

Multi-node production with PostgreSQL and Redis:
```bash
export DATABASE_URL=postgresql://user:pass@host:5432/tbcv
export TBCV_CACHING__L2__BACKEND=redis
export TBCV_CACHING__L2__REDIS_URL=redis://host:6379
export TBCV_SYSTEM_ENVIRONMENT=production
export TBCV_PROMETHEUS__ENABLED=true
```

High-volume with all optional services:
```bash
export DATABASE_URL=postgresql://user:pass@host:5432/tbcv
export TBCV_CACHING__L2__BACKEND=redis
export TBCV_CACHING__L2__REDIS_URL=redis://host:6379
export TBCV_LLM_VALIDATOR__ENABLED=true
export TBCV_LLM_VALIDATOR__MODEL=qwen2.5:latest
export TBCV_RAG__ENABLED=true
export TBCV_PROMETHEUS__ENABLED=true
export GOOGLE_API_KEY=your-google-api-key
export TBCV_SYSTEM_ENVIRONMENT=production
# Error tracking via structured logging to external service (see Error Tracking section)
```

---

### Monitoring

#### Logging
- [ ] Structured logging configured (JSON format)
- [ ] Log levels appropriate for production
- [ ] Log rotation configured
- [ ] Log aggregation configured (if applicable)
- [ ] Sensitive data not logged
- [ ] MCP operations logged with context

**Log Files**:
- `logs/tbcv.log` - Application logs
- `logs/mcp.log` - MCP server logs
- `logs/access_violations.log` - Access guard violations

**Validation**: Review log files for completeness and format.

#### Error Tracking

**Approach:** Structured logging to external service

**Rationale:**
- Sentry SDK removed to reduce dependencies and complexity
- Structured JSON logging (core/logging.py) provides comprehensive error tracking
- JSON logs can be shipped to any log aggregation service
- Simpler maintenance and fewer external service dependencies

**Alternative Approaches:**
- Datadog APM - Full observability platform with APM, logs, and metrics
- New Relic - Enterprise APM with error tracking and performance monitoring
- Elasticsearch + Kibana (ELK Stack) - Open source log aggregation and analysis
- Splunk - Enterprise log aggregation and security monitoring

**Setup with Log Shipping:**
```bash
# Export logs to external service using Filebeat
filebeat -c filebeat.yml

# Example: Ship logs to Datadog
# filebeat.yml
output.datadog:
  api_key: ${DATADOG_API_KEY}
  site: datadoghq.com
```

**Current Logging Setup:**
- All errors logged to `logs/tbcv.log` in JSON format
- Structured logging includes context, stack traces, and metadata
- Logs rotated daily and archived
- Access guard violations logged separately to `logs/access_violations.log`

**For Production Error Tracking:**
1. Configure log shipping to external service (Datadog, New Relic, Splunk)
2. Set up alerts for ERROR and CRITICAL level logs
3. Configure dashboards to monitor error patterns
4. Implement log retention policy (minimum 30 days)
5. Test error scenarios and verify logs appear in external service

#### Metrics Collection (Planned)
- [ ] Performance metrics collected (planned for future release)
- [ ] Operation metrics collected (counts, durations) (planned for future release)
- [ ] Error metrics collected (planned for future release)
- [ ] Business metrics collected (validations, recommendations) (planned for future release)
- [ ] Resource metrics collected (CPU, memory, disk) (planned for future release)

**Status**: Planned for future release. Prometheus monitoring infrastructure is configured but not yet implemented.

**Current State**:
- Configuration present in `config/main.yaml` (monitoring section)
- prometheus-client package installed as dependency
- Implementation pending

**Workaround**:
Use structured JSON logging (see Logging section below) and export logs to external monitoring services:
- Export logs to Datadog, New Relic, Splunk, or CloudWatch
- Use database.metrics table for custom application metrics
- Monitor via API health endpoints at `/health/live`, `/health/ready`, `/health/detailed`
- Use admin endpoint `/admin/status` for system status checks

**Key Metrics** (planned for future):
- MCP operation count and duration
- Validation success/failure rates
- API response times
- Database query times
- Cache hit rates
- Agent performance metrics
- System metrics (CPU, memory, disk)

**Planned Monitoring Features**:
- `/metrics` endpoint for Prometheus scraping
- Application metrics (validation counts, success rates, processing times)
- System metrics (CPU, memory, disk via psutil)
- Agent metrics (calls, latency, errors per agent)
- Cache metrics (hit rate, size, evictions)
- Database metrics (query count, latency, pool size)
- Custom metrics via PerformanceLogger integration

#### Alerting
- [ ] Critical alerts configured
- [ ] Warning alerts configured
- [ ] Alert routing configured
- [ ] Alert escalation configured
- [ ] Alert testing completed

**Critical Alerts**:
- Service down
- Database connection failures
- High error rates (>5%)
- High response times (>500ms)
- Disk space low (<10%)

**Warning Alerts**:
- Increased error rates (>1%)
- Increased response times (>200ms)
- Cache hit rate low (<80%)
- Access guard violations

#### Dashboards
- [ ] System health dashboard created
- [ ] Performance dashboard created
- [ ] Business metrics dashboard created
- [ ] Alert dashboard created
- [ ] Dashboards accessible to ops team

**Dashboard URLs**:
- `/dashboard` - System overview with recent validations, recommendations, and workflows
- `/dashboard/monitoring` - **Performance Monitoring Dashboard** (newly implemented)
  - Real-time system metrics (CPU, memory, disk usage)
  - Validation throughput and agent performance
  - Cache hit rates and database query times
  - Historical charts for trend analysis
  - Configurable alert thresholds
  - Export functionality (CSV, JSON)
  - Mobile-responsive design
- `/dashboard/validations` - Validation list and details
- `/dashboard/recommendations` - Recommendation list and details
- `/dashboard/workflows` - Workflow management
- `/dashboard/audit` - Audit logs

**Performance Monitoring Dashboard Features**:
- **Real-time Metrics**: Auto-refresh every 5 seconds
  - Validation throughput (validations per minute)
  - Agent average response time
  - Cache hit rate percentage
  - Database average query time
  - System resources (CPU, memory, disk)

- **Historical Graphs**: 4 interactive charts using Chart.js
  - Validation throughput over time
  - Response times (agent and database)
  - System resource utilization
  - Error rate and success rate

- **Detailed Tables**:
  - Agent performance breakdown by agent type
  - Database operation metrics with percentiles (P95, P99)
  - Cache performance statistics

- **Alert Configuration**:
  - Configurable thresholds for all metrics
  - Alert cooldown periods
  - Recent alerts log with timestamps
  - Visual indicators for threshold violations

- **Export Capabilities**:
  - JSON export with full metrics
  - CSV export for spreadsheet analysis
  - Timestamped downloads

**Usage**:
1. Start the server: `python main.py --mode api`
2. Access dashboard: `http://localhost:8080/dashboard/monitoring`
3. Configure alert thresholds via the dashboard UI
4. Monitor real-time metrics and historical trends
5. Export data for analysis or reporting

---

### Training & Support

#### Team Training
- [ ] Development team trained on MCP architecture
- [ ] Operations team trained on deployment procedures
- [ ] Support team trained on troubleshooting
- [ ] All team members understand rollback procedures
- [ ] Training materials available

**Training Topics**:
- MCP-first architecture overview
- How to use MCP clients
- Common issues and solutions
- Monitoring and alerting
- Rollback procedures

#### Knowledge Transfer
- [ ] Architecture walkthrough completed
- [ ] Code walkthrough completed
- [ ] Operational walkthrough completed
- [ ] Q&A session completed
- [ ] Team can independently support system

#### Support Procedures
- [ ] On-call rotation defined
- [ ] Escalation procedures documented
- [ ] Contact list maintained
- [ ] Support runbook created
- [ ] Incident response plan documented

---

### Testing & Validation

#### Automated Testing
- [ ] Unit tests passing (500+ tests)
- [ ] Integration tests passing
- [ ] End-to-end tests passing
- [ ] Performance tests passing
- [ ] Security tests passing
- [ ] Regression tests passing

**Test Execution**:
```bash
pytest tests/ -v --tb=short --durations=20
```

#### Manual Testing
- [ ] CLI commands tested manually
- [ ] API endpoints tested manually (Postman/curl)
- [ ] Dashboard tested manually
- [ ] WebSocket connections tested
- [ ] Error scenarios tested
- [ ] Edge cases tested

**Manual Test Scenarios**:
1. Validate single file
2. Validate directory (100+ files)
3. Approve validation
4. Reject validation
5. Generate recommendations
6. Apply recommendations
7. Create and monitor workflow
8. Test with invalid inputs
9. Test with missing files
10. Test concurrent operations

#### Load Testing
- [ ] Load test scenarios defined
- [ ] Load tests executed
- [ ] System stable under load
- [ ] Performance targets met
- [ ] Resource usage acceptable

**Load Test Results**:
- Concurrent users: 100+
- Duration: 60+ seconds
- Error rate: <1%
- Response time P95: <200ms
- Response time P99: <500ms

#### User Acceptance Testing
- [ ] UAT scenarios defined
- [ ] UAT executed by stakeholders
- [ ] All critical paths validated
- [ ] Feedback incorporated
- [ ] Sign-off obtained

---

## Risk Assessment

### Known Risks

#### High Risk
- [ ] Database corruption during migration
  - **Mitigation**: Tested backup and restore procedures
  - **Status**: Mitigated
- [ ] Access guards breaking existing functionality
  - **Mitigation**: Warn mode first, comprehensive testing
  - **Status**: Mitigated

#### Medium Risk
- [ ] Performance degradation under load
  - **Mitigation**: Performance testing, monitoring
  - **Status**: Mitigated
- [ ] Integration issues with external systems
  - **Mitigation**: Integration tests, staging validation
  - **Status**: Mitigated

#### Low Risk
- [ ] Documentation gaps
  - **Mitigation**: Comprehensive documentation review
  - **Status**: Mitigated
- [ ] Team learning curve
  - **Mitigation**: Training sessions, documentation
  - **Status**: Mitigated

### Rollback Readiness
- [ ] Rollback procedures documented
- [ ] Rollback tested in staging
- [ ] Rollback window identified (max 30 minutes)
- [ ] Rollback owner identified
- [ ] Emergency contacts available

---

## Compliance & Governance

### Change Management
- [ ] Change request submitted
- [ ] Change reviewed and approved
- [ ] Stakeholders notified
- [ ] Maintenance window scheduled
- [ ] Communication plan executed

### Audit Trail
- [ ] All changes logged in version control
- [ ] Migration steps documented
- [ ] Test results archived
- [ ] Sign-offs documented
- [ ] Post-mortem template prepared

---

## Sign-Off

### Engineering

**Engineering Lead**:
- Name: _______________________________________
- Signature: ___________________________________
- Date: ________________________________________
- Comments: ___________________________________

**Quality Assurance Lead**:
- Name: _______________________________________
- Signature: ___________________________________
- Date: ________________________________________
- Comments: ___________________________________

### Operations

**Operations Lead**:
- Name: _______________________________________
- Signature: ___________________________________
- Date: ________________________________________
- Comments: ___________________________________

**Site Reliability Engineer**:
- Name: _______________________________________
- Signature: ___________________________________
- Date: ________________________________________
- Comments: ___________________________________

### Security

**Security Review**:
- Name: _______________________________________
- Signature: ___________________________________
- Date: ________________________________________
- Comments: ___________________________________

### Product

**Product Owner**:
- Name: _______________________________________
- Signature: ___________________________________
- Date: ________________________________________
- Comments: ___________________________________

---

## Final Approval

### Deployment Decision

**Deploy to Production**: ☐ Yes  ☐ No

**Deployment Date**: ____________________

**Deployment Window**: __________________

**Rollback Owner**: ______________________

### Conditions for Approval

All of the following must be true:

- [ ] All technical readiness items checked
- [ ] All operational readiness items checked
- [ ] All high/medium risks mitigated
- [ ] All stakeholders trained
- [ ] All sign-offs obtained
- [ ] Rollback procedures tested
- [ ] Monitoring and alerting configured
- [ ] Communication plan executed

### Post-Deployment Monitoring

**Monitor for 48 hours after deployment**:

- [ ] Hour 1: System stability check
- [ ] Hour 4: Performance validation
- [ ] Hour 24: Full system validation
- [ ] Hour 48: Final sign-off

**Monitoring Checklist**:
- [ ] No critical errors in logs
- [ ] Performance within acceptable range
- [ ] No access guard violations (unexpected)
- [ ] All services responding
- [ ] Database stable
- [ ] No user-reported issues

---

## Summary

### Completion Status

**Total Checklist Items**: 150+
**Items Completed**: _________
**Completion Percentage**: _________%

**Required for Production**: 100%

### Outstanding Items

List any incomplete items:

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

### Action Items

List required actions before deployment:

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

### Notes

Add any additional notes or observations:

_______________________________________________
_______________________________________________
_______________________________________________

---

**Document Status**: ☐ Draft  ☐ In Review  ☐ Approved

**Last Updated**: ____________________

**Next Review Date**: ____________________

---

## Quick Reference

### Critical Commands

**Start System**:
```bash
python main.py
```

**Health Check**:
```bash
curl http://localhost:8000/api/health
python cli/main.py admin stats
```

**View Logs**:
```bash
tail -f logs/tbcv.log
grep ERROR logs/tbcv.log
```

**Run Tests**:
```bash
pytest tests/ -v
```

**Backup Database**:
```bash
cp data/tbcv.db backup/tbcv.db.$(date +%Y%m%d_%H%M%S)
```

### Emergency Contacts

**Engineering Lead**: ___________________
**On-Call Engineer**: ___________________
**Operations Lead**: ___________________
**Security Team**: ___________________

### Key URLs

**Production API**: ___________________
**Dashboard**: ___________________
**Monitoring**: ___________________
**Documentation**: https://github.com/tbcv/docs

---

**Remember**: Production readiness is not just about passing tests. It's about confidence that the system will work reliably in production and that the team can support it effectively.
