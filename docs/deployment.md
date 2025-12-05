# Deployment

## Overview

TBCV can be deployed locally for development, in production environments, or using containerization. This guide covers various deployment scenarios and best practices.

## Prerequisites

### System Requirements
- **OS**: Linux, macOS, Windows
- **Python**: 3.8 or higher
- **Memory**: 2GB minimum, 8GB recommended
- **Disk**: 1GB for application, variable for data
- **Network**: Internet access for external integrations

### Dependencies
```bash
# Core dependencies
pip install -r requirements.txt

# Optional: Development dependencies
pip install -r requirements.txt -e .[dev]

# Optional: Performance monitoring
pip install -r requirements.txt -e .[performance]
```

### External Services

All external services are **optional**. TBCV works with SQLite and no LLM by default.

| Service | Status | Version | Purpose | Required |
|---------|--------|---------|---------|----------|
| **Ollama** | Active | 0.4.4+ | Local LLM inference | Optional |
| **ChromaDB** | Active | 0.6.3 | Vector database for RAG | Optional |
| **PostgreSQL** | Supported | Any | Production database | Optional (SQLite default) |
| **Redis** | Optional | 5.0.1 | Distributed L2 cache (multi-node only) | Optional (SQLite L2 default) |
| **LangChain** | Installed (unused) | Latest | LLM framework | No (custom RAG) |
| **Prometheus** | Planned | N/A | Metrics collection | Optional |
| **Sentry** | Optional | Latest | Error tracking | Optional |
| **Google GenAI** | Supported | 1.39.1 | Gemini API fallback | Optional |

### Detailed External Services Configuration

#### Ollama (Active)
**Purpose**: Local LLM inference for semantic validation
**Status**: Active, optional
**Version**: 0.4.4+
**Configuration**:
```yaml
llm_validator:
  enabled: true
  ollama_base_url: "http://localhost:11434"
  model: "qwen2.5:latest"
```

**Setup**:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull qwen2.5:latest

# Start Ollama
ollama serve
```

**When to use**: Enable for semantic validation of plugin usage in documentation. Improves detection accuracy but requires running Ollama service.

---

#### ChromaDB (Active)
**Purpose**: Vector database for RAG (truth data retrieval)
**Status**: Active, optional
**Version**: 0.6.3
**Configuration**:
```yaml
rag:
  enabled: true
  chroma_db_path: "./data/chroma"
```

**When to use**: Enable for RAG-enhanced truth validation. Allows semantic search over plugin definitions to find relevant documentation snippets.

---

#### PostgreSQL (Supported)
**Purpose**: Production database (alternative to SQLite)
**Status**: Supported, optional (SQLite default)
**Version**: Any recent version (tested with 12+)
**Configuration**:
```bash
export DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

**When to use**: Use for production deployments, multi-node setups, or when requiring advanced database features. Recommended for high-volume validation scenarios.

---

#### Redis (Optional - Not Default)
**Purpose**: Distributed L2 cache for multi-node deployments
**Status**: Optional (SQLite L2 cache is default)
**Version**: 5.0.1
**Current Implementation**: SQLite L2 cache (sufficient for most deployments)

##### Default: SQLite L2 Cache
TBCV uses **SQLite for the L2 cache by default**. This approach:
- Requires no external services
- Works perfectly for single-node deployments
- Provides adequate performance for typical validation workloads
- Simplifies deployment and reduces operational overhead

**Default Configuration**:
```yaml
caching:
  l2:
    backend: sqlite  # Default
    max_size_mb: 2048
    ttl_seconds: 3600
    database_path: "data/cache.db"
```

##### When to Use Redis Instead

Use Redis L2 cache **only** when:
1. **Multi-Node Deployments**: Multiple TBCV instances running in parallel
   - Allows shared cache across all instances
   - Reduces redundant validation computations
   - Improves system-wide performance

2. **High-Performance Requirements**: Load-balanced setups with many concurrent requests
   - Centralized cache improves cache hit ratio
   - Reduces per-node memory usage
   - Better for containerized/Kubernetes deployments

3. **Cache Persistence Across Restarts**: Need cache to survive instance restarts
   - SQLite cache is tied to instance
   - Redis maintains cache independently

##### When to Keep SQLite L2 Cache

