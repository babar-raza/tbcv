# TBCV Security Best Practices Guide

**Version 1.0.0** | Comprehensive Security Hardening for TBCV Deployments

## Table of Contents

1. [Overview](#overview)
2. [Access Control](#access-control)
3. [Network Security](#network-security)
4. [Data Security](#data-security)
5. [Application Security](#application-security)
6. [Authentication & Session Management](#authentication--session-management)
7. [Dependency Security](#dependency-security)
8. [Deployment Security](#deployment-security)
9. [Monitoring & Incident Response](#monitoring--incident-response)
10. [Security Checklist](#security-checklist)

---

## 1. Overview

### Security Principles for TBCV

TBCV is a content validation and enhancement system that processes sensitive technical documentation. The system must enforce strict security controls to:

1. **Protect business logic** from unauthorized access
2. **Prevent data breaches** of sensitive content
3. **Ensure data integrity** through validation and audit trails
4. **Maintain compliance** with security standards and regulations
5. **Enable safe deployment** in production environments

### Core Security Principles

- **Defense in Depth**: Multiple overlapping security layers
- **Least Privilege**: Components only access what they need
- **Fail-Safe Defaults**: Secure by default, opt-in for flexibility
- **Separation of Concerns**: Clear architectural boundaries enforced at runtime
- **Audit Trail**: Complete logging of all operations for compliance
- **Zero Trust**: Verify all access requests, assume breach

### Threat Model

**Potential Threats:**

| Threat | Impact | Mitigation |
|--------|--------|-----------|
| Unauthorized API/CLI access to business logic | High | Dual-layer access control (Import + Runtime guards) |
| Direct module imports bypassing MCP layer | High | Import-time guard via `sys.meta_path` hooks |
| SQL injection via content validation | High | SQLAlchemy parameterized queries |
| Cross-site scripting (XSS) in web dashboard | High | Bleach HTML sanitization, templating engine escaping |
| Path traversal in file operations | High | Path validation, directory traversal prevention |
| Sensitive data exposure in logs | Medium | Log filtering, redaction patterns |
| Unauthorized file system access | High | Restricted base directories, access control |
| Compromised dependencies | Medium | Vulnerability scanning, version pinning |
| Brute force attacks on API | Medium | Rate limiting, request throttling |
| Configuration exposure | Medium | Secrets management, environment variables |
| Unencrypted data in transit | High | HTTPS/TLS enforcement, secure protocols |
| Unencrypted data at rest | Medium | Database encryption, backup security |

### Security Layers

TBCV implements five primary security layers working together:

```
┌─────────────────────────────────────────────────────────┐
│  Layer 5: Audit & Compliance                            │
│  - Logging, monitoring, incident response, compliance   │
└─────────────────────────────────────────────────────────┘
                         ▲
┌─────────────────────────────────────────────────────────┐
│  Layer 4: Application Security                          │
│  - Input validation, output encoding, CSRF protection   │
└─────────────────────────────────────────────────────────┘
                         ▲
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Access Control                                │
│  - Dual-layer guards, MCP-first architecture, RBAC      │
└─────────────────────────────────────────────────────────┘
                         ▲
┌─────────────────────────────────────────────────────────┐
│  Layer 2: Network Security                              │
│  - HTTPS/TLS, rate limiting, CORS, firewall rules       │
└─────────────────────────────────────────────────────────┘
                         ▲
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Infrastructure Security                       │
│  - OS hardening, service account privileges, encryption │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Access Control

### Overview

TBCV enforces strict access control through a dual-layer system preventing direct access to business logic from CLI and API layers. All access must flow through the MCP (Model Context Protocol) server layer.

### Dual-Layer Access Control System

#### Layer 1: Import-Time Guard

**Purpose**: Prevent unauthorized modules from importing protected business logic

**Mechanism**: Python `sys.meta_path` hook installed at application startup

**Protected Modules** (by default):
```python
{
    "agents.orchestrator",
    "agents.content_validator",
    "agents.content_enhancer",
    "agents.recommendation_agent",
    "agents.truth_manager",
    "agents.validators",
    "core.validation_store",
    "core.database"
}
```

**Allowed Importers**:
- `svc.mcp_server` - MCP server layer
- `svc.mcp_methods` - MCP method implementations
- `tests` - Test code

**Blocked Importers**:
- `api` - REST API endpoints
- `cli` - CLI commands

**Configuration**:

```bash
# Enable enforcement (via environment variable)
export TBCV_IMPORT_GUARD_MODE=block

# Or set in code during startup
from core.import_guard import install_import_guards, set_enforcement_mode
install_import_guards()
set_enforcement_mode("block")
```

#### Layer 2: Runtime Access Guard

**Purpose**: Prevent direct function calls from unauthorized contexts

**Mechanism**: Stack inspection via `@guarded_operation` decorator

**Implementation Pattern**:

```python
from core.access_guard import guarded_operation

@guarded_operation
def validate_content(file_path: str, content: str) -> ValidationResult:
    """
    Protected entry point - MCP access only.

    Allowed callers:
    - MCP server (svc/mcp_server.py)
    - MCP methods (svc/mcp_methods/*)
    - Tests (tests/*)

    Blocked callers:
    - API endpoints (api/*)
    - CLI commands (cli/*)
    """
    return perform_validation(file_path, content)
```

**Enforcement Modes**:

| Mode | Behavior | Use Case |
|------|----------|----------|
| DISABLED | No enforcement, all access allowed | Local development |
| WARN | Log violations, allow access | Staging/monitoring |
| BLOCK | Log violations, raise errors | Production |

### Configuration Examples

#### Production Configuration (config/access_guards.yaml)

```yaml
# PRODUCTION: Strict enforcement mode
enforcement_mode: block

protected_modules:
  - agents.orchestrator
  - agents.content_validator
  - agents.content_enhancer
  - agents.recommendation_agent
  - agents.truth_manager
  - agents.validators
  - core.validation_store
  - core.database
  - core.checkpoint_manager

allowed_callers:
  - svc.mcp_server
  - svc.mcp_methods
  - tests

blocked_callers:
  - api
  - cli

logging:
  log_violations: true
  log_level: ERROR
  include_stack_trace: true
  include_source_code: false

performance:
  track_overhead: true
  max_overhead_ms: 1.0
```

#### Development Configuration

```yaml
# DEVELOPMENT: Disabled enforcement
enforcement_mode: disabled

logging:
  log_violations: true
  log_level: DEBUG
  include_stack_trace: true
  include_source_code: true
```

#### Staging Configuration

```yaml
# STAGING: Warning mode for monitoring
enforcement_mode: warn

logging:
  log_violations: true
  log_level: WARNING
  include_stack_trace: true
  include_source_code: false
```

### Role-Based Access Patterns

**Admin Role** (Full Access):
- Can perform all operations
- Can approve/reject recommendations
- Can manage system configuration
- Can view audit logs

```python
@app.post("/admin/approve-recommendation")
async def admin_approve_recommendation(
    rec_id: str,
    approved_by: str,
    request: Request
):
    # Verify admin role
    if not verify_admin_role(request.user):
        raise HTTPException(status_code=403, detail="Admin role required")

    # Process approval
    mcp_client = MCPClient()
    return await mcp_client.call_tool("approve_recommendation", {
        "recommendation_id": rec_id,
        "approved_by": approved_by
    })
```

**Reviewer Role** (Limited Approval):
- Can review and approve recommendations
- Cannot modify configuration
- Cannot access admin endpoints

```python
@app.post("/review/approve-recommendation")
async def reviewer_approve(
    rec_id: str,
    status: str,
    request: Request
):
    # Verify reviewer role
    if not verify_reviewer_role(request.user):
        raise HTTPException(status_code=403, detail="Reviewer role required")

    # Only allow approve/reject, not override
    if status not in ["accepted", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    mcp_client = MCPClient()
    return await mcp_client.call_tool("review_recommendation", {
        "recommendation_id": rec_id,
        "status": status
    })
```

**Viewer Role** (Read-Only):
- Can view validation results
- Can view recommendations
- Cannot approve or modify anything

```python
@app.get("/api/recommendations")
async def list_recommendations(
    validation_id: str,
    request: Request
):
    # Verify any authenticated user (viewer+ role)
    if not request.user:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Return recommendations (filtering already done by MCP)
    mcp_client = MCPClient()
    return await mcp_client.call_tool("get_recommendations", {
        "validation_id": validation_id
    })
```

### API Authentication & Authorization

#### HTTP Header-Based Authentication

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify API key from X-API-Key header."""
    if not is_valid_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.post("/api/validate")
async def validate_endpoint(
    request: ValidationRequest,
    api_key: str = Depends(verify_api_key)
):
    # API key is valid, proceed
    mcp_client = MCPClient()
    return await mcp_client.call_tool("validate_file", {
        "file_path": request.file_path,
        "content": request.content,
        "family": request.family
    })
```

#### JWT Token Authentication

```python
from fastapi import HTTPException
from jose import JWTError, jwt
from datetime import datetime

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

async def verify_token(token: str = Header(..., alias="Authorization")) -> str:
    """Verify JWT token from Authorization header."""
    try:
        # Remove "Bearer " prefix
        if token.startswith("Bearer "):
            token = token[7:]

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/validate")
async def validate_endpoint(
    request: ValidationRequest,
    user_id: str = Depends(verify_token)
):
    # User is authenticated, proceed
    mcp_client = MCPClient()
    return await mcp_client.call_tool("validate_file", {
        "file_path": request.file_path,
        "content": request.content,
        "family": request.family,
        "user_id": user_id
    })
```

---

## 3. Network Security

### HTTPS/TLS Configuration

**Production HTTPS Setup**:

```python
# main.py
import ssl
import uvicorn

def main():
    # Load SSL certificates
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(
        certfile="/path/to/cert.pem",
        keyfile="/path/to/key.pem"
    )

    # Minimum TLS 1.2
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

    # Strong cipher suites only
    ssl_context.set_ciphers(
        'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL'
    )

    # Run with SSL
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8443,
        ssl_keyfile="/path/to/key.pem",
        ssl_certfile="/path/to/cert.pem",
        ssl_version=ssl.PROTOCOL_TLSv1_2,
        ssl_cert_reqs=ssl.CERT_NONE,
        ssl_ciphers='ECDHE+AESGCM:ECDHE+CHACHA20:!aNULL'
    )
```

**Let's Encrypt Integration** (Recommended for automatic renewal):

```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Get certificate
certbot certonly --standalone -d yourdomain.com

# Auto-renew (add to crontab)
0 0 1 * * certbot renew --quiet
```

**HSTS Configuration** (Force HTTPS):

```python
from fastapi.middleware import Middleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.hsts import HSTSMiddleware

app = FastAPI(
    middleware=[
        Middleware(HTTPSRedirectMiddleware),
        Middleware(
            HSTSMiddleware,
            max_age=31536000,  # 1 year
            include_subdomains=True,
            preload=True
        )
    ]
)
```

### Firewall Rules

**Recommended Firewall Configuration** (iptables/firewalld):

```bash
# Allow only HTTPS inbound
sudo firewall-cmd --permanent --add-port=8443/tcp
sudo firewall-cmd --permanent --remove-port=8080/tcp

# Restrict to specific IPs if possible
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="203.0.113.0/24" port protocol="tcp" port="8443" accept'

# Block all other traffic
sudo firewall-cmd --permanent --set-default-zone=drop
sudo firewall-cmd --reload
```

**AWS Security Group Example**:

```yaml
# Ingress rules
- IpProtocol: tcp
  FromPort: 443
  ToPort: 443
  CidrIp: 0.0.0.0/0
  Description: "HTTPS from anywhere"

- IpProtocol: tcp
  FromPort: 8443
  ToPort: 8443
  CidrIp: 10.0.0.0/8
  Description: "TBCV API from VPC only"

# Egress rules
- IpProtocol: tcp
  FromPort: 443
  ToPort: 443
  CidrIp: 0.0.0.0/0
  Description: "HTTPS to internet (for updates)"
```

### Port Security

**Default Ports**:
- 8443: HTTPS API (production)
- 8080: HTTP API (development only)
- 8000: Alternative HTTP port (if needed)

**Secure Port Configuration**:

```python
import os

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    HOST = "0.0.0.0"
    PORT = 8443  # HTTPS only
    RELOAD = False
    SSL_ENABLED = True
elif ENVIRONMENT == "staging":
    HOST = "0.0.0.0"
    PORT = 8443
    RELOAD = False
    SSL_ENABLED = True
else:  # development
    HOST = "127.0.0.1"  # Localhost only
    PORT = 8080  # HTTP acceptable for local dev
    RELOAD = True
    SSL_ENABLED = False
```

### API Rate Limiting

**SlowAPI Integration** (FastAPI rate limiting):

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"}
    )

# Apply rate limits to endpoints
@app.post("/api/validate")
@limiter.limit("10/minute")  # 10 requests per minute
async def validate_endpoint(request: Request, data: ValidationRequest):
    return await mcp_client.call_tool("validate_file", {...})

# Stricter limit for expensive operations
@app.post("/api/validate-directory")
@limiter.limit("2/minute")  # 2 requests per minute
async def validate_directory(request: Request, data: DirectoryValidationRequest):
    return await mcp_client.call_tool("validate_directory", {...})

# Very strict for admin operations
@app.post("/admin/reset-cache")
@limiter.limit("1/hour")  # 1 request per hour
async def admin_reset_cache(request: Request):
    return await mcp_client.call_tool("reset_cache", {})
```

**Custom Rate Limiting per Client**:

```python
from slowapi.rates import RateLimit

def get_rate_limit(api_key: str) -> str:
    """Return different rate limits based on API key tier."""
    user_tier = get_user_tier(api_key)

    if user_tier == "premium":
        return "100/minute"
    elif user_tier == "standard":
        return "20/minute"
    else:
        return "5/minute"

@app.post("/api/validate")
async def validate_endpoint(
    request: Request,
    data: ValidationRequest,
    api_key: str = Depends(verify_api_key)
):
    # Apply custom rate limit based on API key
    rate_limit = get_rate_limit(api_key)
    # ... (apply rate limit)

    return await mcp_client.call_tool("validate_file", {...})
```

### CORS Configuration

**Strict CORS Setup** (Production):

```python
from fastapi.middleware.cors import CORSMiddleware

# Production: Only allow specific trusted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://app.yourdomain.com",
        "https://api.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-API-Key",
        "X-Request-ID"
    ],
    expose_headers=["X-Request-ID"],
    max_age=3600
)
```

**Development CORS Configuration** (Flexibility for testing):

```python
# Development: Allow localhost variations
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

**Environment-Based Configuration**:

```python
import os
from fastapi.middleware.cors import CORSMiddleware

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    allowed_origins = [
        "https://yourdomain.com",
        "https://app.yourdomain.com"
    ]
    allow_methods = ["GET", "POST", "PUT", "DELETE"]
    allow_credentials = True
    max_age = 3600
else:  # development/staging
    allowed_origins = ["*"]
    allow_methods = ["*"]
    allow_credentials = True
    max_age = 86400

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=allow_methods,
    allow_headers=["*"],
    max_age=max_age
)
```

---

## 4. Data Security

### Database Encryption at Rest

**SQLite Encryption** (SQLCipher):

```bash
# Install SQLCipher
pip install sqlcipher3

# Create encrypted database
from sqlcipher3 import dbapi2 as sqlite

conn = sqlite.connect(':memory:')
conn.execute("PRAGMA key = 'password'")
conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
```

**SQLAlchemy with SQLCipher**:

```python
from sqlalchemy import create_engine

# SQLite with encryption enabled via connection string
engine = create_engine(
    'sqlite+pysqlcipher:///:memory:',
    connect_args={
        'check_same_thread': False,
        'timeout': 30,
        'uri': True
    },
    echo=False
)

# Or with database file
engine = create_engine(
    'sqlite+pysqlcipher:////path/to/tbcv.db',
    connect_args={
        'passphrase': os.getenv('DB_ENCRYPTION_KEY'),
        'check_same_thread': False
    }
)
```

**PostgreSQL Encryption**:

```python
# PostgreSQL with pgcrypto extension
from sqlalchemy import create_engine

engine = create_engine(
    'postgresql://user:password@localhost/tbcv',
    echo=False,
    pool_size=10,
    max_overflow=20
)

# Enable pgcrypto extension on first connection
with engine.begin() as conn:
    conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

# Encrypt sensitive columns
from sqlalchemy.types import TypeDecorator
from sqlalchemy import String
import os

class EncryptedString(TypeDecorator):
    """Encrypted string column type."""
    impl = String

    def process_bind_param(self, value, dialect):
        if value is not None:
            return f"pgp_sym_encrypt('{value}', '{os.getenv('DB_ENCRYPTION_KEY')}')"
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return f"pgp_sym_decrypt({value}, '{os.getenv('DB_ENCRYPTION_KEY')}')"
        return value
```

### Encryption in Transit

**TLS/SSL for Database Connections**:

```python
from sqlalchemy import create_engine
import ssl

# PostgreSQL with SSL
engine = create_engine(
    'postgresql://user:password@localhost/tbcv',
    connect_args={
        'sslmode': 'require',
        'sslcert': '/path/to/client-cert.pem',
        'sslkey': '/path/to/client-key.pem',
        'sslrootcert': '/path/to/ca-cert.pem'
    }
)

# MySQL with SSL
engine = create_engine(
    'mysql+pymysql://user:password@localhost/tbcv',
    connect_args={
        'ssl_ca': '/path/to/ca-cert.pem',
        'ssl_cert': '/path/to/client-cert.pem',
        'ssl_key': '/path/to/client-key.pem',
        'ssl_verify_cert': True,
        'ssl_verify_identity': True
    }
)
```

**API Responses Over HTTPS**:

All API responses must be transmitted over HTTPS with TLS 1.2+:

```python
from starlette.middleware.hsts import HSTSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(
    HSTSMiddleware,
    max_age=31536000,
    include_subdomains=True,
    preload=True
)
```

### Sensitive Data Handling

**Truth Data Protection**:

Truth data contains plugin definitions and may include sensitive information. Implement access controls:

```python
from core.database import db_manager
from core.access_guard import guarded_operation

@guarded_operation
async def get_truth_data(family: str, user_role: str = "viewer"):
    """
    Retrieve truth data with role-based access control.

    Roles:
    - admin: Full access to all truth data
    - editor: Can see truth data for assigned families
    - viewer: Read-only access
    """
    if user_role == "admin":
        return await db_manager.get_all_truth_data(family)
    elif user_role == "editor":
        return await db_manager.get_truth_data_for_family(family)
    else:  # viewer
        # Return minimal information
        return await db_manager.get_public_truth_data(family)
```

**Validation Results Protection**:

Validation results may contain sensitive file content. Implement retention policies:

```python
import datetime
from core.database import db_manager

@guarded_operation
async def cleanup_sensitive_data(days: int = 90):
    """
    Delete validation results older than specified days.

    This should be run daily via a scheduled task.
    """
    cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)

    deleted_count = await db_manager.delete_validations_before(cutoff_date)
    logger.info(f"Deleted {deleted_count} old validation results")

    # Also delete associated recommendations
    deleted_recs = await db_manager.delete_recommendations_before(cutoff_date)
    logger.info(f"Deleted {deleted_recs} old recommendations")
```

**Recommendation Content Redaction**:

When logging recommendations, redact sensitive content:

```python
from core.logging import get_logger
import json

logger = get_logger(__name__)

def log_recommendation(recommendation: dict, user_id: str):
    """Log recommendation with sensitive content redacted."""
    # Create a copy to avoid modifying original
    log_data = recommendation.copy()

    # Redact file paths and content
    if "file_path" in log_data:
        log_data["file_path"] = "[REDACTED_PATH]"

    if "content" in log_data:
        # Show only first 100 chars and mark as redacted
        log_data["content"] = log_data["content"][:100] + "...[REDACTED]"

    logger.info(f"Recommendation approved by {user_id}", extra={
        "recommendation_id": recommendation.get("id"),
        "status": recommendation.get("status"),
        "type": recommendation.get("recommendation_type")
        # Note: Actual content not logged
    })
```

### Backup Encryption

**Encrypted Database Backups**:

```bash
#!/bin/bash
# backup.sh - Secure database backup script

DB_PATH="/data/tbcv.db"
BACKUP_DIR="/backups/tbcv"
ENCRYPTION_KEY="${DB_ENCRYPTION_KEY}"
RETENTION_DAYS=30

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR"

# Backup with compression and encryption
BACKUP_FILE="$BACKUP_DIR/tbcv_$(date +%Y%m%d_%H%M%S).db.gz.gpg"

# Create backup
sqlite3 "$DB_PATH" ".dump" | \
    gzip | \
    gpg --symmetric \
        --cipher-algo AES256 \
        --output "$BACKUP_FILE" \
        --batch \
        --passphrase "$ENCRYPTION_KEY"

# Verify backup
gpg --decrypt "$BACKUP_FILE" | gunzip > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Backup successful: $BACKUP_FILE"
else
    echo "Backup verification failed!"
    rm "$BACKUP_FILE"
    exit 1
fi

# Delete old backups
find "$BACKUP_DIR" -name "tbcv_*.db.gz.gpg" -mtime +$RETENTION_DAYS -delete

# Set restrictive permissions
chmod 600 "$BACKUP_FILE"

# Store backup in secure cloud storage (if available)
# aws s3 cp "$BACKUP_FILE" s3://backup-bucket/tbcv/ --sse AES256 --storage-class GLACIER
```

**PostgreSQL Encrypted Backups**:

```bash
#!/bin/bash
# postgres_backup.sh - Encrypted PostgreSQL backup

PGHOST="${DB_HOST}"
PGPORT="${DB_PORT}"
PGUSER="${DB_USER}"
PGPASSWORD="${DB_PASSWORD}"
DB_NAME="tbcv"
BACKUP_DIR="/backups/tbcv"
ENCRYPTION_KEY="${DB_ENCRYPTION_KEY}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Full backup with compression
BACKUP_FILE="$BACKUP_DIR/tbcv_$(date +%Y%m%d_%H%M%S).sql.gz.gpg"

# Perform backup
pg_dump -h "$PGHOST" -U "$PGUSER" "$DB_NAME" | \
    gzip | \
    gpg --symmetric \
        --cipher-algo AES256 \
        --output "$BACKUP_FILE" \
        --batch \
        --passphrase "$ENCRYPTION_KEY"

# Verify backup
if gpg --decrypt "$BACKUP_FILE" | gunzip | pg_restore -d "$DB_NAME" --dry-run 2>/dev/null; then
    echo "Backup verified: $BACKUP_FILE"
    chmod 600 "$BACKUP_FILE"

    # Upload to S3 with encryption
    aws s3 cp "$BACKUP_FILE" \
        s3://secure-backups/tbcv/ \
        --sse aws:kms \
        --sse-kms-key-id arn:aws:kms:region:account:key/id
else
    echo "Backup verification failed!"
    rm "$BACKUP_FILE"
    exit 1
fi
```

### Data Retention Policies

**Validation Result Retention**:

```python
import datetime
from core.config import get_settings
from core.database import db_manager

class DataRetentionManager:
    """Manage data retention and cleanup policies."""

    def __init__(self):
        self.settings = get_settings()
        self.db = db_manager

    async def cleanup_validation_results(self):
        """Delete validation results older than retention period."""
        retention_days = self.settings.data_retention.validation_results_days
        cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=retention_days)

        deleted = await self.db.delete_validations_before(cutoff_date)
        logger.info(f"Deleted {deleted} validation results older than {retention_days} days")
        return deleted

    async def cleanup_recommendations(self):
        """Delete recommendations older than retention period."""
        retention_days = self.settings.data_retention.recommendations_days
        cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=retention_days)

        deleted = await self.db.delete_recommendations_before(cutoff_date)
        logger.info(f"Deleted {deleted} recommendations older than {retention_days} days")
        return deleted

    async def cleanup_audit_logs(self):
        """Delete audit logs older than retention period."""
        retention_days = self.settings.data_retention.audit_logs_days
        cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=retention_days)

        deleted = await self.db.delete_audit_logs_before(cutoff_date)
        logger.info(f"Deleted {deleted} audit logs older than {retention_days} days")
        return deleted

    async def run_all_cleanup(self):
        """Run all cleanup operations."""
        results = {
            "validations": await self.cleanup_validation_results(),
            "recommendations": await self.cleanup_recommendations(),
            "audit_logs": await self.cleanup_audit_logs()
        }
        logger.info(f"Cleanup complete: {results}")
        return results

# Schedule daily cleanup (in main.py or scheduler)
import schedule

retention_manager = DataRetentionManager()
schedule.every().day.at("02:00").do(
    asyncio.run,
    retention_manager.run_all_cleanup()
)
```

---

## 5. Application Security

### Input Validation

**Pydantic Model Validation**:

```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class ValidationRequest(BaseModel):
    """Validated input for validation requests."""

    file_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Path to file"
    )

    content: str = Field(
        ...,
        min_length=1,
        max_length=10_000_000,  # 10MB
        description="File content"
    )

    family: str = Field(
        ...,
        regex="^[a-z_]+$",
        description="Product family"
    )

    validators: Optional[list] = Field(
        default=["yaml", "markdown", "code"],
        description="Validators to run"
    )

    @validator("file_path")
    def validate_file_path(cls, v):
        """Prevent directory traversal."""
        if ".." in v or v.startswith("/"):
            raise ValueError("Invalid file path")
        return v

    @validator("family")
    def validate_family(cls, v):
        """Ensure family is in allowed list."""
        allowed_families = ["words", "cells", "slides", "pdf"]
        if v not in allowed_families:
            raise ValueError(f"Unknown family: {v}")
        return v

    @validator("validators")
    def validate_validators(cls, v):
        """Ensure only valid validators are specified."""
        allowed_validators = ["yaml", "markdown", "code", "links", "seo", "truth"]
        for validator_name in v:
            if validator_name not in allowed_validators:
                raise ValueError(f"Unknown validator: {validator_name}")
        return v

@app.post("/api/validate")
async def validate_endpoint(request: ValidationRequest):
    """Automatic validation via Pydantic."""
    # request is guaranteed to be valid at this point
    mcp_client = MCPClient()
    return await mcp_client.call_tool("validate_file", {
        "file_path": request.file_path,
        "content": request.content,
        "family": request.family,
        "validators": request.validators
    })
```

### SQL Injection Prevention

**SQLAlchemy Parameterized Queries** (Prevents SQL injection):

```python
from sqlalchemy import text, select
from core.database import db_manager

# ❌ WRONG - String concatenation (vulnerable to SQL injection)
def get_validation_bad(validation_id: str):
    query = f"SELECT * FROM validations WHERE id = '{validation_id}'"
    return db_manager.execute(query)

# ✅ CORRECT - Parameterized query
def get_validation_good(validation_id: str):
    stmt = select(ValidationResult).where(
        ValidationResult.id == validation_id
    )
    return db_manager.execute(stmt)

# ✅ ALSO CORRECT - Using text() with parameters
def get_validation_alt(validation_id: str):
    stmt = text("SELECT * FROM validations WHERE id = :id")
    return db_manager.execute(stmt, {"id": validation_id})
```

### XSS Prevention

**HTML Sanitization** (Bleach library):

```python
import bleach
from typing import Optional

ALLOWED_TAGS = {
    'p': ['style'],
    'br': [],
    'strong': [],
    'em': [],
    'u': [],
    'a': ['href', 'title'],
    'img': ['src', 'alt', 'title'],
    'code': ['style'],
    'pre': [],
}

ALLOWED_ATTRIBUTES = {
    '*': ['title'],
    'a': ['href'],
    'img': ['src', 'alt'],
}

def sanitize_html(html_content: str) -> str:
    """Sanitize HTML to prevent XSS attacks."""
    return bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )

def sanitize_text(text: str) -> str:
    """Escape plain text to prevent XSS in HTML context."""
    return bleach.clean(text, tags=[], strip=True)

# Usage in templates
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

@app.get("/validations/{validation_id}")
async def view_validation(validation_id: str, request: Request):
    validation = get_validation(validation_id)

    return templates.TemplateResponse("validation.html", {
        "request": request,
        "validation": validation,
        "content": sanitize_html(validation.content)
    })
```

**Content Security Policy (CSP)**:

```python
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Strict CSP to prevent XSS
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "  # Only if necessary
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        return response

app.add_middleware(CSPMiddleware)
```

### CSRF Protection

**CSRF Token Implementation**:

```python
from fastapi import Form
import secrets
import hashlib

class CSRFProtection:
    """CSRF token protection for forms."""

    def __init__(self):
        self.tokens = {}

    def generate_token(self, session_id: str) -> str:
        """Generate CSRF token for session."""
        token = secrets.token_urlsafe(32)
        self.tokens[session_id] = token
        return token

    def validate_token(self, session_id: str, token: str) -> bool:
        """Validate CSRF token."""
        stored_token = self.tokens.get(session_id)
        return stored_token and stored_token == token

csrf_protection = CSRFProtection()

@app.get("/form")
async def show_form(request: Request):
    """Return form with CSRF token."""
    session_id = request.session.get("id")
    csrf_token = csrf_protection.generate_token(session_id)

    return templates.TemplateResponse("form.html", {
        "request": request,
        "csrf_token": csrf_token
    })

@app.post("/submit-form")
async def submit_form(
    request: Request,
    csrf_token: str = Form(...)
):
    """Validate CSRF token before processing."""
    session_id = request.session.get("id")

    if not csrf_protection.validate_token(session_id, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    # Process form
    ...
```

### File Upload Security

**Secure File Upload Pattern**:

```python
import os
import magic
from pathlib import Path

UPLOAD_DIR = "/uploads"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".md", ".txt", ".json", ".yaml"}
ALLOWED_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "application/json",
    "application/x-yaml",
    "text/yaml"
}

async def secure_file_upload(file: UploadFile) -> str:
    """
    Securely handle file uploads.

    Checks:
    1. File size limit
    2. File extension whitelist
    3. MIME type validation
    4. Filename sanitization
    5. Virus scanning (if available)
    """

    # Check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (max {MAX_FILE_SIZE} bytes)"
        )

    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed: {file_ext}"
        )

    # Validate MIME type
    mime = magic.Magic(mime=True)
    detected_mime = mime.from_buffer(contents)
    if detected_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file content: {detected_mime}"
        )

    # Sanitize filename
    safe_filename = Path(file.filename).name
    if any(c in safe_filename for c in ["...", "/", "\\"]):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename"
        )

    # Generate secure filename
    import uuid
    unique_filename = f"{uuid.uuid4()}_{safe_filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Ensure upload directory is safe
    real_path = os.path.realpath(file_path)
    real_upload_dir = os.path.realpath(UPLOAD_DIR)
    if not real_path.startswith(real_upload_dir):
        raise HTTPException(
            status_code=400,
            detail="Invalid file path"
        )

    # Optional: Virus scanning
    if await scan_file_for_virus(contents):
        raise HTTPException(
            status_code=400,
            detail="File failed security scan"
        )

    # Write file
    with open(file_path, "wb") as f:
        f.write(contents)

    return unique_filename

@app.post("/api/upload")
async def upload_file(file: UploadFile):
    """Handle file upload securely."""
    filename = await secure_file_upload(file)
    return {"filename": filename}
```

### Command Injection Prevention

**Subprocess Safety**:

```python
import subprocess
import shlex
from typing import List

# ❌ WRONG - Vulnerable to command injection
def run_command_bad(user_input: str):
    command = f"python validate.py {user_input}"
    result = subprocess.run(command, shell=True)  # VULNERABLE!
    return result.returncode

# ✅ CORRECT - Safe subprocess execution
def run_command_good(user_input: str):
    # Use list form to avoid shell interpretation
    command = ["python", "validate.py", user_input]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

# ✅ ALSO SAFE - Using shlex.quote for shell mode
def run_command_alt(user_input: str):
    # If shell=True is necessary, quote arguments
    command = f"python validate.py {shlex.quote(user_input)}"
    result = subprocess.run(command, shell=True)
    return result.returncode

# Usage in TBCV
def validate_markdown_file(file_path: str) -> dict:
    """Validate markdown file safely."""
    # Validate path first
    safe_path = validate_path(file_path)

    # Use list form to avoid injection
    try:
        result = subprocess.run(
            ["python", "-m", "cli.main", "validate-file", safe_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        return {
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout,
            "error": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error": "Validation timeout"
        }
```

---

## 6. Authentication & Session Management

### Secure Session Handling

**Session Configuration** (FastAPI/Starlette):

```python
from fastapi.middleware.sessions import SessionMiddleware
import os

# Configure secure session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY"),
    session_cookie="session",
    max_age=3600,  # 1 hour
    path="/",
    domain=None,
    secure=True,  # HTTPS only
    httponly=True,  # No JavaScript access
    samesite="lax"  # CSRF protection
)

# Use session
@app.post("/login")
async def login(request: Request, credentials: LoginRequest):
    # Verify credentials
    user = verify_credentials(credentials.username, credentials.password)

    if user:
        request.session["user_id"] = user.id
        request.session["username"] = user.username
        request.session["role"] = user.role
        return {"status": "authenticated"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"status": "logged out"}
```

### Token Management

**JWT Token Implementation**:

```python
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})

    # Sign with algorithm
    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt

def verify_token(token: str):
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/token")
async def login_for_access_token(credentials: LoginRequest):
    """Issue access token."""
    user = authenticate_user(credentials.username, credentials.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@app.post("/refresh-token")
async def refresh_token(request: Request):
    """Issue new access token using refresh token."""
    refresh_token = request.headers.get("Authorization", "").split("Bearer ")[-1]

    try:
        user_id = verify_refresh_token(refresh_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Issue new access token
    access_token = create_access_token(data={"sub": str(user_id)})

    return {"access_token": access_token, "token_type": "bearer"}
```

### Password Policies

**Secure Password Handling**:

```python
import hashlib
import secrets
from typing import Tuple

class PasswordManager:
    """Manage password hashing and validation."""

    # Password policy constants
    MIN_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = True
    MAX_AGE_DAYS = 90
    MIN_UNIQUE_NEW = 3  # Don't reuse last 3 passwords

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(password, password_hash)

    @classmethod
    def validate_password_strength(cls, password: str) -> Tuple[bool, str]:
        """Validate password strength."""
        if len(password) < cls.MIN_LENGTH:
            return False, f"Password must be at least {cls.MIN_LENGTH} characters"

        if cls.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            return False, "Password must contain uppercase letter"

        if cls.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            return False, "Password must contain lowercase letter"

        if cls.REQUIRE_DIGITS and not any(c.isdigit() for c in password):
            return False, "Password must contain digit"

        if cls.REQUIRE_SPECIAL and not any(c in "!@#$%^&*()" for c in password):
            return False, "Password must contain special character"

        return True, "Password is valid"

# Usage
from pydantic import BaseModel, field_validator

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    def validate_new_password(cls, v):
        is_valid, msg = PasswordManager.validate_password_strength(v)
        if not is_valid:
            raise ValueError(msg)
        return v

@app.post("/api/change-password")
async def change_password(request: ChangePasswordRequest, user_id: str):
    """Change user password."""
    user = get_user(user_id)

    # Verify old password
    if not PasswordManager.verify_password(request.old_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")

    # Check password hasn't been used recently
    if check_password_history(user_id, request.new_password):
        raise HTTPException(status_code=400, detail="Password was recently used")

    # Update password
    user.password_hash = PasswordManager.hash_password(request.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "password changed"}
```

### Multi-Factor Authentication (MFA)

**TOTP (Time-Based One-Time Password) Implementation**:

```python
import pyotp
import qrcode
from io import BytesIO

class MFAManager:
    """Manage multi-factor authentication."""

    @staticmethod
    def generate_secret() -> str:
        """Generate TOTP secret."""
        return pyotp.random_base32()

    @staticmethod
    def get_provisioning_uri(email: str, secret: str) -> str:
        """Get provisioning URI for QR code."""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            email,
            issuer_name="TBCV"
        )

    @staticmethod
    def generate_qr_code(provisioning_uri: str) -> bytes:
        """Generate QR code image."""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        """Verify TOTP token."""
        totp = pyotp.TOTP(secret)
        # Allow ±1 time window for clock skew
        return totp.verify(token, valid_window=1)

@app.post("/mfa/setup")
async def setup_mfa(user_id: str):
    """Setup MFA for user."""
    user = get_user(user_id)

    # Generate secret
    secret = MFAManager.generate_secret()

    # Get provisioning URI
    provisioning_uri = MFAManager.get_provisioning_uri(user.email, secret)

    # Generate QR code
    qr_code = MFAManager.generate_qr_code(provisioning_uri)

    # Store secret temporarily (not confirmed yet)
    cache.set(f"mfa_setup_{user_id}", secret, ttl=600)  # 10 minutes

    return {
        "qr_code": qr_code.hex(),
        "secret": secret
    }

@app.post("/mfa/confirm")
async def confirm_mfa(user_id: str, token: str):
    """Confirm MFA setup."""
    user = get_user(user_id)

    # Get temporary secret
    secret = cache.get(f"mfa_setup_{user_id}")
    if not secret:
        raise HTTPException(status_code=400, detail="MFA setup expired")

    # Verify token
    if not MFAManager.verify_totp(secret, token):
        raise HTTPException(status_code=400, detail="Invalid token")

    # Save secret to user
    user.mfa_secret = secret
    user.mfa_enabled = True
    db.commit()

    # Clear temporary secret
    cache.delete(f"mfa_setup_{user_id}")

    return {"status": "MFA enabled"}

@app.post("/login")
async def login(credentials: LoginRequest):
    """Login with optional MFA."""
    user = authenticate_user(credentials.username, credentials.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # If MFA enabled, require token
    if user.mfa_enabled:
        if not credentials.mfa_token:
            raise HTTPException(status_code=403, detail="MFA token required")

        if not MFAManager.verify_totp(user.mfa_secret, credentials.mfa_token):
            raise HTTPException(status_code=401, detail="Invalid MFA token")

    # Issue access token
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token}
```

### Session Timeout Configuration

**Automatic Session Expiration**:

```python
from datetime import datetime, timedelta, timezone
import asyncio

class SessionManager:
    """Manage session timeouts and expiration."""

    def __init__(self):
        self.active_sessions = {}  # session_id -> session_data
        self.idle_timeout = 3600  # 1 hour
        self.absolute_timeout = 28800  # 8 hours

    async def start_session(self, user_id: str) -> str:
        """Create new session."""
        import uuid

        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        self.active_sessions[session_id] = {
            "user_id": user_id,
            "created_at": now,
            "last_activity": now
        }

        # Start expiration monitor
        asyncio.create_task(self._monitor_session(session_id))

        return session_id

    async def _monitor_session(self, session_id: str):
        """Monitor session for timeout."""
        session = self.active_sessions.get(session_id)
        if not session:
            return

        while session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            now = datetime.now(timezone.utc)

            # Check idle timeout
            idle_time = (now - session["last_activity"]).total_seconds()
            if idle_time > self.idle_timeout:
                logger.info(f"Session {session_id} expired due to inactivity")
                del self.active_sessions[session_id]
                break

            # Check absolute timeout
            absolute_time = (now - session["created_at"]).total_seconds()
            if absolute_time > self.absolute_timeout:
                logger.info(f"Session {session_id} expired (absolute timeout)")
                del self.active_sessions[session_id]
                break

            # Wait before next check
            await asyncio.sleep(60)  # Check every minute

    def touch_session(self, session_id: str):
        """Update last activity time."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["last_activity"] = datetime.now(timezone.utc)

    def invalidate_session(self, session_id: str):
        """Explicitly invalidate session."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

# Usage in middleware
session_manager = SessionManager()

@app.middleware("http")
async def session_middleware(request: Request, call_next):
    """Update session activity on each request."""
    session_id = request.session.get("session_id")

    if session_id:
        session_manager.touch_session(session_id)

    response = await call_next(request)
    return response
```

---

## 7. Dependency Security

### Managing Python Dependencies

**Lock Dependency Versions**:

```
# requirements.txt - Pin specific versions
fastapi==0.115.3
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic==2.12.0
# ... etc
```

**Use Requirements with Hash Verification**:

```
fastapi==0.115.3 --hash=sha256:abc123...
uvicorn==0.24.0 --hash=sha256:def456...
```

### Vulnerability Scanning

**Regular Dependency Audits**:

```bash
# Install tools
pip install safety pip-audit

# Check for known vulnerabilities
safety check
pip-audit

# Generate reports
safety check --json > security_report.json
pip-audit --desc --format json > audit_report.json
```

**Automated Scanning in CI/CD**:

```yaml
# .github/workflows/security.yml
name: Security Checks

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install safety pip-audit

      - name: Run safety check
        run: safety check --json
        continue-on-error: true

      - name: Run pip-audit
        run: pip-audit --desc --format json
        continue-on-error: true
```

### Keeping Dependencies Updated

**Scheduled Updates** (Dependabot):

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "03:00"
    open-pull-requests-limit: 5
    reviewers:
      - "security-team"
    labels:
      - "dependencies"
    allow:
      - dependency-type: "all"
```

**Manual Update Process**:

```bash
# Check outdated packages
pip list --outdated

# Update specific package
pip install --upgrade fastapi

# Update all packages safely
pip install -U -r requirements.txt

# Test after update
pytest
```

### Security Advisories

**Monitor Security Advisories**:

1. Subscribe to package security lists
2. Monitor GitHub security advisories
3. Set up alerts for TBCV dependencies

```python
# Check for compromised packages at startup
import requests
import json

async def check_security_advisories():
    """Check GitHub security database for known vulnerabilities."""
    with open("requirements.txt") as f:
        packages = [line.split("==")[0] for line in f if "==" in line]

    vulnerabilities = []
    for package in packages:
        try:
            response = requests.get(
                f"https://api.github.com/repos/{package}/security/advisories"
            )
            if response.status_code == 200:
                advisories = response.json()
                if advisories:
                    vulnerabilities.append({
                        "package": package,
                        "count": len(advisories),
                        "advisories": advisories
                    })
        except Exception as e:
            logger.warning(f"Could not check {package}: {e}")

    if vulnerabilities:
        logger.warning(f"Found {len(vulnerabilities)} packages with vulnerabilities")
        logger.warning(json.dumps(vulnerabilities, indent=2))

    return vulnerabilities
```

---

## 8. Deployment Security

### Container Security (Docker)

**Secure Dockerfile**:

```dockerfile
# Use minimal base image
FROM python:3.11-slim-bullseye

# Set working directory
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 tbcv

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=tbcv:tbcv . .

# Switch to non-root user
USER tbcv

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health/live')"

# Run application
CMD ["python", "main.py", "--mode", "api"]
```

**Container Scanning**:

```bash
# Scan image for vulnerabilities
docker scan tbcv:latest

# Use Trivy for detailed scanning
trivy image tbcv:latest

# Use Grype for SBOM
grype tbcv:latest
```

### Environment Variable Security

**Secure Secrets Management**:

```python
# ❌ WRONG - Hardcoded secrets
API_KEY = "sk-1234567890"
DB_PASSWORD = "password123"

# ✅ CORRECT - Environment variables
import os
API_KEY = os.getenv("API_KEY")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# ✅ BETTER - Secrets manager
from aws_secretsmanager_caching import SecretCache
import json

def get_secret(secret_name: str) -> dict:
    """Get secret from AWS Secrets Manager."""
    cache = SecretCache()
    secret = cache.get_secret_string(secret_name)
    return json.loads(secret)

# Usage
db_credentials = get_secret("tbcv/database")
db_password = db_credentials["password"]
```

**.env File Security**:

```bash
# .env - NEVER commit to git
DB_HOST=localhost
DB_PORT=5432
DB_USER=tbcv
DB_PASSWORD=secure_password_123
JWT_SECRET_KEY=long_random_secret_key
API_KEY=sk_live_...

# .env.example - Commit to git (no secrets)
DB_HOST=
DB_PORT=
DB_USER=
DB_PASSWORD=
JWT_SECRET_KEY=
API_KEY=
```

**Load Environment Variables Securely**:

```python
from dotenv import load_dotenv
import os

# Load from .env file (development only)
if os.getenv("ENVIRONMENT") == "development":
    load_dotenv(".env")

# Alternatively, use Pydantic settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings from environment."""

    db_host: str
    db_port: int
    db_user: str
    db_password: str
    jwt_secret_key: str
    api_key: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
```

### Secrets Management

**HashiCorp Vault Integration**:

```python
import hvac
import json

class VaultManager:
    """Manage secrets using HashiCorp Vault."""

    def __init__(self, vault_addr: str, vault_token: str):
        self.client = hvac.Client(url=vault_addr, token=vault_token)

    def get_secret(self, path: str, key: str = None):
        """Get secret from Vault."""
        response = self.client.secrets.kv.read_secret_version(path=path)
        data = response['data']['data']

        if key:
            return data.get(key)
        return data

    def get_database_credentials(self) -> dict:
        """Get database credentials."""
        return self.get_secret("secret/tbcv/database")

    def get_api_keys(self) -> dict:
        """Get API keys."""
        return self.get_secret("secret/tbcv/api-keys")

# Usage at startup
import os

vault_addr = os.getenv("VAULT_ADDR")
vault_token = os.getenv("VAULT_TOKEN")
vault_manager = VaultManager(vault_addr, vault_token)

db_creds = vault_manager.get_database_credentials()
api_keys = vault_manager.get_api_keys()
```

### Service Account Permissions

**Principle of Least Privilege**:

```yaml
# Kubernetes RBAC example
apiVersion: v1
kind: ServiceAccount
metadata:
  name: tbcv-app

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: tbcv-role
rules:
# Only allow necessary actions
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]

- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get"]

- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get"]
  resourceNames: ["tbcv-secrets"]  # Specific secret only

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: tbcv-role-binding
subjects:
- kind: ServiceAccount
  name: tbcv-app
roleRef:
  kind: Role
  name: tbcv-role
  apiGroup: rbac.authorization.k8s.io
```

---

## 9. Monitoring & Incident Response

### Security Logging

**Structured Security Logging**:

```python
from structlog import get_logger

logger = get_logger(__name__)

def log_security_event(
    event_type: str,
    user_id: str,
    action: str,
    resource: str,
    status: str,
    details: dict = None
):
    """Log security-relevant event."""
    logger.info(
        "security_event",
        event_type=event_type,
        user_id=user_id,
        action=action,
        resource=resource,
        status=status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        **(details or {})
    )

# Usage
log_security_event(
    event_type="authentication",
    user_id="user123",
    action="login",
    resource="api",
    status="success"
)

log_security_event(
    event_type="authorization",
    user_id="user123",
    action="access_denied",
    resource="/admin/settings",
    status="blocked",
    details={"reason": "insufficient_permissions"}
)
```

### Audit Trails

**Complete Audit Logging**:

```python
from core.database import db_manager
from core.logging import get_logger
from datetime import datetime, timezone

logger = get_logger(__name__)

async def audit_log(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    changes: dict = None,
    status: str = "success"
):
    """Log action to audit trail."""
    audit_entry = {
        "timestamp": datetime.now(timezone.utc),
        "user_id": user_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "changes": changes or {},
        "status": status,
        "ip_address": request.client.host if request else None
    }

    # Store in database
    await db_manager.create_audit_log(audit_entry)

    # Log to security logs
    logger.info(
        "audit_log",
        **audit_entry
    )

# Usage
await audit_log(
    user_id="user123",
    action="recommendation_approved",
    resource_type="recommendation",
    resource_id="rec456",
    changes={"status": "pending -> approved"},
    status="success"
)
```

### Anomaly Detection

**Detect Suspicious Patterns**:

```python
from core.database import db_manager
from datetime import datetime, timedelta, timezone

class AnomalyDetector:
    """Detect suspicious activity patterns."""

    @staticmethod
    async def check_failed_login_attempts(user_id: str, threshold: int = 5):
        """Detect brute force attempts."""
        # Check failed logins in last hour
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        failed_attempts = await db_manager.count_failed_logins(
            user_id,
            since=one_hour_ago
        )

        if failed_attempts >= threshold:
            logger.warning(
                "possible_brute_force",
                user_id=user_id,
                failed_attempts=failed_attempts
            )
            # Lock account or require MFA
            await db_manager.set_user_locked(user_id, locked=True)
            return False

        return True

    @staticmethod
    async def check_unusual_access_patterns(user_id: str):
        """Detect unusual access patterns."""
        # Get user's typical access times
        typical_hours = await db_manager.get_user_typical_access_hours(user_id)

        # Get current access time
        current_hour = datetime.now(timezone.utc).hour

        # If accessing outside typical hours, flag it
        if current_hour not in typical_hours:
            logger.warning(
                "unusual_access_time",
                user_id=user_id,
                access_hour=current_hour,
                typical_hours=typical_hours
            )
            # Require additional verification
            return False

        return True

    @staticmethod
    async def check_data_access_anomalies(user_id: str, accessed_resources: int):
        """Detect unusual data access volumes."""
        # Get user's typical access volume per hour
        typical_volume = await db_manager.get_user_typical_access_volume(user_id)

        # If accessing significantly more than usual, flag it
        if accessed_resources > typical_volume * 2:
            logger.warning(
                "unusual_access_volume",
                user_id=user_id,
                accessed_resources=accessed_resources,
                typical_volume=typical_volume
            )
            # Require approval for large data access
            return False

        return True
```

### Incident Response Procedures

**Incident Response Plan**:

```python
from enum import Enum
from datetime import datetime, timezone

class IncidentSeverity(Enum):
    """Incident severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentHandler:
    """Handle security incidents."""

    async def report_incident(
        self,
        severity: IncidentSeverity,
        description: str,
        affected_systems: list,
        evidence: dict
    ):
        """Report security incident."""
        incident = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc),
            "severity": severity.value,
            "description": description,
            "affected_systems": affected_systems,
            "evidence": evidence,
            "status": "open"
        }

        # Store incident
        await db_manager.create_incident(incident)

        # Alert security team based on severity
        if severity in [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]:
            await self.alert_security_team(incident)

        # Take automated response actions
        if severity == IncidentSeverity.CRITICAL:
            await self.escalate_incident(incident)

    async def alert_security_team(self, incident: dict):
        """Alert security team of incident."""
        # Send email/Slack/PagerDuty alert
        message = f"""
        SECURITY INCIDENT DETECTED
        Severity: {incident['severity']}
        Description: {incident['description']}
        Affected Systems: {', '.join(incident['affected_systems'])}
        Evidence: {json.dumps(incident['evidence'], indent=2)}
        """

        await send_alert(message, recipient="security-team@company.com")

    async def escalate_incident(self, incident: dict):
        """Escalate critical incident."""
        # Lock affected resources
        for system in incident['affected_systems']:
            await lock_system(system)

        # Enable enhanced logging
        logger.setLevel(logging.DEBUG)

        # Notify incident commander
        await notify_incident_commander(incident)

# Usage
incident_handler = IncidentHandler()

await incident_handler.report_incident(
    severity=IncidentSeverity.HIGH,
    description="Unauthorized access attempt detected",
    affected_systems=["api_server", "database"],
    evidence={
        "ip_address": "192.0.2.1",
        "user_id": "unknown",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempts": 15
    }
)
```

### Security Alerts

**Alert Configuration**:

```python
from enum import Enum

class AlertType(Enum):
    """Alert types."""
    AUTHENTICATION_FAILURE = "auth_failure"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    VULNERABILITY_DETECTED = "vulnerability_detected"
    DATA_EXFILTRATION = "data_exfiltration"
    RESOURCE_ABUSE = "resource_abuse"
    CONFIGURATION_CHANGE = "config_change"

async def setup_alerts():
    """Configure security alerts."""
    alert_manager = AlertManager()

    # High priority alerts
    alert_manager.add_alert(
        alert_type=AlertType.AUTHENTICATION_FAILURE,
        threshold=5,
        window_seconds=300,  # 5 minutes
        severity="high",
        recipients=["security-team@company.com"],
        actions=["lock_account", "notify_user"]
    )

    alert_manager.add_alert(
        alert_type=AlertType.UNAUTHORIZED_ACCESS,
        threshold=1,
        window_seconds=0,
        severity="critical",
        recipients=["ciso@company.com"],
        actions=["lock_resource", "disable_user", "alert_soc"]
    )

    alert_manager.add_alert(
        alert_type=AlertType.VULNERABILITY_DETECTED,
        threshold=1,
        window_seconds=0,
        severity="high",
        recipients=["security-team@company.com"],
        actions=["patch_system", "increase_monitoring"]
    )
```

---

## 10. Security Checklist

### Pre-Deployment Security Checklist

**Infrastructure & Deployment**

- [ ] HTTPS/TLS enabled with TLS 1.2+ minimum
- [ ] SSL certificate from trusted CA (not self-signed)
- [ ] HSTS header configured and enforced
- [ ] Firewall rules configured (restrict inbound/outbound)
- [ ] Non-standard ports blocked (only 443/8443 open)
- [ ] Service running as non-root user
- [ ] File permissions properly restricted (644 for files, 755 for directories)
- [ ] SELinux or AppArmor policies configured
- [ ] Container/VM hardened (if applicable)
- [ ] Network segmentation in place (VPC/security groups)

**Access Control**

- [ ] Access guard enforcement mode set to BLOCK (production)
- [ ] Import guards installed and verified
- [ ] MCP-first architecture enforced
- [ ] No direct imports of protected modules in API/CLI
- [ ] API authentication enabled (API keys or JWT)
- [ ] API endpoints require authentication
- [ ] RBAC implemented and configured
- [ ] Admin accounts restricted to authorized users
- [ ] Service account permissions follow least privilege
- [ ] Access logs enabled and monitored

**Data Security**

- [ ] Database encryption at rest enabled
- [ ] Database encryption in transit (TLS/SSL)
- [ ] Backup encryption enabled
- [ ] Data retention policies configured
- [ ] Sensitive data redaction in logs
- [ ] Password hashing using strong algorithms (bcrypt)
- [ ] Session timeouts configured (idle + absolute)
- [ ] No plaintext passwords in code/configs
- [ ] Secrets stored in secure manager (Vault/AWS Secrets)
- [ ] Database credentials rotated regularly

**Application Security**

- [ ] Input validation on all API endpoints
- [ ] Output encoding for HTML/JSON responses
- [ ] SQL injection prevention verified (parameterized queries)
- [ ] XSS prevention verified (HTML sanitization)
- [ ] CSRF protection enabled
- [ ] File upload security implemented
- [ ] Command injection prevention verified
- [ ] Rate limiting configured
- [ ] CORS properly configured (whitelist origins)
- [ ] Security headers configured (CSP, X-Frame-Options, etc.)

**Dependencies & Updates**

- [ ] All dependencies pinned to specific versions
- [ ] Vulnerability scanning performed (safety, pip-audit)
- [ ] No known vulnerabilities in dependencies
- [ ] Dependency update process established
- [ ] Security advisories subscribed
- [ ] Dependency lock file committed to git
- [ ] Regular update schedule (weekly/monthly)
- [ ] Test coverage includes security tests
- [ ] CI/CD pipeline includes security checks
- [ ] SBOM (Software Bill of Materials) generated

**Monitoring & Logging**

- [ ] Security logging configured
- [ ] Audit trails enabled
- [ ] Log retention configured
- [ ] Logs stored securely
- [ ] Log access restricted
- [ ] Monitoring/alerting configured
- [ ] Alerting recipients configured
- [ ] Incident response procedures documented
- [ ] On-call schedule for security alerts
- [ ] Regular log reviews scheduled

**Documentation & Training**

- [ ] Security documentation complete (this guide)
- [ ] Security policies documented
- [ ] Incident response plan documented
- [ ] Security contacts documented
- [ ] Team trained on security practices
- [ ] RBAC documentation complete
- [ ] API security documentation complete
- [ ] Deployment security runbook created
- [ ] Post-incident review process defined
- [ ] Security changelog maintained

### Production Security Hardening

**Environment Setup**

```bash
# Set enforcement mode to BLOCK
export TBCV_ACCESS_GUARD_MODE=block
export TBCV_ENVIRONMENT=production

# Enable HTTPS only
export TBCV_SSL_ENABLED=true
export TBCV_SSL_CERT_PATH=/path/to/cert.pem
export TBCV_SSL_KEY_PATH=/path/to/key.pem

# Database encryption
export DB_ENCRYPTION_KEY=$(openssl rand -hex 32)
export DB_ENCRYPTION_ALGORITHM=AES256

# Session security
export SESSION_SECRET_KEY=$(openssl rand -hex 32)
export SESSION_TIMEOUT_MINUTES=30

# JWT configuration
export JWT_SECRET_KEY=$(openssl rand -hex 32)
export JWT_ALGORITHM=HS256
export JWT_EXPIRATION_MINUTES=30

# API rate limiting
export RATE_LIMIT_CALLS=10
export RATE_LIMIT_PERIOD=60

# Logging
export LOG_LEVEL=WARNING
export LOG_RETENTION_DAYS=90
export AUDIT_LOG_ENABLED=true
```

**Firewall Configuration**

```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 8443/tcp # TBCV API
sudo ufw enable

# firewalld (RHEL/CentOS)
sudo firewall-cmd --set-default-zone=drop
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=8443/tcp
sudo firewall-cmd --reload
```

**System Hardening**

```bash
# Disable unnecessary services
sudo systemctl disable avahi-daemon
sudo systemctl disable cups
sudo systemctl disable bluetooth

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install security tools
sudo apt-get install -y fail2ban aide auditd

# Configure fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Enable audit logging
sudo systemctl enable auditd
sudo systemctl start auditd
```

### Regular Security Audits

**Weekly Security Tasks**

- [ ] Review security logs for anomalies
- [ ] Check alert configuration is working
- [ ] Verify all services are running
- [ ] Review failed authentication attempts
- [ ] Check for unusual data access patterns
- [ ] Verify backups are successful

**Monthly Security Tasks**

- [ ] Review and update security policies
- [ ] Audit access control configuration
- [ ] Review user access rights
- [ ] Run vulnerability scanning
- [ ] Test incident response procedures
- [ ] Review dependency updates
- [ ] Audit log retention and integrity

**Quarterly Security Reviews**

- [ ] Full security audit (external if possible)
- [ ] Penetration testing
- [ ] Code review for security issues
- [ ] Architecture review against OWASP Top 10
- [ ] Update threat model
- [ ] Security training for team
- [ ] Incident response simulation

**Annual Security Assessment**

- [ ] Comprehensive security audit
- [ ] Compliance assessment (SOC2, ISO, etc.)
- [ ] Disaster recovery testing
- [ ] Business continuity testing
- [ ] Third-party security review
- [ ] Update security documentation
- [ ] Plan for next year's improvements

### Compliance Considerations

**SOC2 Compliance**

- [ ] Access control policies documented and enforced
- [ ] Change management process implemented
- [ ] Monitoring and alerting configured
- [ ] Incident response plan documented
- [ ] Data retention and destruction policies
- [ ] Regular security training
- [ ] Annual audits scheduled

**GDPR Compliance** (if applicable)

- [ ] Data processing agreements in place
- [ ] Data protection impact assessments
- [ ] Right to be forgotten implemented
- [ ] Data breach notification procedures
- [ ] Privacy policy documented
- [ ] Consent management for data processing
- [ ] Regular compliance audits

**HIPAA Compliance** (if handling health data)

- [ ] Encryption of data at rest and in transit
- [ ] Access controls and audit trails
- [ ] Data integrity controls
- [ ] Disaster recovery and backup procedures
- [ ] Security incident procedures
- [ ] Business associate agreements

**PCI DSS Compliance** (if handling payment data)

- [ ] Network segmentation
- [ ] Strong encryption
- [ ] Access controls
- [ ] Vulnerability management
- [ ] Security monitoring
- [ ] Incident response procedures

---

## References

### External Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/) - Critical web application security risks
- [OWASP API Top 10](https://owasp.org/www-project-api-security/) - API security risks
- [CWE Top 25](https://cwe.mitre.org/top25/) - Most dangerous software weaknesses
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework) - Security governance
- [PCI DSS](https://www.pcisecuritystandards.org/) - Payment card security
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security) - Health data security
- [GDPR](https://gdpr-info.eu/) - Data protection regulation

### Python Security Libraries

- **passlib** - Password hashing
- **pyotp** - Multi-factor authentication
- **cryptography** - Encryption
- **bleach** - HTML sanitization
- **safety** - Dependency vulnerability scanning
- **bandit** - Code security analysis
- **pip-audit** - Dependency auditing

### TBCV Documentation

- [Security Architecture](security.md) - Detailed security architecture
- [Configuration Guide](configuration.md) - Security configuration options
- [Deployment Guide](deployment.md) - Secure deployment procedures
- [Troubleshooting](troubleshooting.md) - Common security issues
- [API Reference](api_reference.md) - API security features

---

**Document Version**: 1.0.0
**Last Updated**: 2025-12-05
**Status**: Complete
**Review Date**: 2026-03-05

**Maintainers**: Security Team
**Contact**: security@company.com

---

## Appendix: Security Testing Examples

### Example 1: Testing Access Guards

```python
# tests/test_security_guards.py
import pytest
from core.access_guard import guarded_operation, AccessGuardError, set_enforcement_mode, EnforcementMode

def test_access_guard_blocks_api_access():
    """Test that access guard blocks API access."""
    set_enforcement_mode(EnforcementMode.BLOCK)

    @guarded_operation
    def protected_function():
        return "success"

    # Calling from test context (allowed)
    result = protected_function()
    assert result == "success"

def test_access_guard_violation_logging():
    """Test that violations are logged."""
    set_enforcement_mode(EnforcementMode.WARN)

    @guarded_operation
    def protected_function():
        return "success"

    result = protected_function()
    assert result == "success"

    # Check logs contain violation info
    # (implementation depends on logging setup)
```

### Example 2: Testing Input Validation

```python
# tests/test_input_validation.py
import pytest
from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)

def test_validate_file_path_traversal():
    """Test that path traversal is prevented."""
    response = client.post("/api/validate", json={
        "file_path": "../../../etc/passwd",
        "content": "test",
        "family": "words"
    })
    assert response.status_code == 422  # Validation error

def test_validate_invalid_family():
    """Test that invalid family is rejected."""
    response = client.post("/api/validate", json={
        "file_path": "test.md",
        "content": "test",
        "family": "invalid"
    })
    assert response.status_code == 422  # Validation error

def test_validate_oversized_content():
    """Test that oversized content is rejected."""
    large_content = "x" * (11 * 1024 * 1024)  # 11MB
    response = client.post("/api/validate", json={
        "file_path": "test.md",
        "content": large_content,
        "family": "words"
    })
    assert response.status_code == 422  # Validation error
```

### Example 3: Testing SQL Injection Prevention

```python
# tests/test_sql_injection.py
import pytest
from core.database import db_manager

def test_sql_injection_prevented():
    """Test that SQL injection attempts are prevented."""
    # Attempt SQL injection
    malicious_input = "' OR '1'='1"

    # Using SQLAlchemy ORM (safe)
    result = db_manager.get_validation(malicious_input)
    assert result is None  # No validation found

    # Using parameterized query (safe)
    from sqlalchemy import text
    stmt = text("SELECT * FROM validations WHERE id = :id")
    # Parameters are properly escaped
    result = db_manager.execute(stmt, {"id": malicious_input})
    assert result is None or len(list(result)) == 0
```

