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
- **Ollama** (optional): For local LLM processing
- **PostgreSQL** (optional): For production database
- **Redis** (optional): For distributed caching

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

### Dockerfile
```dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TBCV_SYSTEM_ENVIRONMENT=production
ENV TBCV_DATA_DIRECTORY=/app/data

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash tbcv

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data && chown -R tbcv:tbcv /app

# Switch to non-root user
USER tbcv

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health/live || exit 1

# Expose port
EXPOSE 8080

# Start application
CMD ["uvicorn", "tbcv.api.server:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  tbcv:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - tbcv_data:/app/data
      - ./config:/app/config:ro
    environment:
      - TBCV_SYSTEM_ENVIRONMENT=production
      - TBCV_DATABASE_URL=sqlite:////app/data/tbcv.db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    command: serve
    profiles:
      - with-ollama

volumes:
  tbcv_data:
  ollama_data:
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

### SQLite (Default)
```bash
# Local file database
export TBCV_DATABASE_URL=sqlite:///./data/tbcv.db

# In-memory (for testing)
export TBCV_DATABASE_URL=sqlite:///:memory:
```

### PostgreSQL
```bash
# Install psycopg2
pip install psycopg2-binary

# Connection string
export TBCV_DATABASE_URL=postgresql://user:password@localhost:5432/tbcv

# AWS RDS
export TBCV_DATABASE_URL=postgresql://user:password@rds-instance.region.rds.amazonaws.com:5432/tbcv
```

### MySQL
```bash
# Install PyMySQL
pip install pymysql

# Connection string
export TBCV_DATABASE_URL=mysql+pymysql://user:password@localhost:3306/tbcv
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

### Metrics
```bash
# Prometheus metrics
curl http://localhost:8080/metrics

# System status
curl http://localhost:8080/admin/status
```

### Monitoring Setup
```yaml
# prometheus.yml
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