Keep SQLite L2 cache (default) for:
1. **Single-Node Deployments**: Standalone server or single Docker container
2. **Development & Testing**: Local development environments
3. **Cost Optimization**: Avoid additional infrastructure (Redis server)
4. **Simplicity**: Fewer moving parts to manage and monitor

##### Redis Setup Guide

**Step 1: Install Redis**

```bash
# macOS with Homebrew
brew install redis
brew services start redis

# Linux (Ubuntu/Debian)
sudo apt-get install redis-server
sudo systemctl start redis-server

# Docker (Recommended for production)
docker run -d \
  --name tbcv-redis \
  -p 6379:6379 \
  redis:7-alpine

# Windows (via WSL2)
wsl
sudo apt-get install redis-server
sudo service redis-server start
```

**Step 2: Verify Redis Installation**

```bash
redis-cli ping
# Expected output: PONG
```

**Step 3: Configure TBCV to Use Redis**

Update `config/main.yaml`:
```yaml
caching:
  l2:
    backend: redis  # Switch from sqlite
    redis_url: "redis://localhost:6379"
    max_connections: 10
    timeout_seconds: 5
    ttl_seconds: 3600
    key_prefix: "tbcv:"
```

Or set environment variable:
```bash
export TBCV_CACHING_L2_BACKEND=redis
export TBCV_CACHING_L2_REDIS_URL=redis://localhost:6379
```

**Step 4: Restart TBCV Application**

```bash
# If using systemd
sudo systemctl restart tbcv

# If using Docker Compose
docker-compose restart tbcv
```

##### Redis Configuration Examples

**Basic Local Setup**:
```yaml
caching:
  l2:
    backend: redis
    redis_url: "redis://localhost:6379"
    db: 0  # Use database 0
```

**Multi-Node Deployment (Recommended)**:
```yaml
caching:
  l2:
    backend: redis
    redis_url: "redis://redis-cluster:6379"
    max_connections: 20
    timeout_seconds: 5
    connection_pool_size: 10
    retry_on_timeout: true
    retry_attempts: 3
```

**Docker Compose with Redis**:
```yaml
version: '3.8'

services:
  tbcv:
    build: .
    container_name: tbcv-app
    ports:
      - "8080:8080"
    environment:
      - TBCV_CACHING_L2_BACKEND=redis
      - TBCV_CACHING_L2_REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    container_name: tbcv-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  redis_data:
```

**Production Setup (AWS ElastiCache)**:
```yaml
caching:
  l2:
    backend: redis
    redis_url: "redis://your-cluster.xxxxx.ng.0001.use1.cache.amazonaws.com:6379"
    ssl: true
    ssl_certfile: "/etc/ssl/certs/ca-bundle.crt"
    max_connections: 50
```

##### Redis vs SQLite: Performance Comparison

| Aspect | SQLite L2 Cache | Redis |
|--------|----------------|-------|
| **Setup Complexity** | ✓ Simple (no extra service) | Requires Redis server |
| **Cache Sharing** | Per-instance only | Shared across all instances |
| **Memory Usage** | Per-instance | Centralized |
| **Persistence** | Instance restart loses cache | Survives restarts |
| **Multi-Node Support** | No | Yes |
| **Performance (single-node)** | Excellent | Excellent |
| **Performance (multi-node)** | Poor (duplicated) | Excellent (shared) |
| **Operational Cost** | Minimal | Moderate (Redis infrastructure) |
| **Scaling** | Limited | Excellent |

**Recommendation**: Start with SQLite L2 cache (default). Switch to Redis only when you have:
- Multiple TBCV instances, OR
- Strict performance requirements, OR
- Cache persistence requirements

##### Monitoring Redis Cache

```bash
# Check Redis connection
redis-cli ping

# Monitor cache operations
redis-cli MONITOR

# Check memory usage
redis-cli INFO memory

# Clear all cache (use with caution)
redis-cli FLUSHDB

# View cache keys
redis-cli KEYS "tbcv:*"

# Check specific cache entry
redis-cli GET "tbcv:validation:result:abc123"
```

##### Fallback & Failover

TBCV implements graceful degradation when Redis is unavailable:
- Cache operations fall back to SQLite if Redis unreachable
- System continues working (without distributed cache benefit)
- Errors logged for monitoring
- Consider Redis as **optional optimization, not critical dependency**

