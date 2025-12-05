# Deployment Checklist

**TBCV - Truth-Based Content Validation System**
Comprehensive Pre-Deployment, Deployment, and Post-Deployment Verification Guide

**Version**: 2.0
**Last Updated**: 2024-12-05
**Applicable to**: TBCV v2.0.0+

---

## Table of Contents

1. [Quick Checklist Summary](#quick-checklist-summary)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Deployment Checklist](#deployment-checklist)
4. [Post-Deployment Verification](#post-deployment-verification)
5. [Environment-Specific Checklists](#environment-specific-checklists)
6. [Rollback Checklist](#rollback-checklist)
7. [Troubleshooting Common Issues](#troubleshooting-common-issues)
8. [Verification Commands Reference](#verification-commands-reference)

---

## Quick Checklist Summary

| Phase | Items | Est. Time |
|-------|-------|-----------|
| Pre-Deployment | 18 items | 30-45 min |
| Deployment | 12 items | 15-30 min |
| Post-Deployment | 14 items | 20-30 min |
| **Total** | **44 items** | **60-105 min** |

---

## Pre-Deployment Checklist

**Estimated Time**: 30-45 minutes
**Purpose**: Verify all prerequisites and readiness before deployment

### System Requirements Verification

- [ ] ⚠️ **Critical**: Verify Python version 3.8+ installed on target server
  - **Why**: TBCV requires Python 3.8+. Older versions will cause import errors.
  - **Verification Command**: `python --version`
  - **Expected Output**: `Python 3.8.0` or higher

- [ ] ⚠️ **Critical**: Verify available disk space (minimum 1GB for application, additional space for data)
  - **Why**: Insufficient disk space will cause deployment failure and data loss.
  - **Verification Command**: `df -h /path/to/deployment` (Linux/Mac) or `dir C:\` (Windows)
  - **Expected Output**: At least 5GB free space for safe operation

- [ ] ⚠️ **Critical**: Verify system memory (minimum 2GB, 8GB recommended for production)
  - **Why**: Insufficient memory causes out-of-memory errors and service crashes.
  - **Verification Command**: `free -h` (Linux) or `systeminfo | findstr /C:"Total Physical Memory"` (Windows)
  - **Expected Output**: At least 2GB available RAM

- [ ] Verify CPU resources (minimum 2 cores, 4+ cores recommended)
  - **Why**: Multi-agent system benefits from multiple CPU cores for concurrent processing.
  - **Verification Command**: `nproc` (Linux) or `echo %NUMBER_OF_PROCESSORS%` (Windows)
  - **Expected Output**: 2 or more cores available

- [ ] Verify network connectivity to external services (if applicable)
  - **Why**: Many features depend on external integrations (Ollama, ChromaDB, PostgreSQL, etc.).
  - **Verification Commands**:
    ```bash
    # Test Ollama connectivity (if using LLM)
    curl -s http://localhost:11434/api/status

    # Test ChromaDB connectivity (if using RAG)
    curl -s http://localhost:8000/api/v1/heartbeat

    # Test PostgreSQL connectivity (if using as database)
    psql -h hostname -U username -d database -c "SELECT 1;"
    ```
  - **Expected Output**: HTTP 200 responses or successful database connection

- [ ] Verify OS compatibility (Linux, macOS, or Windows with WSL2 recommended)
  - **Why**: Some scripts are shell-based and may require adaptation for Windows.
  - **Verification**: Review docs/deployment.md OS support section
  - **Action**: If Windows, use WSL2 or adapt scripts to batch/PowerShell

### Dependencies Check

- [ ] ⚠️ **Critical**: Verify all Python dependencies can be installed
  - **Why**: Missing or incompatible dependencies will cause import failures.
  - **Verification Commands**:
    ```bash
    # Create virtual environment
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows

    # Install dependencies
    pip install -r requirements.txt
    ```
  - **Expected Output**: All packages installed successfully without errors
  - **Failure Handling**: If pip install fails, check Python version and network connectivity

- [ ] Verify development dependencies (if deploying development environment)
  - **Why**: Development tools needed for debugging and testing.
  - **Verification Command**: `pip install -r requirements.txt -e .[dev]`
  - **Expected Output**: Test framework, linting tools installed successfully

- [ ] Verify performance monitoring dependencies (if monitoring production)
  - **Why**: Metrics collection requires additional packages.
  - **Verification Command**: `pip install -r requirements.txt -e .[performance]`
  - **Expected Output**: Monitoring packages installed without errors

- [ ] Verify optional external service clients (based on enabled features)
  - **Why**: Features like LLM validation and RAG require specific clients.
  - **Verification Commands**:
    ```bash
    pip install ollama      # For LLM features
    pip install chromadb    # For RAG features
    pip install psycopg2    # For PostgreSQL
    ```
  - **Expected Output**: Respective clients installed successfully

- [ ] Check for conflicting dependency versions
  - **Why**: Incompatible versions can cause runtime errors.
  - **Verification Command**: `pip check`
  - **Expected Output**: No conflicting dependencies listed

### Configuration Review

- [ ] ⚠️ **Critical**: Review and validate main.yaml configuration file
  - **Why**: Incorrect configuration causes deployment failures and runtime errors.
  - **Verification**:
    ```bash
    # Validate YAML syntax
    python -c "import yaml; yaml.safe_load(open('config/main.yaml'))"
    ```
  - **Expected Output**: No syntax errors
  - **Action Items**:
    - Review `system.environment` setting matches deployment environment
    - Verify `system.log_level` appropriate for deployment
    - Check `server.host` and `server.port` settings

- [ ] ⚠️ **Critical**: Verify database configuration matches deployment environment
  - **Why**: Wrong database settings cause data loss or deployment to wrong server.
  - **Verification Items**:
    - Database URL points to correct server (not development server)
    - Database credentials are correct and secure
    - Database user has appropriate permissions (CREATE, SELECT, INSERT, UPDATE, DELETE)
    - Connection string is valid and accessible
  - **Verification Commands**:
    ```bash
    # Test database connection
    python -c "from core.database import Database; db = Database(); print('Connection OK')"
    ```
  - **Expected Output**: Connection successful message

- [ ] Verify server configuration (host, port, CORS origins)
  - **Why**: Incorrect server config prevents clients from connecting.
  - **Verification Items**:
    - `server.host` should be `0.0.0.0` for production (or specific IP)
    - `server.port` not already in use
    - CORS origins include all client origins
    - Request timeout appropriate for workload (30s default good for most cases)
  - **Verification Commands**:
    ```bash
    # Check if port is in use
    lsof -i :8080  # Linux/Mac
    netstat -ano | findstr :8080  # Windows
    ```

- [ ] Verify agent configurations match deployment requirements
  - **Why**: Agent settings affect validation accuracy and performance.
  - **Verification Items**:
    - Fuzzy detector similarity threshold appropriate (0.85 is default, good)
    - Content validator enabled for production
    - Content enhancer configuration matches requirements
    - Orchestrator max concurrent workflows appropriate for system capacity
    - Checkpoint intervals set appropriately (30s default good)

- [ ] Verify logging configuration
  - **Why**: Proper logging essential for troubleshooting production issues.
  - **Verification Items**:
    - Log level set to INFO or higher for production (not DEBUG)
    - Log output directory has write permissions
    - Log rotation configured (if using file logging)
    - Sufficient disk space for logs

- [ ] Verify cache configuration
  - **Why**: Cache settings affect performance and memory usage.
  - **Verification Items**:
    - L1 cache size appropriate for available memory
    - L2 cache type selected (in-memory or Redis)
    - Redis connection configured if using Redis L2 cache
    - TTL values reasonable for use case

- [ ] Verify security configuration
  - **Why**: Security misconfiguration exposes system to vulnerabilities.
  - **Verification Items**:
    - Access guard enabled
    - Authentication mechanism configured
    - API keys/tokens managed securely (via environment variables, not hardcoded)
    - CORS properly configured to prevent unauthorized access
    - Secrets not stored in configuration files

### Security Audit

- [ ] ⚠️ **Critical**: Verify no hardcoded credentials or secrets in codebase
  - **Why**: Hardcoded secrets can be exposed in version control and logs.
  - **Verification Commands**:
    ```bash
    # Search for common secret patterns
    grep -r "password\|api_key\|secret\|token" --include="*.py" --include="*.yaml" --include="*.json" \
      --exclude-dir=.git --exclude-dir=__pycache__ .

    # Check for AWS/Azure credentials
    grep -r "AKIA\|aws_access_key\|azure_" --include="*.py" --include="*.yaml" .
    ```
  - **Expected Output**: No matches in source code (only example/template files)

- [ ] ⚠️ **Critical**: Verify environment variables are set for sensitive data
  - **Why**: Environment variables prevent secrets from being exposed.
  - **Verification Items**:
    - Database password from environment variable (DATABASE_PASSWORD)
    - API keys from environment variables (OLLAMA_API_KEY, etc.)
    - No secrets in deployment scripts or configuration files
  - **Action**: Set environment variables before deployment start

- [ ] Verify access control mechanisms enabled
  - **Why**: Access control prevents unauthorized data access.
  - **Verification Items**:
    - Access guard module enabled in configuration
    - Role-based access control (RBAC) configured if needed
    - Admin credentials strong and unique
    - Review docs/access_guard.md for security model
  - **Verification Command**: `grep -r "access_guard" config/`

- [ ] ⚠️ **Critical**: Verify HTTPS/TLS configured for production
  - **Why**: HTTP exposes data in transit.
  - **Verification Items**:
    - SSL certificates obtained and valid
    - Certificate paths configured in server settings
    - Reverse proxy (nginx/Apache) configured for TLS termination
    - Redirect HTTP to HTTPS configured
  - **Verification Command**: `openssl s_client -connect hostname:443`

- [ ] Verify rate limiting configured
  - **Why**: Rate limiting prevents brute force and DoS attacks.
  - **Verification Items**:
    - Rate limits set in configuration
    - Verification that limits are reasonable (not too strict, not too permissive)

- [ ] Verify authentication mechanism configured
  - **Why**: Authentication prevents unauthorized access.
  - **Verification Items**:
    - Authentication type configured (if required by your setup)
    - Session management configured appropriately
    - Token expiration set to reasonable values

- [ ] Run security scanning tools
  - **Why**: Automated scanning catches known vulnerabilities.
  - **Verification Commands**:
    ```bash
    # Scan for known vulnerabilities in dependencies
    pip install safety
    safety check

    # Run bandit for code security issues
    pip install bandit
    bandit -r svc/ core/ api/ cli/
    ```
  - **Expected Output**: No critical vulnerabilities found
  - **Action**: Fix any discovered vulnerabilities before deployment

- [ ] Verify backup and recovery procedures documented
  - **Why**: Ability to recover from security incidents is critical.
  - **Verification Items**:
    - Backup strategy documented
    - Recovery procedures tested
    - Backups stored in secure, separate location

### Database Preparation

- [ ] ⚠️ **Critical**: Create production database (if using PostgreSQL)
  - **Why**: Wrong database configuration causes data loss.
  - **Verification Commands**:
    ```bash
    # Create database
    createdb -U postgres tbcv_prod

    # Create user if needed
    psql -U postgres -c "CREATE USER tbcv_user WITH PASSWORD 'secure_password';"
    psql -U postgres -c "ALTER USER tbcv_user CREATEDB;"

    # Grant permissions
    psql -U postgres -d tbcv_prod -c "GRANT ALL PRIVILEGES ON DATABASE tbcv_prod TO tbcv_user;"
    ```
  - **Expected Output**: Database and user created successfully

- [ ] ⚠️ **Critical**: Run database migrations
  - **Why**: Schema must match application expectations.
  - **Verification Commands**:
    ```bash
    # Using Alembic for migrations
    alembic upgrade head

    # Verify schema created
    psql -U tbcv_user -d tbcv_prod -c "\dt"
    ```
  - **Expected Output**: All tables created successfully
  - **Failure Handling**: Check alembic.ini configuration and migration files

- [ ] Verify database backups configured
  - **Why**: Backups provide disaster recovery capability.
  - **Verification Items**:
    - Automated backup schedule configured
    - Backup location verified and accessible
    - Backup retention policy documented
    - Test backup/restore procedure

- [ ] ⚠️ **Critical**: Verify database user permissions are minimal
  - **Why**: Excessive permissions increase security risk.
  - **Verification Items**:
    - Database user only has necessary permissions (not admin/superuser)
    - Separate read-only user created for reporting (if needed)
    - No hardcoded passwords in connection strings

- [ ] Initialize seed data (if required)
  - **Why**: Some data may need to be pre-populated.
  - **Verification Command**: Check if seed data scripts needed by reviewing docs/database_schema.md
  - **Action**: Run any required seed data scripts

- [ ] Verify data migration from previous version (if upgrading)
  - **Why**: Data loss during migration causes severe issues.
  - **Verification Items**:
    - Backup of existing data created
    - Migration procedure tested on backup
    - Data validation after migration completed
    - Rollback plan prepared and documented

- [ ] Performance test database queries
  - **Why**: Slow queries impact user experience.
  - **Verification Commands**:
    ```bash
    # Enable query profiling
    python -c "from core.database import Database; db = Database(); db.enable_profiling()"

    # Run performance tests
    pytest tests/performance/ -v
    ```
  - **Expected Output**: Queries execute within acceptable time limits

---

## Deployment Checklist

**Estimated Time**: 1-2 hours
**Purpose**: Execute the actual deployment process

### Pre-Deployment Final Checks

- [ ] ⚠️ **Critical**: Create backup of previous production deployment
  - **Why**: Enables rollback if new deployment has issues.
  - **Verification Commands**:
    ```bash
    # Backup application files
    tar -czf /backups/tbcv_backup_$(date +%Y%m%d_%H%M%S).tar.gz /path/to/tbcv

    # Backup database
    pg_dump -U tbcv_user tbcv_prod > /backups/tbcv_db_backup_$(date +%Y%m%d_%H%M%S).sql
    ```
  - **Expected Output**: Backup files created in /backups directory
  - **Verification**: List backup files and verify sizes are reasonable

- [ ] ⚠️ **Critical**: Notify stakeholders of deployment start time
  - **Why**: Teams need to know about maintenance window.
  - **Action Items**:
    - Send deployment notification email/Slack message
    - Include expected downtime and rollback procedure
    - Include contact information for issues

- [ ] Final code review of deployment branch
  - **Why**: Catches last-minute issues.
  - **Verification Items**:
    - Review all changes since last production release
    - Verify no uncommitted changes
    - Verify branch is up to date with main

- [ ] ⚠️ **Critical**: Verify no database locks or active connections
  - **Why**: Active connections prevent safe migrations.
  - **Verification Commands**:
    ```bash
    # Check for active connections
    psql -U postgres -d tbcv_prod -c "SELECT usename, count(*) FROM pg_stat_activity GROUP BY usename;"

    # Kill any hanging connections (if safe to do)
    psql -U postgres -d tbcv_prod -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='tbcv_prod' AND pid != pg_backend_pid();"
    ```
  - **Expected Output**: No active connections to the database

### Application Deployment

- [ ] Stop current production service
  - **Why**: Prevents conflicts during deployment.
  - **Verification Commands**:
    ```bash
    # Stop API service
    systemctl stop tbcv-api

    # Stop background workers (if applicable)
    systemctl stop tbcv-workers

    # Verify services stopped
    systemctl status tbcv-api
    ```
  - **Expected Output**: All services show as stopped/inactive
  - **Timeout**: Service should stop within 30 seconds

- [ ] Deploy application code to production
  - **Why**: Updates application with new version.
  - **Verification Commands**:
    ```bash
    # Navigate to deployment directory
    cd /opt/tbcv

    # Pull latest code (if using git)
    git fetch origin main
    git checkout main
    git reset --hard origin/main

    # Or extract from release archive
    tar -xzf tbcv-release-v2.0.0.tar.gz

    # Install dependencies
    pip install -r requirements.txt
    ```
  - **Expected Output**: All files deployed and dependencies installed

- [ ] Update Python virtual environment
  - **Why**: Ensures all packages match requirements.
  - **Verification Commands**:
    ```bash
    # Activate virtual environment
    source /opt/tbcv/venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install all dependencies
    pip install -r requirements.txt

    # Verify installation
    pip list
    ```
  - **Expected Output**: All required packages listed and at correct versions

- [ ] ⚠️ **Critical**: Apply configuration changes
  - **Why**: Configuration must match new application requirements.
  - **Verification Items**:
    - Copy config/main.yaml to deployment location
    - Verify environment-specific settings (database URL, server host, etc.)
    - Set required environment variables
    - Verify file permissions (readable by application user)
  - **Verification Commands**:
    ```bash
    # Validate configuration
    python -c "from core.config import Config; c = Config(); print('Config valid')"
    ```

- [ ] Update environment variables
  - **Why**: Environment-specific settings must be in place.
  - **Verification Items**:
    - DATABASE_URL set correctly
    - SECRET_KEY set to production value
    - LOG_LEVEL set to INFO (not DEBUG)
    - Any API keys set (OLLAMA_API_KEY, etc.)
    - Environment marked as "production"
  - **Verification Command**: `env | grep -E "DATABASE|SECRET|LOG_LEVEL"`

### Database Deployment

- [ ] ⚠️ **Critical**: Backup database before migrations
  - **Why**: Provides recovery point if migration fails.
  - **Verification Commands**:
    ```bash
    pg_dump -U tbcv_user tbcv_prod > /backups/pre_migration_backup.sql
    gzip /backups/pre_migration_backup.sql
    ```
  - **Expected Output**: Compressed backup file in /backups

- [ ] ⚠️ **Critical**: Run database migrations
  - **Why**: Schema must be updated for new application version.
  - **Verification Commands**:
    ```bash
    # Run migrations
    alembic upgrade head

    # Verify migration success
    alembic current
    alembic history --verbose
    ```
  - **Expected Output**: All migrations applied successfully
  - **Failure Handling**: See Rollback Plan section

- [ ] Verify schema integrity after migration
  - **Why**: Confirms database structure is correct.
  - **Verification Commands**:
    ```bash
    # Check table count and structure
    psql -U tbcv_user -d tbcv_prod -c "\dt"

    # Verify key tables exist
    psql -U tbcv_user -d tbcv_prod -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public';" | wc -l
    ```
  - **Expected Output**: All expected tables present

- [ ] Validate data integrity after migration
  - **Why**: Catches data corruption issues.
  - **Verification Commands**:
    ```bash
    # Check for null values in required columns
    psql -U tbcv_user -d tbcv_prod -c "SELECT * FROM table_name WHERE required_column IS NULL LIMIT 10;"

    # Verify record counts reasonable
    psql -U tbcv_user -d tbcv_prod -c "SELECT table_name, COUNT(*) FROM information_schema.tables GROUP BY table_name;"
    ```
  - **Expected Output**: No unexpected nulls, record counts reasonable

### Service Startup

- [ ] ⚠️ **Critical**: Start application API service
  - **Why**: Makes application available to users.
  - **Verification Commands**:
    ```bash
    # Start service
    systemctl start tbcv-api

    # Verify service started
    systemctl status tbcv-api

    # Check service logs for errors
    journalctl -u tbcv-api -n 50
    ```
  - **Expected Output**: Service is active and running
  - **Failure Handling**: Check logs, rollback if critical errors found

- [ ] Start background workers (if applicable)
  - **Why**: Background tasks need to be processing.
  - **Verification Commands**:
    ```bash
    # Start workers
    systemctl start tbcv-workers

    # Verify workers running
    ps aux | grep tbcv-worker
    ```
  - **Expected Output**: Worker processes running

- [ ] Verify API is responding to requests
  - **Why**: Confirms application is accepting connections.
  - **Verification Commands**:
    ```bash
    # Test API health endpoint
    curl -s http://localhost:8080/health | jq '.'

    # Test with timeout
    curl -s --connect-timeout 5 http://localhost:8080/health
    ```
  - **Expected Output**: HTTP 200 response with health data

- [ ] Enable monitoring and alerting
  - **Why**: Enables detection of issues during and after deployment.
  - **Verification Items**:
    - Monitoring dashboards accessible
    - Alerts configured and enabled
    - Log aggregation service running
    - Metrics collection working

- [ ] Verify no errors in application logs
  - **Why**: Application errors indicate deployment issues.
  - **Verification Commands**:
    ```bash
    # Check application logs
    tail -f /var/log/tbcv/api.log | grep -i error

    # Check for startup errors
    journalctl -u tbcv-api --since "1 hour ago" | grep -i error
    ```
  - **Expected Output**: No ERROR or CRITICAL level messages
  - **Failure Handling**: Investigate and resolve errors or rollback

### Health Checks

- [ ] ⚠️ **Critical**: Verify API endpoints responding correctly
  - **Why**: Confirms application is fully functional.
  - **Verification Commands**:
    ```bash
    # Check health endpoint
    curl -s http://localhost:8080/health

    # Check version endpoint
    curl -s http://localhost:8080/api/v1/version

    # Test with authentication (if applicable)
    curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/v1/validations
    ```
  - **Expected Output**: HTTP 200 responses with valid JSON data

- [ ] Verify database connectivity from application
  - **Why**: Application cannot function without database access.
  - **Verification Commands**:
    ```bash
    # Run database connectivity test
    python -c "from core.database import Database; db = Database(); print('DB Connected')"

    # Test database operations
    curl -s http://localhost:8080/api/v1/health | grep -i database
    ```
  - **Expected Output**: Database connection successful message

- [ ] Verify external service integrations (if applicable)
  - **Why**: Features depending on external services must be verified.
  - **Verification Items**:
    - Ollama LLM service connectivity (if enabled)
    - ChromaDB RAG service connectivity (if enabled)
    - Redis cache connectivity (if using Redis L2)
  - **Verification Commands**:
    ```bash
    # Test Ollama
    curl -s http://localhost:11434/api/status

    # Test ChromaDB
    curl -s http://localhost:8000/api/v1/heartbeat

    # Test Redis
    redis-cli ping
    ```

- [ ] Verify caching working correctly
  - **Why**: Cache improves performance; if broken, performance suffers.
  - **Verification Commands**:
    ```bash
    # Check cache statistics
    curl -s http://localhost:8080/api/v1/cache/stats

    # Verify cache entries
    redis-cli KEYS "tbcv:*" | head -20
    ```
  - **Expected Output**: Cache hit/miss statistics, cache entries present

- [ ] Load test with expected volume
  - **Why**: Verifies system handles production load.
  - **Verification Commands**:
    ```bash
    # Simple load test (5 concurrent requests)
    for i in {1..5}; do
      curl -s http://localhost:8080/health &
    done
    wait

    # More comprehensive load test (if using Apache Bench)
    ab -n 100 -c 10 http://localhost:8080/health
    ```
  - **Expected Output**: All requests succeed with acceptable response times

- [ ] Monitor resource utilization during load test
  - **Why**: Identifies performance bottlenecks.
  - **Verification Commands**:
    ```bash
    # Monitor CPU, memory, disk
    top -b -n 5 | head -20

    # Check application memory usage
    ps aux | grep python

    # Monitor disk I/O
    iostat -x 1 5
    ```
  - **Expected Output**: Resource usage within acceptable limits

---

## Post-Deployment Checklist

**Estimated Time**: 1-3 hours
**Purpose**: Validate deployment success and system stability

### Smoke Testing

- [ ] ⚠️ **Critical**: Run smoke test suite
  - **Why**: Validates all critical functionality works.
  - **Verification Commands**:
    ```bash
    # Run smoke tests
    pytest tests/smoke/ -v

    # Expected tests: Basic API calls, database ops, core features
    ```
  - **Expected Output**: All smoke tests pass
  - **Coverage**: Minimum 100% pass rate required
  - **Failure Handling**: Investigate failed tests, rollback if critical

- [ ] Test all critical user workflows
  - **Why**: Real-world usage patterns may differ from automated tests.
  - **Verification Items**:
    - Complete a validation workflow
    - Submit enhancement request
    - Retrieve recommendations
    - Execute approval workflow
    - Query analytics/reports
  - **Expected Output**: All workflows execute successfully

- [ ] Test API integrations
  - **Why**: External integrations must work with new version.
  - **Verification Items**:
    - Test authentication/authorization
    - Test rate limiting
    - Test error responses
    - Test pagination (if applicable)
  - **Verification Commands**:
    ```bash
    # Test with invalid auth
    curl -s http://localhost:8080/api/v1/validations -H "Authorization: Bearer invalid" -w "\n%{http_code}\n"

    # Should return 401 Unauthorized
    ```

- [ ] Test data access controls
  - **Why**: Ensures security controls are enforced.
  - **Verification Items**:
    - Verify users can only access their own data
    - Verify admin features restricted to admins
    - Verify audit logging working
  - **Expected Output**: Access controls enforced correctly

- [ ] Verify user-facing features
  - **Why**: UI must be fully functional.
  - **Verification Items** (if web UI deployed):
    - Dashboard loads without errors
    - Forms submit successfully
    - Real-time updates working (WebSocket)
    - Download functionality working

- [ ] Test error handling and edge cases
  - **Why**: Confirms graceful degradation.
  - **Verification Items**:
    - Invalid input properly rejected
    - Missing required fields handled
    - Timeout scenarios handled
    - Large dataset handling verified

### Monitoring Setup

- [ ] ⚠️ **Critical**: Verify monitoring dashboards accessible
  - **Why**: Operations team needs visibility.
  - **Verification Items**:
    - Monitoring dashboard URL works
    - Charts displaying data
    - All key metrics visible
  - **Expected Output**: Dashboards show current metrics

- [ ] Verify alerting rules active
  - **Why**: Alerts notify team of problems.
  - **Verification Items**:
    - CPU alert threshold set (e.g., >80%)
    - Memory alert threshold set (e.g., >85%)
    - Error rate alert set (e.g., >1%)
    - API response time alert set (e.g., >5s)
  - **Expected Output**: All alerts configured and active

- [ ] Test alert notification channels
  - **Why**: Confirms alerts reach appropriate team members.
  - **Verification Commands**:
    ```bash
    # Trigger test alert
    curl -X POST http://monitoring-system/api/test-alert -d '{"severity":"INFO", "message":"Test alert"}'
    ```
  - **Expected Output**: Alert received on Slack/email/PagerDuty

- [ ] Setup log aggregation
  - **Why**: Centralized logs enable faster troubleshooting.
  - **Verification Items**:
    - Log aggregation service running
    - Application logs being collected
    - Searchable and filterable
  - **Expected Output**: Recent logs visible in aggregation system

- [ ] Configure metrics collection
  - **Why**: Metrics essential for observability.
  - **Verification Items**:
    - Prometheus collecting metrics (if using)
    - Custom metrics for TBCV features
    - Metrics retention policy set
  - **Verification Commands**:
    ```bash
    # Check Prometheus targets
    curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'
    ```

- [ ] Setup performance baseline
  - **Why**: Enables detection of performance regressions.
  - **Verification Items**:
    - Response time baseline recorded
    - Throughput baseline recorded
    - Resource utilization baseline recorded
  - **Action**: Review docs/performance_baselines.md

- [ ] Configure log retention policies
  - **Why**: Prevents excessive disk usage.
  - **Verification Items**:
    - Log rotation configured (e.g., daily, 30-day retention)
    - Archived logs stored separately
    - Old logs automatically deleted

### Backup Verification

- [ ] ⚠️ **Critical**: Verify database backup completed successfully
  - **Why**: Confirms disaster recovery capability.
  - **Verification Commands**:
    ```bash
    # List recent backups
    ls -lh /backups/tbcv_db_backup* | tail -5

    # Verify backup integrity
    gzip -t /backups/tbcv_db_backup_latest.sql.gz
    ```
  - **Expected Output**: Recent backup file exists and is not corrupted

- [ ] ⚠️ **Critical**: Test backup restoration procedure
  - **Why**: Confirms disaster recovery actually works.
  - **Verification Commands**:
    ```bash
    # Create test database
    createdb -U postgres tbcv_test

    # Restore from backup
    gunzip < /backups/tbcv_db_backup_latest.sql.gz | psql -U postgres tbcv_test

    # Verify restored data
    psql -U postgres -d tbcv_test -c "SELECT COUNT(*) FROM table_name;"
    ```
  - **Expected Output**: Data restored successfully
  - **Cleanup**: Drop test database after verification

- [ ] Verify application files backup
  - **Why**: Confirms application can be recovered.
  - **Verification Commands**:
    ```bash
    # List backup files
    ls -lh /backups/tbcv_backup* | tail -5

    # Verify tar.gz integrity
    tar -tzf /backups/tbcv_backup_latest.tar.gz | head -20
    ```
  - **Expected Output**: Backup file exists and contains expected files

- [ ] Verify backup automation is scheduled
  - **Why**: Ongoing backups needed for disaster recovery.
  - **Verification Commands**:
    ```bash
    # Check cron jobs (Linux)
    crontab -l | grep backup

    # Or check Windows scheduled tasks
    schtasks /query | grep backup
    ```
  - **Expected Output**: Backup job scheduled to run regularly (e.g., daily)

- [ ] Document backup/recovery procedure
  - **Why**: Team needs to know how to recover from disaster.
  - **Action Items**:
    - Document backup command used
    - Document restore command
    - Document time estimates for restore
    - Document any special considerations
    - Store documentation in accessible location

### Documentation Updates

- [ ] Update deployment documentation with version details
  - **Why**: Documentation must reflect current deployment state.
  - **Verification Items**:
    - Version number updated
    - Deployment date recorded
    - Deployment environment documented
    - Configuration changes documented
    - Any known issues documented

- [ ] Update runbook with lessons learned
  - **Why**: Future deployments improved based on current experience.
  - **Verification Items**:
    - Any issues encountered documented
    - Workarounds documented
    - Time estimates updated if different
    - Success criteria documented

- [ ] Update troubleshooting guide with new issues encountered
  - **Why**: Enables faster resolution of future issues.
  - **Action**: Review docs/troubleshooting.md and add any new scenarios

- [ ] Update API documentation if changes made
  - **Why**: API consumers need accurate documentation.
  - **Verification Items**:
    - New endpoints documented
    - Endpoint changes documented
    - Authentication changes documented
  - **Verification**: Check docs/api_reference.md matches actual API

- [ ] Update architecture documentation if changes made
  - **Why**: Team needs to understand current system.
  - **Verification Items**:
    - Component changes documented
    - Flow changes documented
    - New integrations documented
  - **Verification**: Check docs/architecture.md aligns with current system

### Team Notification

- [ ] ⚠️ **Critical**: Send deployment completion notification
  - **Why**: Teams need to know deployment is complete.
  - **Action Items**:
    - Send email to stakeholders
    - Post to Slack/Teams
    - Include deployment summary:
      - Version deployed
      - Deployment time
      - Status (successful)
      - Known issues
      - Contact for questions

- [ ] Notify support team of changes
  - **Why**: Support needs to know what changed.
  - **Action Items**:
    - List of new features
    - List of bug fixes
    - List of breaking changes
    - Known limitations
    - Escalation procedures

- [ ] Update status page (if applicable)
  - **Why**: External users need status information.
  - **Action Items**:
    - Update deployment status to "Deployed"
    - Add brief summary of changes
    - Remove maintenance notice if any

- [ ] Schedule post-deployment review meeting
  - **Why**: Team reflects on deployment success.
  - **Action Items**:
    - Schedule for 1-2 weeks post-deployment
    - Invite team members
    - Prepare agenda
    - Discuss what went well and improvements

- [ ] Monitor application for 24 hours post-deployment
  - **Why**: Early detection of issues.
  - **Verification Items**:
    - Check error rates (should be < 0.1%)
    - Check response times (should be < 5s P99)
    - Check resource utilization (should be stable)
    - Check logs for anomalies
  - **Action**: Team member assigned to monitor for 24 hours

---

## Rollback Plan

**Purpose**: Procedures to revert failed deployment
**Estimated Time**: 30-60 minutes
**Trigger Points**: Use rollback if:
- Critical functionality broken
- Error rate exceeds 5%
- API response time exceeds 30s
- Database connectivity lost
- Data corruption detected
- Security vulnerability discovered

### Rollback Triggers

- [ ] **Critical System Failure**: API not responding
  - **Indicator**: Health check failing for >5 minutes
  - **Action**: Initiate rollback immediately

- [ ] **Data Corruption**: Data validation failures
  - **Indicator**: Database integrity checks failing
  - **Action**: Initiate rollback immediately

- [ ] **High Error Rate**: Application errors exceeding threshold
  - **Indicator**: Error rate > 5% for >5 minutes
  - **Action**: Initiate rollback immediately

- [ ] **Security Issue**: Vulnerability discovered in deployed code
  - **Indicator**: Security team notification
  - **Action**: Initiate rollback immediately

- [ ] **Database Migration Failure**: Schema mismatch
  - **Indicator**: Database migration errors in logs
  - **Action**: Initiate rollback immediately

- [ ] **Performance Degradation**: Response times unacceptable
  - **Indicator**: API response time > 30s P99 for >5 minutes
  - **Action**: Evaluate if rollback needed or if troubleshooting will resolve

### Rollback Steps

**Step 1: Stop Current Services**

- [ ] Stop application API service
  - **Command**: `systemctl stop tbcv-api`
  - **Verify**: `systemctl status tbcv-api` shows stopped
  - **Timeout**: 30 seconds max

- [ ] Stop background workers
  - **Command**: `systemctl stop tbcv-workers`
  - **Verify**: `ps aux | grep tbcv-worker` shows no processes

- [ ] Block incoming traffic (if using load balancer)
  - **Command**: Remove from load balancer health checks
  - **Expected**: All traffic routed to previous version

**Step 2: Restore Application Code**

- [ ] Restore previous version from backup
  - **Commands**:
    ```bash
    cd /opt
    tar -xzf tbcv_backup_previous.tar.gz

    # Or checkout previous tag
    cd /opt/tbcv
    git checkout v1.9.0  # Replace with previous version
    ```
  - **Verify**: `git describe --tags` shows previous version tag

- [ ] Reinstall dependencies for previous version
  - **Commands**:
    ```bash
    cd /opt/tbcv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
  - **Verify**: `pip list` shows previous version packages

- [ ] Restore previous configuration
  - **Commands**:
    ```bash
    cp /backups/config_previous.yaml config/main.yaml
    ```
  - **Verify**: `cat config/main.yaml | grep version`

**Step 3: Restore Database**

- [ ] ⚠️ **Critical**: Stop database operations
  - **Commands**:
    ```bash
    # Kill any connections to prevent corruption
    psql -U postgres -d tbcv_prod -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='tbcv_prod' AND pid != pg_backend_pid();"
    ```

- [ ] ⚠️ **Critical**: Restore database from backup
  - **Commands**:
    ```bash
    # Drop corrupted database
    dropdb -U postgres tbcv_prod

    # Restore from backup
    createdb -U postgres tbcv_prod
    gunzip < /backups/pre_migration_backup.sql.gz | psql -U postgres tbcv_prod

    # Verify restoration
    psql -U postgres -d tbcv_prod -c "SELECT COUNT(*) FROM migration_table;"
    ```
  - **Expected Output**: Database restored with previous schema
  - **Verify**: Record counts match pre-deployment

- [ ] Verify data integrity after restoration
  - **Commands**:
    ```bash
    # Check for integrity issues
    ANALYZE tbcv_prod

    # Verify key tables
    psql -U postgres -d tbcv_prod -c "\dt"
    ```

**Step 4: Restart Services**

- [ ] Start application API service
  - **Commands**:
    ```bash
    systemctl start tbcv-api
    systemctl status tbcv-api
    ```
  - **Verify**: Service status shows active/running
  - **Wait**: 30 seconds for service to fully start

- [ ] Start background workers
  - **Commands**:
    ```bash
    systemctl start tbcv-workers
    ps aux | grep tbcv-worker
    ```

- [ ] Enable traffic in load balancer
  - **Commands**: Add back to load balancer
  - **Verify**: Health checks passing

**Step 5: Verify Rollback Success**

- [ ] Verify API responding to requests
  - **Commands**:
    ```bash
    curl -s http://localhost:8080/health
    curl -s http://localhost:8080/api/v1/version
    ```
  - **Expected Output**: HTTP 200, version shows previous version

- [ ] Verify database connectivity
  - **Commands**:
    ```bash
    python -c "from core.database import Database; db = Database(); print('DB Connected')"
    ```

- [ ] Verify no errors in logs
  - **Commands**:
    ```bash
    journalctl -u tbcv-api --since "5 minutes ago" | grep -i error
    ```
  - **Expected Output**: No ERROR level messages

- [ ] Run smoke tests
  - **Commands**:
    ```bash
    pytest tests/smoke/ -v
    ```
  - **Expected Output**: All smoke tests pass

### Data Recovery

- [ ] ⚠️ **Critical**: Assess data loss
  - **Action**: Compare current database with backup
  - **Questions to answer**:
    - What data was lost?
    - How many records affected?
    - Is loss acceptable?
    - Can users re-submit data?

- [ ] Notify affected users
  - **Action Items**:
    - Send email to affected users
    - Explain what happened
    - Explain recovery steps
    - Provide support contact

- [ ] Implement data recovery procedure (if needed)
  - **Options**:
    1. Restore specific records from backup
    2. Request users resubmit data
    3. Merge data from partial backup
  - **Commands** (if restoring specific records):
    ```bash
    # Export specific records from backup
    pg_restore --table=table_name /backups/backup.sql > table_data.sql

    # Import into current database
    psql -U tbcv_user -d tbcv_prod < table_data.sql
    ```

- [ ] Verify data recovery complete
  - **Commands**: Query affected records to confirm

### Communication Plan

- [ ] ⚠️ **Critical**: Notify stakeholders of rollback
  - **Action Items**:
    - Send email to all stakeholders
    - Include:
      - Rollback completion time
      - Reason for rollback
      - Status (system back to normal)
      - Data impact (if any)
      - Contact for questions
    - Post to Slack/Teams
    - Update status page

- [ ] Notify support team
  - **Action Items**:
    - Brief support team on what happened
    - Provide talking points for customers
    - Set up escalation path
    - Schedule post-rollback review

- [ ] Schedule root cause analysis meeting
  - **Action Items**:
    - Schedule for within 24 hours of rollback
    - Invite engineering, ops, and product teams
    - Prepare detailed timeline
    - Document lessons learned

- [ ] Update public status page
  - **Action Items**:
    - Update status to "Resolved"
    - Provide brief explanation
    - Include resolution time
    - Link to incident report (if sharing externally)

---

## Environment-Specific Checklists

### Development Deployment

**Purpose**: Deploy TBCV to development environment for testing
**Frequency**: Daily or on-demand
**Downtime Acceptable**: Yes

- [ ] Create feature branch from main
  - **Command**: `git checkout -b feature/your-feature main`

- [ ] Verify Python 3.8+ installed
  - **Command**: `python --version`

- [ ] Create virtual environment
  - **Commands**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

- [ ] Install dependencies
  - **Command**: `pip install -r requirements.txt -e .[dev]`

- [ ] Set development configuration
  - **Items**:
    - `system.environment: "development"`
    - `system.debug: true`
    - `system.log_level: "debug"`
    - `server.host: "localhost"`
    - `server.port: 8080`

- [ ] Initialize SQLite database
  - **Commands**:
    ```bash
    rm -f data/tbcv.db
    alembic upgrade head
    ```

- [ ] Start application
  - **Command**: `python -m tbcv`

- [ ] Verify API responding
  - **Command**: `curl http://localhost:8080/health`

- [ ] Run tests
  - **Command**: `pytest tests/ -v`

- [ ] Run linting
  - **Commands**:
    ```bash
    black --check svc/ core/ api/ cli/
    flake8 svc/ core/ api/ cli/
    mypy svc/ core/
    ```

**Estimated Time**: 15-30 minutes

---

### Staging Deployment

**Purpose**: Deploy TBCV to staging for final validation before production
**Frequency**: Before each production release
**Downtime Acceptable**: No (should be minimized)

- [ ] Perform full pre-deployment checklist
  - **Sections**: All items in Pre-Deployment Checklist above

- [ ] Use staging database (PostgreSQL recommended)
  - **Configuration**: Point to staging PostgreSQL instance

- [ ] Enable full monitoring
  - **Items**: Metrics, logs, alerts all active

- [ ] Run full test suite including integration tests
  - **Command**: `pytest tests/ -v --cov --cov-report=html`

- [ ] Run performance tests
  - **Command**: `pytest tests/performance/ -v`

- [ ] Test disaster recovery
  - **Action**: Simulate database failure and recovery

- [ ] Load test with realistic volume
  - **Tools**: Apache Bench, JMeter, or custom script

- [ ] User acceptance testing (UAT)
  - **Action**: Have business stakeholders verify features

- [ ] Security testing
  - **Commands**:
    ```bash
    safety check
    bandit -r svc/ core/ api/ cli/
    ```

- [ ] Verify all monitoring working
  - **Items**: Dashboards, alerts, logs all visible

**Estimated Time**: 4-8 hours

---

### Production Deployment

**Purpose**: Deploy TBCV to production for customer use
**Frequency**: Quarterly or as needed
**Downtime Acceptable**: No (must minimize)

- [ ] ⚠️ **Critical**: Complete entire deployment checklist above
  - **Sections**: Pre-Deployment, Deployment, Post-Deployment

- [ ] ⚠️ **Critical**: Execute from change control process
  - **Items**:
    - Change request approved
    - Stakeholder sign-off obtained
    - Maintenance window scheduled
    - Rollback plan reviewed

- [ ] ⚠️ **Critical**: Production database with full backups
  - **Items**:
    - PostgreSQL with replication (if available)
    - Automated daily backups
    - Weekly backup tested
    - Point-in-time recovery configured

- [ ] ⚠️ **Critical**: Full security hardening applied
  - **Items**:
    - HTTPS/TLS enabled
    - Authentication configured
    - Rate limiting enabled
    - Access control verified
    - Secrets in environment variables

- [ ] ⚠️ **Critical**: Production monitoring configured
  - **Items**:
    - Real-time dashboards active
    - Alerts configured for all thresholds
    - Log aggregation collecting all logs
    - Metrics collection active
    - On-call rotation in place

- [ ] ⚠️ **Critical**: Deployment during low-traffic window
  - **Items**:
    - Scheduled for off-peak time
    - All teams aware
    - Support team standing by
    - On-call engineer assigned

- [ ] ⚠️ **Critical**: 24-hour post-deployment monitoring
  - **Items**:
    - Dedicated person monitoring for 24 hours
    - Alert response procedures activated
    - Support team available for escalations
    - Daily check-in during first week

**Estimated Time**: 8-16 hours (including pre/post)

---

### Disaster Recovery Deployment

**Purpose**: Restore TBCV from disaster (major failure)
**Frequency**: As needed (hopefully never)
**Expected Downtime**: 1-4 hours depending on scenario

**Prerequisites**:
- Backup files intact and accessible
- Backup servers available
- Team members available for recovery
- Communication channels working

**Step-by-Step Procedure**:

1. **Assess Situation** (15 minutes)
   - Determine what failed
   - Identify data loss scope
   - Verify backup availability
   - Notify stakeholders

2. **Restore From Backup** (30-45 minutes)
   - Deploy application code from latest backup
   - Restore database from latest backup
   - Verify data integrity
   - Test connectivity

3. **Verify System** (15-30 minutes)
   - Run smoke tests
   - Verify critical functionality
   - Check monitoring and alerts
   - Test backup systems

4. **Full Recovery Validation** (30-60 minutes)
   - Run complete test suite
   - User acceptance testing
   - Performance validation
   - Security verification

5. **Post-Recovery** (Ongoing)
   - Monitor closely for 24 hours
   - Implement preventive measures
   - Update disaster recovery documentation
   - Schedule post-incident review

**Key Contacts**:
- On-call engineer: [Phone/Email]
- Operations manager: [Phone/Email]
- Database administrator: [Phone/Email]
- CTO/Technical lead: [Phone/Email]

---

## Summary Table

| Phase | Duration | Critical Items | Verification Method |
|-------|----------|-----------------|---------------------|
| Pre-Deployment | 2-4h | System/DB/Security checks | Manual verification + scripts |
| Deployment | 1-2h | Code/DB deployment | Service status checks |
| Post-Deployment | 1-3h | Smoke tests/Monitoring | Test execution + dashboard review |
| Rollback (if needed) | 30-60m | Data restoration | Service restart + data validation |
| **Development** | 15-30m | None (non-prod) | Tests + linting |
| **Staging** | 4-8h | All integration tests | Full test suite + UAT |
| **Production** | 8-16h | All critical items | Change control + monitoring |
| **Disaster Recovery** | 1-4h | Data restoration | Backup validation |

---

## Appendix: Common Issues and Solutions

### Issue: Database Migration Fails

**Symptoms**: Alembic upgrade errors, schema mismatch

**Resolution**:
1. Check migration files exist: `ls alembic/versions/`
2. Verify database connection: `psql -U user -d database -c "SELECT 1;"`
3. Check for locks: `psql -c "SELECT * FROM pg_stat_activity;"`
4. Downgrade if needed: `alembic downgrade -1`
5. Review migration code for syntax errors

---

### Issue: API Not Starting

**Symptoms**: Service fails to start, logs show errors

**Resolution**:
1. Check configuration: `python -c "from core.config import Config; Config()"`
2. Verify dependencies: `pip check`
3. Check port not in use: `lsof -i :8080`
4. Review logs: `journalctl -u tbcv-api -n 50`
5. Test with manual start: `python -m tbcv`

---

### Issue: Database Connection Timeout

**Symptoms**: Connection pool exhausted, slow queries

**Resolution**:
1. Check database load: `psql -c "SELECT count(*) FROM pg_stat_activity;"`
2. Kill idle connections: `psql -c "SELECT pg_terminate_backend(pid) FROM ..."`
3. Increase connection pool size in config
4. Verify database server resources
5. Check network connectivity

---

---

## Post-Deployment Verification

### API Endpoint Verification

- [ ] **Health Endpoints Responding**
  - [ ] Liveness endpoint responds
  - Verification: `curl http://localhost:8080/health/live`
  - Expected: `{"status": "live"}` or similar
  - Timeout: 5 seconds

- [ ] **Readiness Endpoint Responding**
  - [ ] Readiness endpoint responds
  - Verification: `curl http://localhost:8080/health/ready`
  - Expected: `{"status": "ready"}` or similar
  - Timeout: 5 seconds

- [ ] **API Documentation Accessible**
  - [ ] Swagger UI available
  - Verification: Open browser to `http://localhost:8080/docs`
  - Expected: Interactive API documentation displayed

- [ ] **Health Status Details Available**
  - [ ] Detailed health information endpoint
  - Verification: `curl http://localhost:8080/health`
  - Expected: Comprehensive health status with component details

### Validation Workflow Testing

- [ ] **Validation Workflow Functional**
  - [ ] Single file validation works
  - Verification: `curl -X POST http://localhost:8080/api/validate` with test file
  - Expected: Validation result returned with no errors

- [ ] **Fuzzy Detection Working**
  - [ ] Plugin patterns detected in content
  - [ ] Confidence scores assigned
  - Verification: Run validation on file with plugin references
  - Expected: Fuzzy matches detected

- [ ] **Truth Validation Working**
  - [ ] Truth data validation rules applied
  - [ ] Unknown plugins flagged
  - Verification: Test with invalid plugin names
  - Expected: Appropriate errors/warnings

- [ ] **Enhancement Workflow Functional**
  - [ ] Recommendations can be generated
  - [ ] Enhancement can be applied
  - Verification: Test enhancement endpoint
  - Expected: Enhanced content returned without errors

### Performance Baseline

- [ ] **Response Time Within Acceptable Range**
  - [ ] Small files: < 300ms
  - [ ] Medium files: < 1000ms
  - [ ] Large files: < 3000ms
  - Verification: Time multiple validation requests
  - Expected: Response times within targets

- [ ] **Memory Usage Stable**
  - [ ] No memory leaks detected
  - [ ] Memory usage stable over time
  - Verification: Monitor process memory for 5+ minutes
  - Expected: Memory stable, not continuously increasing

- [ ] **CPU Usage Reasonable**
  - [ ] CPU usage below configured limit
  - [ ] No runaway processes
  - Verification: Monitor CPU usage during validation
  - Expected: CPU usage spikes for validation, returns to baseline

---

## Troubleshooting Common Issues

### Port Already in Use

**Issue**: Application fails to start on configured port

```bash
# Find process using port
lsof -i :8080                    # Linux/macOS
netstat -tulpn | grep :8080      # Linux
netstat -ano | findstr :8080     # Windows

# Kill process (force)
kill -9 <PID>                    # Linux/macOS
taskkill /PID <PID> /F           # Windows
```

**Resolution**:
- Change configured port in config/main.yaml
- Or kill the process using the port
- Or wait for the process to release the port

---

### Database Connection Failed

**Issue**: Application cannot connect to database

```bash
# Test connection
python -c "from core.database import db_manager; print(db_manager.is_connected())"

# Check database file
ls -la data/tbcv.db

# Verify permissions
stat data/tbcv.db
```

**Resolution**:
- Check DATABASE_URL environment variable
- Verify database file exists and is readable
- Check file permissions (should be 600)
- Reinitialize database if corrupted

---

### Memory Issues

**Issue**: Application consuming excessive memory or crashing

```bash
# Monitor memory usage
htop                             # Linux/macOS
ps aux --sort=-%mem | head       # Linux
Get-Process | Sort-Object PM -Descending | Select-Object -First 10  # Windows

# Check system memory
free -h                          # Linux
vm_stat                          # macOS
Get-ComputerInfo | Select CSMemory  # Windows
```

**Resolution**:
- Reduce `max_concurrent_workflows` in config
- Disable L1 cache if memory constrained
- Reduce cache sizes in config/cache.yaml
- Add more RAM to system if possible

---

### Slow Performance

**Issue**: Validation requests taking longer than expected

```bash
# Monitor system resources
vmstat 1                         # Linux
iostat -x 1                      # Linux disk I/O
top                              # Linux/macOS

# Check application logs for slow queries
grep "processing_time_ms" data/logs/tbcv.log | sort -n | tail -20

# Profile application
python -m cProfile -s cumtime -m cli.main validate-file test.md
```

**Resolution**:
- Increase `worker_pool_size` in config
- Enable caching if disabled
- Check for slow database queries
- Profile application to find bottlenecks

---

### LLM Service Unavailable

**Issue**: Ollama not responding or LLM validation fails

```bash
# Check if Ollama running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Pull required model
ollama pull qwen2.5

# Check logs
tail -f data/logs/tbcv.log | grep -i ollama
```

**Resolution**:
- Start Ollama service
- Pull required model
- Disable LLM validation if not needed (set enabled: false in config)
- Check network connectivity to Ollama

---

### Corrupted Database

**Issue**: Database locked or corruption detected

```bash
# Check database integrity
sqlite3 data/tbcv.db "PRAGMA integrity_check;"

# Backup corrupted database
cp data/tbcv.db data/tbcv.db.corrupted

# Restore from backup
cp data/tbcv_backup.db data/tbcv.db
```

**Resolution**:
- Restore from backup if available
- Reinitialize database if no backup
- Note: Reinitialization will lose data

---

### Configuration Not Loading

**Issue**: Configuration changes not taking effect

```bash
# Verify configuration file syntax
python -c "import yaml; yaml.safe_load(open('config/main.yaml'))" && echo "Valid"

# Check environment variable precedence
env | grep TBCV_

# Verify configuration is being loaded
python -c "from core.config_loader import ConfigLoader; c = ConfigLoader(); print(c.load_config('config/main.yaml'))"
```

**Resolution**:
- Check YAML syntax in config files
- Verify environment variables are set correctly
- Restart application to load new configuration
- Check configuration file permissions

---

## Verification Commands Reference

### System Information

```bash
# Python version
python --version

# Installed packages
pip list

# System memory
free -h                         # Linux
vm_stat                         # macOS

# Disk space
df -h .

# Network connectivity
ping google.com
```

### TBCV Specific

```bash
# Initialize database
python -c "from core.database import db_manager; db_manager.initialize_database()"

# Check database connection
python -c "from core.database import db_manager; print(db_manager.is_connected())"

# Load configuration
python -c "from core.config_loader import ConfigLoader; c = ConfigLoader(); print(c.load_config('config/main.yaml'))"

# Test validation
python -m cli.main validate-file test.md --family words

# Check application status
curl http://localhost:8080/admin/status

# View health status
curl http://localhost:8080/health
```

### Monitoring Commands

```bash
# Real-time logs
tail -f data/logs/tbcv.log

# Filter error logs
grep "ERROR" data/logs/tbcv.log

# JSON log parsing
cat data/logs/tbcv.log | jq .

# Count validations
grep "validations_total" data/logs/tbcv.log | wc -l

# Performance analysis
grep "processing_time_ms" data/logs/tbcv.log | jq '.processing_time_ms' | awk '{sum+=$1; count++} END {print "Average:", sum/count, "ms"}'

# Monitor database
sqlite3 data/tbcv.db "SELECT COUNT(*) FROM workflows;"

# Check cache size
du -h data/cache/
```

### Backup and Recovery

```bash
# Database backup
sqlite3 data/tbcv.db ".backup data/backup_$(date +%Y%m%d_%H%M%S).db"

# Configuration backup
tar -czf config_backup_$(date +%Y%m%d_%H%M%S).tar.gz config/

# Restore database
cp data/backup_YYYYMMDD_HHMMSS.db data/tbcv.db

# Restore configuration
tar -xzf config_backup_YYYYMMDD_HHMMSS.tar.gz
```

---

## Related Documentation

- [Deployment Guide](deployment.md) - Detailed deployment procedures
- [Configuration Guide](configuration.md) - Complete configuration reference
- [Troubleshooting Guide](troubleshooting.md) - Extended troubleshooting
- [Production Readiness](production_readiness.md) - Production best practices
- [Architecture Documentation](architecture.md) - System design details
- [Security Documentation](security.md) - Security configuration and best practices

---

## Checklist Usage Tips

1. **Print and Use**: Print this checklist for each deployment
2. **Team Coordination**: Assign items to team members
3. **Sign-Off**: Have authorized person sign off on each phase
4. **Document Issues**: Record any issues encountered
5. **Update Template**: Refine checklist based on deployment experience
6. **Version Control**: Keep updated checklist in version control

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2024-12-05 | Enhanced comprehensive deployment checklist with additional sections and improvements |
| 1.0 | 2024-12-03 | Initial deployment checklist |

---

*Last Updated: 2024-12-05*
*Applicable to: TBCV v2.0.0+*