---

---

#### LangChain (Installed but Unused for RAG)
**Purpose**: LLM application framework
**Status**: In dependencies but NOT used for RAG implementation
**Version**: 0.3.21+
**Why**: Custom RAG implementation provides more flexibility and better control over plugin detection logic
**Configuration**: N/A

**Detailed Rationale:**
1. **Simplified Architecture**: Custom RAG with TruthManagerAgent, FuzzyDetectorAgent, and LLMValidatorAgent provides precise control
2. **Performance**: Direct ChromaDB integration optimized for TBCV's plugin detection workflow
3. **Maintainability**: Custom logic is easier to debug and modify without framework abstractions
4. **Hybrid Approach**: Combines fuzzy string matching (Levenshtein, Jaro-Winkler) with semantic search
5. **Reduced Complexity**: Avoids unnecessary abstractions from LangChain

**Custom RAG Components:**
- `agents/truth_manager.py`: Indexes 6,000+ plugins with 6 specialized indexes
- `agents/fuzzy_detector.py`: Implements specialized matching algorithms with context windows
- `agents/llm_validator.py`: Optional semantic validation using direct API calls
- ChromaDB: Direct vector DB access without framework wrapping

**Future Potential Uses:**
- Advanced multi-step agent orchestration with tool use
- Complex prompt engineering and few-shot learning patterns
- Cross-document semantic analysis
- Multi-provider LLM fallback chains

**Current Status**: TBCV successfully meets all production RAG requirements with custom implementation. LangChain remains in dependencies as a reserved dependency for future feature expansion without requiring additional installation steps.

---

#### Prometheus (Planned)
**Purpose**: Metrics collection and monitoring
**Status**: Configured but not implemented (see TASK-HIGH-003)
**Version**: N/A
**Configuration**: See config/main.yaml monitoring section

**Workaround**: Use structured logging + external log aggregation for monitoring until Prometheus is fully implemented.

---

#### Sentry (Optional)
**Purpose**: Error tracking and monitoring
**Status**: Optional (implementation depends on TASK-HIGH-004 decision)
**Version**: Latest (1.38.0+)
**Configuration**:
```bash
export SENTRY_DSN=your-sentry-dsn-here
```

See production_readiness.md for deployment configuration details.

---

#### Google GenAI (Supported)
**Purpose**: Gemini API for LLM fallback
**Status**: Supported, optional
**Version**: 1.39.1
**Configuration**:
```bash
export GOOGLE_API_KEY=your-api-key
```

**When to use**: Fallback when Ollama unavailable (not implemented yet). Provides alternative LLM capability using Google's Gemini API.

## Local Development

### Quick Start
```bash
# Clone repository
git clone <repository-url>
cd tbcv

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from core.database import db_manager; db_manager.initialize_database()"

# Start development server
uvicorn tbcv.api.server:app --reload --host 0.0.0.0 --port 8080
```

### Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install in development mode
pip install -e .

# Run tests
pytest tests/

# Start with auto-reload
uvicorn tbcv.api.server:app --reload
```

### IDE Configuration
- **VS Code**: Use Python extension, set interpreter to virtual environment
- **PyCharm**: Configure project interpreter
- **Debugging**: Use `uvicorn` with `--reload` flag

## Production Deployment

### Standalone Server
```bash
# Using Uvicorn
uvicorn tbcv.api.server:app --host 0.0.0.0 --port 8080 --workers 4

# Using Gunicorn
gunicorn tbcv.api.server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080

# With configuration file
uvicorn tbcv.api.server:app --host 0.0.0.0 --port 8080 --workers 4 --env-file .env
```

### Systemd Service (Linux)
```bash
# Create service file
sudo tee /etc/systemd/system/tbcv.service > /dev/null <<EOF
[Unit]
Description=TBCV Content Validation System
After=network.target

[Service]
Type=simple
User=tbcv
Group=tbcv
WorkingDirectory=/opt/tbcv
Environment=PATH=/opt/tbcv/venv/bin
ExecStart=/opt/tbcv/venv/bin/uvicorn tbcv.api.server:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable tbcv
sudo systemctl start tbcv
sudo systemctl status tbcv
```

### Windows Service
```bash
# Install pywin32
pip install pywin32

# Create service installer
python service_installer.py install

# Start service
net start TBCV

# Check status
sc query TBCV
```

## Docker Deployment

TBCV includes a ready-to-use `Dockerfile` and `docker-compose.yml` in the repository root.

### Dockerfile (Actual)
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data data/logs data/cache

# Run startup validation
RUN python startup_check.py || true

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health/live').raise_for_status()" || exit 1

# Set environment variables
ENV TBCV_SYSTEM_ENVIRONMENT=production \
    TBCV_SYSTEM_DEBUG=false \
    TBCV_SYSTEM_LOG_LEVEL=info \
    TBCV_SERVER_HOST=0.0.0.0 \
    TBCV_SERVER_PORT=8080

# Run the application
CMD ["python", "main.py", "--mode", "api", "--host", "0.0.0.0", "--port", "8080"]
```

### Docker Compose (Actual)
```yaml
version: '3.8'

services:
  tbcv:
    build: .
    container_name: tbcv-app
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
      - ./config:/app/config:ro
      - ./truth:/app/truth:ro
    environment:
      - TBCV_SYSTEM_ENVIRONMENT=production
      - TBCV_SYSTEM_DEBUG=false
      - TBCV_SYSTEM_LOG_LEVEL=info
      - TBCV_SERVER_HOST=0.0.0.0
      - TBCV_SERVER_PORT=8080
      - TBCV_DATABASE_URL=sqlite:///./data/tbcv.db
      - TBCV_PERFORMANCE_WORKER_POOL_SIZE=8
      - TBCV_PERFORMANCE_MAX_CONCURRENT_WORKFLOWS=50
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8080/health/live').raise_for_status()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Redis for distributed caching (not yet implemented)
  # redis:
  #   image: redis:7-alpine
  #   container_name: tbcv-redis
  #   ports:
  #     - "6379:6379"
```

### Building and Running
```bash
# Build image
docker build -t tbcv:latest .

# Run container
docker run -d \
  --name tbcv \
  -p 8080:8080 \
  -v tbcv_data:/app/data \
  tbcv:latest

# With Docker Compose
docker-compose up -d

# With Ollama
docker-compose --profile with-ollama up -d
```

## Cloud Deployment

### AWS EC2
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip -y

# Clone and setup
git clone <repository-url>
cd tbcv
pip install -r requirements.txt

# Configure environment
export TBCV_SERVER_HOST=0.0.0.0
export TBCV_SERVER_PORT=8080

# Start with systemd or use EC2 user data
```

### AWS ECS/Fargate
```yaml
# task-definition.json
{
  "family": "tbcv",
  "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "tbcv",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/tbcv:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "hostPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "TBCV_SYSTEM_ENVIRONMENT", "value": "production"},
        {"name": "TBCV_DATABASE_URL", "value": "postgresql://..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/tbcv",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Heroku
```yaml
# Procfile
web: uvicorn tbcv.api.server:app --host 0.0.0.0 --port $PORT

# runtime.txt
python-3.12

# requirements.txt (add gunicorn)
fastapi==0.100.0
uvicorn[standard]==0.20.0
gunicorn==20.1.0
# ... other dependencies
```

### Railway
```yaml
# railway.json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn tbcv.api.server:app --host 0.0.0.0 --port $PORT"
  }
}
```

## Database Configuration

### SQLite (Default - Currently Only Supported Backend)

TBCV currently uses **SQLite only**. PostgreSQL and MySQL support are planned but not yet implemented.

```bash
# Local file database (default)
export TBCV_DATABASE_URL=sqlite:///./data/tbcv.db

# In-memory (for testing)
export TBCV_DATABASE_URL=sqlite:///:memory:

# Custom path
export TBCV_DATABASE_URL=sqlite:///path/to/custom/database.db
```

**Note**: The SQLite database is created automatically on first run. For production deployments with high concurrency requirements, consider the following:
- Use SSD storage for the database file
- Configure WAL mode for better concurrent access
- Implement regular backups (see Backup section)

### Future Database Support (Not Yet Implemented)

PostgreSQL and MySQL support are planned for future releases. The configuration will use:

```bash
# PostgreSQL (planned)
# export TBCV_DATABASE_URL=postgresql://user:password@localhost:5432/tbcv

# MySQL (planned)
# export TBCV_DATABASE_URL=mysql+pymysql://user:password@localhost:3306/tbcv
```

## External Services Integration

### Ollama Setup
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull models
ollama pull llama2
ollama pull codellama

# Configure TBCV
export OLLAMA_BASE_URL=http://localhost:11434
```

### OpenAI Integration
```bash
# Set API key
export OPENAI_API_KEY=sk-your-api-key-here

# Configure as fallback
# config/main.yaml
llm_validator:
  provider: ollama
  fallback_providers:
    - openai
```

### GitHub Integration
```bash
# Generate personal access token
# Set in environment
export GITHUB_TOKEN=ghp_your_token_here
```

## Monitoring and Observability

### Health Checks
```bash
# Liveness probe
curl http://localhost:8080/health/live

# Readiness probe
curl http://localhost:8080/health/ready

# Detailed health
curl http://localhost:8080/health
```

### Logging
```bash
# View application logs
tail -f data/logs/tbcv.log

# Structured JSON logs
jq . data/logs/tbcv.log | head -10
```

### Error Tracking

Error tracking is implemented via **structured JSON logging** with optional log shipping to external services.

**Approach:**
- All errors logged to `logs/tbcv.log` with full context and stack traces
- Logs can be shipped to external error tracking services
- No external error tracking SDK (Sentry removed to reduce dependencies)

**Shipping Logs to External Services:**

**Option 1: Filebeat (Recommended)**
```bash
# Install Filebeat
curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-8.11.0-linux-x86_64.tar.gz
tar xzvf filebeat-8.11.0-linux-x86_64.tar.gz

# Configure filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /opt/tbcv/logs/tbcv.log
    json.message_key: msg
    json.keys_under_root: true

output.datadog:
  api_key: ${DATADOG_API_KEY}
  site: datadoghq.com

# Start Filebeat
./filebeat -c filebeat.yml
```

**Option 2: Cloud Provider Native Logging**
- AWS CloudWatch: EC2 CloudWatch agent
- Google Cloud: Cloud Logging agent
- Azure: Azure Monitor Agent

**Option 3: Open Source ELK Stack**
```yaml
# docker-compose.yml with ELK
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - xpack.security.enabled=false
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5000:5000"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
```

**Alternative Error Tracking Services:**
- **Datadog APM** - Full observability platform
- **New Relic** - Enterprise APM and error tracking
- **Splunk** - Enterprise logging and security
- **CloudWatch** (AWS) - Native AWS error tracking
- **Stackdriver** (Google Cloud) - Native GCP error tracking

### Metrics
```bash
# Prometheus metrics
curl http://localhost:8080/metrics

# System status
curl http://localhost:8080/admin/status
```

### Monitoring Setup

#### Current Status: Monitoring (Planned for Future Release)

**Note**: Prometheus metrics collection is currently **planned but not yet implemented**. The monitoring configuration is present in `config/main.yaml` but the `/metrics` endpoint is not yet functional.

#### Current Monitoring Options (Workaround)

Use the following approaches for production monitoring until Prometheus metrics are implemented:

**1. Structured Logging with Log Aggregation**:
```bash
# View JSON logs
tail -f data/logs/tbcv.log | jq .

# Export logs to external services (Datadog, New Relic, Splunk, CloudWatch)
# Use a log shipper agent or cloud native log aggregation service
```

**2. Health Check Endpoints**:
```bash
# Liveness probe (is service running?)
curl http://localhost:8080/health/live

# Readiness probe (is service ready to handle requests?)
curl http://localhost:8080/health/ready

# Detailed health status
curl http://localhost:8080/health

# System status and statistics
curl http://localhost:8080/admin/status
```

**3. Database Metrics Table**:
```bash
# Query custom application metrics from database
sqlite3 data/tbcv.db "SELECT * FROM metrics WHERE timestamp > datetime('now', '-1 hour');"
```

**4. Log-Based Monitoring Example**:
```bash
# Monitor validation success rate
grep "validations_total" data/logs/tbcv.log | jq .

# Track API response times
grep "processing_time_ms" data/logs/tbcv.log | jq '.processing_time_ms' | awk '{sum+=$1; count++} END {print "Average:", sum/count, "ms"}'

# Monitor error rates
grep "ERROR" data/logs/tbcv.log | wc -l
```

**5. Container-Based Monitoring**:
```yaml
# Docker Health Check (used in deployment)
healthcheck:
  test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8080/health/live').raise_for_status()"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

#### Future: Prometheus Metrics (Planned Implementation)

When Prometheus metrics are implemented in a future release, use this configuration:

```yaml
# prometheus.yml (future)
scrape_configs:
  - job_name: 'tbcv'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
```

## Security Considerations

### Network Security
```bash
# Use HTTPS in production
# Configure SSL/TLS certificates

# Firewall configuration
sudo ufw allow 8080/tcp
sudo ufw enable
```

### Application Security
```yaml
# config/production.yaml
server:
  enable_cors: false
  max_request_size_mb: 10

# Environment variables for secrets
export TBCV_SECRET_KEY=your-secret-key
export OPENAI_API_KEY=sk-...
```

### Data Protection
```bash
# Database encryption
# File system permissions
chmod 700 data/
chmod 600 data/tbcv.db

# Backup strategy
# Regular database dumps
# Encrypted backups
```

## Performance Tuning

### Resource Allocation
```yaml
# config/production.yaml
performance:
  worker_pool_size: 8
  max_concurrent_workflows: 100
  memory_limit_mb: 4096

cache:
  l1:
    max_memory_mb: 512
  l2:
    max_size_mb: 2048
```

### Scaling Strategies
```bash
# Horizontal scaling with load balancer
# Database read replicas
# Redis for distributed caching
# CDN for static assets
```

## Backup and Recovery

### Database Backup
```bash
# SQLite backup
sqlite3 data/tbcv.db ".backup backup.db"

# PostgreSQL backup
pg_dump tbcv > backup.sql

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
sqlite3 data/tbcv.db ".backup data/backup_$DATE.db"
find data/ -name "backup_*.db" -mtime +30 -delete
```

### Configuration Backup
```bash
# Backup configs
tar -czf config_backup.tar.gz config/

# Version control configs
git add config/
git commit -m "Backup production config"
```

### Disaster Recovery
```bash
# Restore from backup
cp backup.db data/tbcv.db

# Reinitialize if needed
python -c "from core.database import db_manager; db_manager.initialize_database()"

# Verify system health
curl http://localhost:8080/health/ready
```

## Troubleshooting Deployment

### Common Issues

**Port already in use**:
```bash
# Find process using port
lsof -i :8080
# or
netstat -tulpn | grep :8080

# Kill process
kill -9 <PID>
```

**Database connection failed**:
```bash
# Test connection
python -c "from core.database import db_manager; print(db_manager.is_connected())"

# Check database file permissions
ls -la data/tbcv.db
```

**Memory issues**:
```bash
# Monitor memory usage
htop
# or
ps aux --sort=-%mem | head

# Adjust limits in config
performance:
  memory_limit_mb: 2048
```

**Slow performance**:
```bash
# Check system resources
vmstat 1
iostat -x 1

# Profile application
python -m cProfile -s time main.py
```

### Diagnostic Commands
```bash
# System information
uname -a
python --version
pip list | grep -E "(fastapi|uvicorn|sqlalchemy)"

# TBCV diagnostics
curl http://localhost:8080/admin/status
python -m tbcv.cli check-agents
python startup_check.py
```

### Log Analysis
```bash
# Error patterns
grep "ERROR" data/logs/tbcv.log | tail -10

# Performance metrics
grep "processing_time_ms" data/logs/tbcv.log | sort -n

# Workflow failures
grep "workflow.*failed" data/logs/tbcv.log
```

## Maintenance Tasks

### Regular Maintenance
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Clear caches
curl -X POST http://localhost:8080/admin/cache/clear

# Database maintenance
python -c "from core.database import db_manager; db_manager.optimize_database()"

# Log rotation
logrotate /etc/logrotate.d/tbcv
```

### Automated Maintenance
```bash
# Cron job for daily maintenance
0 2 * * * /opt/tbcv/maintenance.sh

# maintenance.sh
#!/bin/bash
cd /opt/tbcv
source venv/bin/activate
python -m tbcv.cli status > /var/log/tbcv/daily_status.log
```

This comprehensive deployment guide covers all major scenarios from local development to production cloud deployments, with security, monitoring, and maintenance best practices.