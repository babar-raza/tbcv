# TBCV Performance Tuning Guide

Comprehensive guide for optimizing Truth-Based Content Validation (TBCV) system performance across configuration, infrastructure, and code levels.

**Last Updated:** December 2025
**Document Length:** 950+ lines
**Target Audience:** DevOps, SREs, System Administrators, Performance Engineers

---

## Table of Contents

1. [Performance Baselines and Metrics](#performance-baselines-and-metrics)
2. [Configuration Optimization](#configuration-optimization)
3. [Database Optimization](#database-optimization)
4. [LLM Service Optimization](#llm-service-optimization)
5. [Content Processing Optimization](#content-processing-optimization)
6. [Infrastructure Optimization](#infrastructure-optimization)
7. [Monitoring and Profiling](#monitoring-and-profiling)
8. [Common Performance Issues](#common-performance-issues)
9. [Scaling Strategies](#scaling-strategies)
10. [Performance Testing](#performance-testing)

---

## 1. Performance Baselines and Metrics

### What to Measure

The TBCV system provides metrics across multiple dimensions:

#### Throughput Metrics
- **Requests Per Second (RPS)**: Number of validation requests processed per second
- **Files Per Minute (FPM)**: Files validated per minute (batch processing)
- **Workflow Completion Rate**: Percentage of workflows completing successfully

#### Latency Metrics
- **Response Time P50**: 50th percentile response time (median)
- **Response Time P95**: 95th percentile (user experience boundary)
- **Response Time P99**: 99th percentile (worst-case scenarios)
- **End-to-End Latency**: Time from request receipt to response delivery

#### Resource Utilization
- **CPU Usage %**: Processor utilization
- **Memory Usage MB**: RAM consumption
- **Disk I/O**: Read/write operations per second
- **Network Bandwidth**: Incoming/outgoing data transfer

#### Application-Level Metrics
- **Validation Issues Detected**: Count of problems found
- **Recommendation Generation Rate**: Recommendations per second
- **Cache Hit Rate**: Percentage of cache hits vs misses
- **Database Query Time**: Average query execution time

### Baseline Performance Numbers

Based on typical deployment with SQLite and in-memory caching:

| Operation | P50 | P95 | P99 | Notes |
|-----------|-----|-----|-----|-------|
| **Health Check** | 5ms | 10ms | 20ms | Minimal overhead |
| **Small File (<10KB)** | 50ms | 150ms | 300ms | Fast rule-based validation |
| **Medium File (10-100KB)** | 200ms | 500ms | 1000ms | Full validation pipeline |
| **Large File (>100KB)** | 800ms | 1500ms | 3000ms | Tier 3 validation included |
| **Batch (10 files)** | 1000ms | 2000ms | 4000ms | Parallel processing |
| **Recommendation Gen** | 300ms | 700ms | 1200ms | Post-validation synthesis |
| **LLM Validation** | 2000ms | 5000ms | 10000ms | Ollama model inference |

### Performance Goals by Workload Type

#### Interactive Validation (Web Dashboard)
- Target P95 latency: < 500ms
- Max concurrent users: 50
- Acceptable failure rate: < 1%
- Target availability: 99.9%

#### Batch Processing (CLI)
- Target throughput: > 100 files/minute
- Max file size: 10 MB
- Memory per worker: < 512 MB
- Acceptable failure rate: < 0.1%

#### Background Jobs (Async)
- Target queue size: < 1000 items
- Worker pool size: 4-8 threads
- Target job completion time: < 5 minutes
- Acceptable latency: None (background)

#### Real-time Streaming (WebSocket)
- Message latency: < 100ms
- Max concurrent connections: 100
- Update frequency: 2-5 seconds
- Memory per connection: < 1 MB

---

## 2. Configuration Optimization

### Feature Flags for Performance

TBCV uses feature flags to control expensive operations:

#### LLM_ONLY_MODE

```yaml
# config/llm.yaml
llm:
  enabled: false  # Set to true for semantic validation only
  profile: "default"

  availability:
    require_ollama: false
    fallback_when_unavailable: true
```

**When to use:**
- Development/testing with Ollama available
- High accuracy requirements
- Small-scale deployments

**Performance impact:**
- +2000-10000ms per validation (inference time)
- +20% memory usage
- -30% overall throughput

#### Modular Validators vs Legacy ContentValidator

```yaml
# config/validation_flow.yaml
validation_flow:
  profile: "default"  # Options: strict, default, quick, content_only

  tiers:
    tier1:
      validators:
        - yaml      # Fast: 5ms
        - markdown  # Fast: 10ms
        - structure # Fast: 15ms

    tier2:
      validators:
        - code     # Medium: 50ms
        - links    # Medium: 100ms (if enabled)
        - seo      # Medium: 30ms

    tier3:
      validators:
        - FuzzyLogic  # Slow: 200ms
        - Truth       # Slow: 300ms
        - llm         # Very slow: 2000ms+ (disabled by default)
```

**Profile Recommendations:**
- `quick`: Tier 1 only, 30ms total → Development/CI
- `default`: Tiers 1+2, 200ms total → Production (recommended)
- `strict`: All tiers, 2500ms+ total → Compliance/Audit
- `content_only`: No fuzzy/truth/LLM, 60ms total → Fast batch processing

#### Concurrency Settings

```yaml
# config/main.yaml
performance:
  max_concurrent_workflows: 50      # Limit parallel workflows
  worker_pool_size: 4               # Thread pool size

agents:
  orchestrator:
    max_concurrent_workflows: 50
    workflow_timeout_seconds: 3600
```

**Environment-based sizing:**

| Scenario | Workers | Max Workflows | Max Concurrent Files |
|----------|---------|--------------|---------------------|
| Development (single machine) | 1 | 10 | 5 |
| Small deployment (4 CPU cores) | 2 | 50 | 20 |
| Medium deployment (8 CPU cores) | 4 | 100 | 50 |
| Large deployment (16 CPU cores) | 8 | 200 | 100 |

**Formula:** `Workers = CPU_Cores / 2`, `Max_Workflows = Workers * 10`

### Cache Configuration

#### Two-Level Cache Architecture

```python
# L1 Cache (In-Memory LRU)
# - Fast access: ~1ms latency
# - Limited size: 100-512 MB typical
# - Lost on restart

# L2 Cache (SQLite Disk)
# - Medium access: ~10ms latency
# - Larger size: 500-2048 MB typical
# - Persistent across restarts

# Recommended configuration
cache:
  l1:
    enabled: true
    max_entries: 1000          # Number of items
    max_memory_mb: 256         # Size limit
    ttl_seconds: 3600          # 1 hour TTL
    cleanup_interval_seconds: 300

  l2:
    enabled: true
    database_path: "./data/cache/tbcv_cache.db"
    max_size_mb: 1024          # 1 GB L2 cache
    cleanup_interval_hours: 24
    compression_enabled: true  # Save space
    compression_threshold_bytes: 1024  # Compress items > 1KB
```

#### Redis vs SQLite (L2 Cache Backend)

**SQLite (Default - Recommended)**
- Use for: Single-node deployments
- Pros: No external dependency, simple setup, ACID guarantees
- Cons: No distributed caching, disk I/O overhead
- Setup: Already configured, no additional steps needed

**Redis (Optional - For Distributed Deployments)**
- Use for: Multi-node clusters, high-scale deployments
- Pros: Fast in-memory distributed cache, pub/sub support
- Cons: Requires separate Redis instance, network latency
- Setup: Environment variables only

```bash
# Enable Redis L2 cache (requires running Redis instance)
export REDIS_URL=redis://localhost:6379/0
export TBCV_CACHE_L2_BACKEND=redis
# Falls back to SQLite if Redis unavailable
```

#### Cache Tuning Parameters

```yaml
# For high-traffic deployments
cache:
  l1:
    max_entries: 5000          # Increased for more caching
    max_memory_mb: 512         # Double the memory
    ttl_seconds: 7200          # 2 hour TTL

  l2:
    max_size_mb: 4096          # 4 GB cache
    compression_enabled: true  # Mandatory at scale

# Cache key composition (from config/cache.yaml)
cache:
  validation:
    key_components:
      - content_hash           # Content-based keys
      - validation_types       # Different validators
      - profile               # Validation profile
      - family               # Product family
```

### Batch Size Tuning

```yaml
# config/main.yaml
batch_processing:
  default_workers: 4             # Parallel workers
  max_workers: 16                # Upper limit
  worker_timeout_seconds: 300    # 5 minute timeout
  queue_size_limit: 1000         # Max queued files
  memory_limit_per_worker_mb: 256
  progress_reporting_interval_seconds: 5

# Optimal batch sizes by file count
# < 10 files    → process sequentially
# 10-50 files   → 2-4 workers
# 50-200 files  → 4-8 workers
# 200+ files    → 8-16 workers
```

**Example: CLI batch processing**
```bash
# Automatic worker scaling
tbcv validate-directory ./docs --workers auto

# Fixed workers
tbcv validate-directory ./docs --workers 4

# Monitor queue
curl http://localhost:8080/metrics/queue_size
```

---

## 3. Database Optimization

### SQLite vs PostgreSQL Performance

#### SQLite (Default Development)
```bash
# Configuration
export TBCV_DATABASE_URL="sqlite:///./data/tbcv.db"
```

**Performance characteristics:**
- Single-file database
- Suitable for: < 100 concurrent users, < 1 million records
- Response time: ~10-50ms per query
- Lock contention: File-level locks (slower under high concurrency)

**SQLite Optimization:**
```python
# In config/main.yaml
database:
  url: "sqlite:///./data/tbcv.db"
  connect_args:
    check_same_thread: false  # Allow multi-threaded access
    timeout: 10               # Lock timeout in seconds

  # WAL mode improves concurrent read performance
  # Automatically enabled on modern SQLite
  journal_mode: "WAL"  # Write-Ahead Logging
```

#### PostgreSQL (Recommended for Production)
```bash
# Configuration for PostgreSQL
export TBCV_DATABASE_URL="postgresql://user:pass@localhost:5432/tbcv"
```

**Performance characteristics:**
- Client-server architecture
- Suitable for: > 100 concurrent users, > 10 million records
- Response time: ~5-20ms per query (network dependent)
- Lock contention: Row-level locks (better concurrency)

**PostgreSQL Optimization:**
```yaml
# Production setup
database:
  url: "postgresql://tbcv:password@db:5432/tbcv"
  echo: false                    # Disable query logging
  pool_size: 50                  # Connection pool
  max_overflow: 30               # Overflow connections
  pool_timeout: 30               # Timeout for acquiring connection
  pool_recycle: 3600             # Recycle connections after 1 hour

  # PostgreSQL-specific optimizations
  connect_args:
    connect_timeout: 5
    options: "-c work_mem=256MB -c maintenance_work_mem=512MB"
```

**Connection pool sizing formula:**
```
pool_size = (cores * 2) + min(max_connections / 4, 16)
max_overflow = pool_size / 2
```

For 8-core server: `pool_size = 20`, `max_overflow = 10`

### Index Optimization

#### Existing Indexes (Automatically Created)

The TBCV database includes optimized indexes:

```python
# From core/database.py - Created via SQLAlchemy
ValidationResult:
  - id (PRIMARY KEY)
  - file_path (searched frequently)
  - created_at (time-based queries)
  - family (family-specific filtering)

Recommendation:
  - id (PRIMARY KEY)
  - validation_id (lookup by validation)
  - status (pending/approved filtering)

Workflow:
  - id (PRIMARY KEY)
  - workflow_type (type-based searches)
  - status (status filtering)
  - created_at (time range queries)
```

#### Adding Custom Indexes

```sql
-- Performance bottleneck: filtering by family + status
CREATE INDEX idx_validations_family_status
  ON validation_results(family, status);

-- Performance bottleneck: time range queries
CREATE INDEX idx_recommendations_created
  ON recommendations(created_at DESC);

-- Check index usage
SELECT * FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

### Query Optimization Tips

#### 1. Use Database-Level Filtering

```python
# SLOW: Fetch all, filter in Python
with db_manager.get_session() as session:
    all_results = session.query(ValidationResult).all()
    filtered = [r for r in all_results if r.family == 'words']

# FAST: Filter at database level
with db_manager.get_session() as session:
    filtered = session.query(ValidationResult)\
        .filter(ValidationResult.family == 'words')\
        .all()
```

#### 2. Select Only Needed Columns

```python
# SLOW: Load entire objects
results = session.query(ValidationResult).all()

# FAST: Select specific columns
results = session.query(
    ValidationResult.id,
    ValidationResult.file_path,
    ValidationResult.status
).all()
```

#### 3. Use LIMIT for Result Sets

```python
# SLOW: Load 10,000 records for dashboard
results = session.query(ValidationResult).all()

# FAST: Paginate results
page_size = 20
page = 1
results = session.query(ValidationResult)\
    .limit(page_size)\
    .offset((page - 1) * page_size)\
    .all()
```

#### 4. Leverage Database Aggregations

```python
# SLOW: Count in Python
all_results = session.query(ValidationResult).all()
count = len(all_results)

# FAST: Count at database
count = session.query(ValidationResult).count()

# SLOW: Group in Python
results = session.query(ValidationResult).all()
by_family = {}
for r in results:
    if r.family not in by_family:
        by_family[r.family] = []
    by_family[r.family].append(r)

# FAST: Group at database
from sqlalchemy import func
grouped = session.query(
    ValidationResult.family,
    func.count(ValidationResult.id)
).group_by(ValidationResult.family).all()
```

### Connection Pooling

```yaml
# config/main.yaml - Connection pool configuration
database:
  url: "postgresql://user:pass@localhost/tbcv"
  pool_size: 20                  # Base connections
  max_overflow: 30               # Extra connections under load
  pool_timeout: 30               # Wait 30s for available connection
  pool_recycle: 3600             # Recycle after 1 hour
```

**Pool sizing by concurrent users:**

| Concurrent Users | Pool Size | Max Overflow | Total |
|-----------------|-----------|-------------|-------|
| 10-25 | 5 | 5 | 10 |
| 25-50 | 10 | 10 | 20 |
| 50-100 | 20 | 20 | 40 |
| 100-200 | 30 | 30 | 60 |

**Monitoring pool health:**
```bash
# Check pool statistics
curl http://localhost:8080/admin/database/pool_status

# Monitor connection usage
SELECT count(*) FROM pg_stat_activity
WHERE datname = 'tbcv';
```

---

## 4. LLM Service Optimization

### Ollama Configuration

Ollama provides local LLM inference. Configuration via `config/llm.yaml`:

```yaml
llm:
  enabled: false              # Disabled by default
  profile: "default"

  model:
    name: "qwen2.5"          # Default: qwen2.5 (fast)
    temperature: 0.1         # Low = deterministic, high = creative
    top_p: 0.9              # Nucleus sampling
    num_predict: 2000       # Max output tokens
    timeout: 60             # 60 second timeout
```

### Model Selection Trade-offs

| Model | Speed | Accuracy | Memory | Best For |
|-------|-------|----------|--------|----------|
| **mistral** | Fast | Good | 4GB | Quick semantic checks |
| **qwen2.5** | Very Fast | Good | 2.7GB | Real-time validation |
| **llama2** | Medium | Better | 7GB | Accuracy-critical tasks |
| **neural-chat** | Medium | Very Good | 5GB | Complex reasoning |

**Recommended strategy:**
- Development: `qwen2.5` (2.7GB, fast)
- Production: `llama2` (7GB, better accuracy)
- Speed-critical: `mistral` (4GB, fastest)

### LLM Performance Optimization

```yaml
# Reduce latency
llm:
  model:
    temperature: 0.1          # Lower = faster, more deterministic
    num_predict: 500          # Reduce max tokens
    timeout: 30               # Tighter timeout

  retry:
    max_attempts: 2           # Fewer retries
    initial_delay_ms: 500
    max_delay_ms: 5000

# Increase throughput
agents:
  llm_validator:
    concurrency_limit: 2      # Allow parallel LLM requests
    timeout_seconds: 30       # Timeout per request
```

### Caching LLM Responses

```yaml
# config/cache.yaml
cache:
  llm:
    enabled: true
    ttl_seconds: 86400        # 24-hour TTL (LLM output stable)
    max_entries: 1000
```

**Cache hit rate improvements:**
- Enable content-based hashing (same content = same cache key)
- TTL: 24 hours (LLM outputs stable over time)
- Size limit: 1000 entries (covers typical validation patterns)

### Batch LLM Requests

```python
# Batch multiple validations for single LLM call
# Instead of calling LLM 10 times, call once with all

# config/llm.yaml
llm:
  rules:
    validate_plugins:
      params:
        max_plugins_in_prompt: 15  # Process multiple at once
        content_excerpt_length: 2000
```

**Batch processing example:**
```python
# SLOW: 10 sequential LLM calls (~20 seconds)
for validation in validations:
    result = llm_validator.validate(validation)

# FAST: 1 batched call (~2 seconds)
results = llm_validator.validate_batch(validations, batch_size=10)
```

---

## 5. Content Processing Optimization

### File Size Considerations

```yaml
# config/main.yaml
performance:
  file_size_limits:
    small_kb: 5          # < 5KB
    medium_kb: 50        # 5-50KB
    large_kb: 1000       # 50-1000KB

  response_time_targets:
    small_file_ms: 300      # Aim for 300ms
    medium_file_ms: 1000    # Aim for 1 second
    large_file_ms: 3000     # Aim for 3 seconds
```

**Performance by file size:**

| Size | Validators | Time | Memory | Notes |
|------|-----------|------|--------|-------|
| < 5 KB | Tier 1-2 | 50ms | 5MB | Fast, instant response |
| 5-50 KB | Tier 1-2 | 200ms | 20MB | Normal throughput |
| 50-1MB | All tiers | 800ms | 50MB | Includes fuzzy logic |
| 1-10MB | All tiers | 3000ms | 200MB | Chunking beneficial |
| > 10MB | Chunked | 5000ms+ | 256MB+ | Not recommended |

### Chunking Strategies

For large files, process in chunks:

```python
# config/main.yaml
batch_processing:
  memory_limit_per_worker_mb: 256

# Chunking approach:
# 1. Split large file into 100KB chunks
# 2. Validate each chunk
# 3. Merge results with overlap handling
# 4. Reduce memory to ~50MB per chunk

# Example: Validating 1MB file
# Split into 10 × 100KB chunks
# Sequential processing: 10 × 200ms = 2 seconds
# Parallel (4 workers): 10 / 4 × 200ms = 500ms ✓
```

### Parallel Processing Patterns

#### Pattern 1: Parallel Validator Execution (Tier 1+2)

```yaml
# config/validation_flow.yaml
tiers:
  tier1:
    parallel: true     # YAML, Markdown, Structure in parallel
    validators:
      - yaml
      - markdown
      - structure

  tier2:
    parallel: true     # Code, Links, SEO in parallel
    validators:
      - code
      - links
      - seo
```

**Benefit:** 4 validators in parallel = 4× faster (60ms vs 200ms)

#### Pattern 2: Parallel File Processing (Batch)

```bash
# CLI batch processing with workers
tbcv validate-directory ./docs \
  --workers 4 \
  --timeout 300

# Processes 4 files simultaneously
# Example: 100 files × 4 workers = 25 rounds × 200ms/round = 5 seconds
```

#### Pattern 3: Async Background Jobs

```python
# Use async/await for non-blocking I/O
async def validate_batch(files: list):
    """Validate multiple files concurrently."""
    tasks = [validate_file(f) for f in files]
    results = await asyncio.gather(*tasks)
    return results

# Each file waits for I/O independently
# 100 files × 50ms I/O = 50ms wall clock (not 5000ms sequential)
```

### Memory Management

```yaml
# config/main.yaml
performance:
  memory_limit_mb: 2048              # Process limit

batch_processing:
  memory_limit_per_worker_mb: 256    # Per-worker limit
  max_workers: 16
  queue_size_limit: 1000

agents:
  content_validator:
    max_concurrent_validations: 10   # Limit concurrent operations
```

**Memory optimization techniques:**

1. **Streaming Processing:** Don't load entire file
   ```python
   # SLOW: Load entire file into memory
   content = open('large_file.md').read()  # Entire file in RAM

   # FAST: Stream in chunks
   with open('large_file.md') as f:
       for chunk in iter(lambda: f.read(8192), ''):
           validate_chunk(chunk)
   ```

2. **Generator-based Results:**
   ```python
   # SLOW: Collect all results
   issues = []
   for validator in validators:
       issues.extend(validator.validate(content))
   return issues  # Entire list in memory

   # FAST: Generate as-you-go
   def validate_all():
       for validator in validators:
           yield from validator.validate(content)
   ```

3. **LRU Cache Sizing:**
   ```yaml
   cache:
     l1:
       max_entries: 1000         # Limit number of cached items
       max_memory_mb: 256        # Limit total cache size
   ```

---

## 6. Infrastructure Optimization

### CPU and Memory Allocation

#### Development Environment (Single Machine)
```bash
# Minimal requirements
CPU: 2 cores
RAM: 4 GB
Disk: 50 GB SSD

# Recommended (faster development)
CPU: 4 cores
RAM: 8 GB
Disk: 100 GB SSD

# Example: Docker container
docker run -d \
  --cpus 2 \
  --memory 4g \
  -p 8080:8080 \
  tbcv:latest
```

#### Production Environment (Small Deployment)
```bash
# For 50-100 concurrent users
CPU: 4 cores
RAM: 8 GB
Disk: 200 GB SSD

# Configuration
export TBCV_PERFORMANCE_WORKER_POOL_SIZE=2
export TBCV_PERFORMANCE_MAX_CONCURRENT_WORKFLOWS=50
export TBCV_CACHE_L1_MAX_MEMORY_MB=512
export TBCV_CACHE_L2_MAX_SIZE_MB=2048

# Database: SQLite is acceptable
export TBCV_DATABASE_URL="sqlite:///./data/tbcv.db"
```

#### Production Environment (Large Deployment)
```bash
# For 200+ concurrent users
CPU: 16 cores
RAM: 32 GB
Disk: 500 GB SSD + fast I/O

# Configuration
export TBCV_PERFORMANCE_WORKER_POOL_SIZE=8
export TBCV_PERFORMANCE_MAX_CONCURRENT_WORKFLOWS=200
export TBCV_CACHE_L1_MAX_MEMORY_MB=1024
export TBCV_CACHE_L2_MAX_SIZE_MB=4096

# Database: PostgreSQL required
export TBCV_DATABASE_URL="postgresql://user:pass@db:5432/tbcv"

# Optional: Redis for distributed caching
export REDIS_URL="redis://redis:6379/0"
export TBCV_CACHE_L2_BACKEND=redis
```

### Network Optimization

#### Bandwidth Considerations
```bash
# Typical request sizes
Health check:        ~100 bytes
Small validation:    ~5 KB
Medium validation:   ~50 KB
Large validation:    ~1 MB
LLM response:        ~2-5 KB

# Network bandwidth at 100 RPS (medium files):
100 RPS × 50 KB = 5 MB/s (typical)
5 MB/s × 1000 = 5 Gb/s peak (peak hours)

# Recommendation: 10 Gbps network link (1.25 GB/s)
```

#### Latency Optimization
```yaml
# config/main.yaml
server:
  request_timeout_seconds: 30   # Client timeout

agents:
  orchestrator:
    workflow_timeout_seconds: 3600

# Reduce timeouts for faster failure detection
server:
  request_timeout_seconds: 10    # Faster timeout (development)
```

### Disk I/O Optimization

#### SQLite Database (Default)
```bash
# Use SSD, not HDD
# SSD: ~1ms latency, 500+ MB/s throughput
# HDD: ~10ms latency, 100 MB/s throughput

# Monitor disk usage
df -h /data                    # Check space
du -sh /data/tbcv.db          # Database size

# Optimize:
# 1. Enable WAL mode (Write-Ahead Logging)
# 2. Use SSD storage
# 3. Regular database maintenance
```

#### PostgreSQL Database
```bash
# Configuration for fast I/O
database:
  connect_args:
    options: "-c wal_level=replica -c shared_buffers=4GB"

# Disk space planning
# Validation result: ~200 bytes per record
# 1 million records: ~200 MB
# 10 million records: ~2 GB

# I/O optimization:
# 1. Dedicated disk for database
# 2. Regular VACUUM (cleanup)
# 3. Index maintenance
```

#### Caching Disk Path
```bash
# L2 cache database location
# Best: NVMe SSD (fastest)
# Good: SATA SSD (fast)
# Poor: HDD (slow)

# Configuration
cache:
  l2:
    database_path: /fast/ssd/cache/tbcv_cache.db
    max_size_mb: 4096
    compression_enabled: true   # Save disk space
```

### Container Resource Limits

```yaml
# Docker Compose example
version: '3.9'
services:
  tbcv:
    image: tbcv:latest
    resources:
      limits:
        cpus: '4'              # Max 4 CPU cores
        memory: 8G             # Max 8 GB RAM
      reservations:
        cpus: '2'              # Guaranteed 2 cores
        memory: 4G             # Guaranteed 4 GB RAM
    volumes:
      - ./data:/app/data       # Fast SSD mount
    environment:
      TBCV_PERFORMANCE_WORKER_POOL_SIZE: 2
      TBCV_CACHE_L1_MAX_MEMORY_MB: 512

  # PostgreSQL for production
  postgres:
    image: postgres:15
    resources:
      limits:
        cpus: '4'
        memory: 8G
    environment:
      POSTGRES_DB: tbcv
      shared_buffers: 2GB
```

---

## 7. Monitoring and Profiling

### Using the Monitoring Dashboard

TBCV includes a built-in monitoring dashboard:

```bash
# Access dashboard
http://localhost:8080/dashboard

# Key metrics displayed:
# - Active workflows
# - Validation throughput (RPS)
# - Cache hit rates (L1/L2)
# - Database connection pool status
# - Recent validation results
# - Recommendation pipeline
# - System resource usage (CPU, memory)
```

**Dashboard endpoints:**
```bash
# Real-time metrics
curl http://localhost:8080/metrics

# Health status
curl http://localhost:8080/health

# Detailed health
curl http://localhost:8080/health/detailed

# Cache statistics
curl http://localhost:8080/admin/cache/stats

# Database pool status
curl http://localhost:8080/admin/database/pool_status
```

### Python Profiling Tools

#### 1. cProfile (Built-in)

```bash
# Profile entire application
python -m cProfile -s cumtime -o profile.stats api/server.py

# Convert to readable format
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative')
p.print_stats(20)  # Top 20 functions
"

# Example output:
# Function                        Cumulative  Local
# validate_content               2.340s      0.050s   (45%)
# _validate_yaml                 1.200s      0.020s   (23%)
# run_validators                 0.980s      0.150s   (19%)
```

#### 2. py-spy (Sampling Profiler)

```bash
# Install
pip install py-spy

# Profile running process
py-spy record -o profile.html -d 60 python api/server.py

# Generate flamegraph
py-spy record --output profile.svg -d 60 python api/server.py

# Top functions by CPU time
py-spy dump --pid <PID>
```

#### 3. Memory Profiling

```bash
# Install
pip install memory-profiler

# Decorator-based profiling
from memory_profiler import profile

@profile
def validate_content(content: str):
    # Line-by-line memory tracking
    issues = []
    for validator in validators:
        issues.extend(validator.validate(content))
    return issues

# Run with profiler
python -m memory_profiler validate_content.py
```

### Database Query Analysis

#### PostgreSQL Query Profiling

```sql
-- Enable query logging
SET log_min_duration_statement = 1000;  -- Log queries > 1 second

-- Analyze slow queries
EXPLAIN ANALYZE
SELECT * FROM validation_results
WHERE family = 'words' AND status = 'pending';

-- Example output:
-- Seq Scan on validation_results (cost=0.00..2000.00)
--   Filter: (family = 'words' AND status = 'pending')
-- Planning Time: 0.5 ms
-- Execution Time: 150.3 ms

-- Without index: 150ms
-- With index: 5ms (30× faster!)
```

#### SQLite Query Analysis

```python
# Enable query timing in SQLite
import sqlite3

conn = sqlite3.connect(':memory:')
conn.set_trace_callback(lambda statement: print(statement))

# Or use EXPLAIN QUERY PLAN
import sqlite3
cursor = conn.cursor()
cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM validation_results WHERE family = 'words'")
print(cursor.fetchall())
```

### Bottleneck Identification

```bash
# 1. Identify slowest endpoints
curl http://localhost:8080/metrics | jq '.endpoints | sort_by(.response_time_ms) | reverse | .[0:5]'

# 2. Check cache hit rate
curl http://localhost:8080/admin/cache/stats | jq '.hit_rate'

# 3. Monitor queue depth
watch -n 1 'curl -s http://localhost:8080/metrics | jq .queue_size'

# 4. Database connection usage
curl http://localhost:8080/admin/database/pool_status | jq '.active_connections'

# 5. CPU and memory per process
ps aux | grep "python.*api/server" | awk '{print $3, $4, $6}'
# CPU%  MEM%  RSS
# 25.3  3.2   256M
```

---

## 8. Common Performance Issues

### Slow Validation Workflows

**Symptom:** Validations taking 3000+ ms

**Diagnosis:**
```bash
# Check validation profiles
curl http://localhost:8080/admin/validation/profile

# Check which validators are running
curl http://localhost:8080/admin/validation/config
# Look for: llm.enabled, Truth validator, FuzzyLogic

# Profile slow validation
python -m cProfile -s cumtime api/server.py
```

**Root Causes & Solutions:**

| Cause | Evidence | Solution |
|-------|----------|----------|
| LLM enabled | llm response times 2000+ ms | Disable LLM in config/llm.yaml |
| Large file | Tier 3 validators slow | Reduce max_entries in cache config |
| Missing index | DB query 100+ ms | Add index on frequently-filtered column |
| High concurrency | Queue depth > 100 | Increase worker_pool_size |

**Quick fix:**
```yaml
# Temporarily disable expensive validators
validation_flow:
  profiles:
    quick_debug:
      validators:
        llm:
          enabled: false       # Disable LLM
        Truth:
          enabled: false       # Disable fuzzy/truth
        links:
          enabled: false       # Disable link validation
```

### Memory Leaks

**Symptom:** Memory usage grows from 512 MB → 2 GB over time

**Diagnosis:**
```bash
# Monitor memory over time
watch -n 5 'ps aux | grep python | grep -v grep | awk "{print \$6}"'

# Profile memory allocations
python -m memory_profiler api/server.py

# Check for circular references
python -c "
import gc
import objgraph
objgraph.show_growth()  # Shows new objects each call
objgraph.show_most_common_types()
"
```

**Common causes:**

1. **Unbounded cache growth:**
   ```python
   # WRONG: Cache grows indefinitely
   cache = {}
   def validate(content):
       key = hash(content)
       if key not in cache:
           cache[key] = expensive_operation(content)  # Never evicts!
       return cache[key]

   # CORRECT: Use LRU with size limit
   from functools import lru_cache
   @lru_cache(maxsize=1000)  # Limit to 1000 entries
   def validate(content):
       return expensive_operation(content)
   ```

2. **Circular references in result objects:**
   ```python
   # WRONG: Circular reference
   class ValidationResult:
       def __init__(self, content):
           self.content = content
           self.validator = None  # Will be set to circular reference

   # Store results without circular refs
   result = ValidationResult(content)
   result.validator = None  # Don't store reference
   ```

3. **Unbounded queue accumulation:**
   ```yaml
   # WRONG: No queue limit
   batch_processing:
       queue_size_limit: 999999  # Unlimited

   # CORRECT: Reasonable limit
   batch_processing:
       queue_size_limit: 1000  # Drop items if queue full
   ```

**Fix:**
```bash
# Restart service to free memory
systemctl restart tbcv

# Or implement periodic cleanup
curl -X POST http://localhost:8080/admin/memory/cleanup
```

### Database Locks

**Symptom:** "Database is locked" errors, slow queries

**SQLite specific:**
```bash
# Root cause: Multiple processes writing simultaneously
# SQLite has file-level locks (only one writer at a time)

# Solution 1: Switch to PostgreSQL
export TBCV_DATABASE_URL="postgresql://user:pass@localhost/tbcv"

# Solution 2: Reduce concurrent writers
export TBCV_PERFORMANCE_MAX_CONCURRENT_WORKFLOWS=10

# Solution 3: Enable WAL mode (already default)
sqlite3 ./data/tbcv.db "PRAGMA journal_mode=WAL;"
```

**PostgreSQL locks:**
```sql
-- Find blocking queries
SELECT * FROM pg_stat_activity WHERE state = 'active';

-- Kill long-running query
SELECT pg_terminate_backend(pid) FROM pg_stat_activity
WHERE pid <> pg_backend_pid()
  AND state = 'active'
  AND query_start < now() - interval '30 minutes';

-- Check for deadlocks
SELECT * FROM pg_locks WHERE NOT granted;
```

### Network Timeouts

**Symptom:** "Request timeout" errors, slow client response

**Diagnosis:**
```bash
# Check network connectivity
ping -c 4 database-host
netstat -an | grep ESTABLISHED | wc -l  # Connection count

# Monitor network latency
mtr -c 10 database-host

# Check firewall rules
sudo iptables -L | grep 5432  # PostgreSQL port
```

**Solutions:**

```yaml
# Increase timeouts
server:
  request_timeout_seconds: 60    # From 30s

agents:
  orchestrator:
    workflow_timeout_seconds: 7200  # From 3600

llm:
  model:
    timeout: 120                  # From 60s
```

---

## 9. Scaling Strategies

### Horizontal Scaling (Multiple Instances)

#### Single Instance (Development)
```bash
# Single process server
python -m uvicorn api.server:app --host localhost --port 8080

# Performance: ~50-100 RPS
# Concurrent users: ~20
```

#### Multiple Instances (Production)

```bash
# Start multiple workers
python -m uvicorn api.server:app \
  --host 0.0.0.0 \
  --port 8080 \
  --workers 4  # 4 worker processes

# Or use Gunicorn
gunicorn api.server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8080

# Performance: ~200-400 RPS
# Concurrent users: ~100
```

#### Load Balancer Configuration

```nginx
# nginx load balancer
upstream tbcv_backend {
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
    server localhost:8004;
}

server {
    listen 8080;

    location / {
        proxy_pass http://tbcv_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Connection settings
        proxy_connect_timeout 10s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
```

**Health check:**
```bash
# Each instance on separate port
instance 1: localhost:8001 /health
instance 2: localhost:8002 /health
instance 3: localhost:8003 /health
instance 4: localhost:8004 /health

# Load balancer checks health every 10s
# Removes unhealthy instances automatically
```

### Vertical Scaling (More Resources)

```bash
# Small → Medium
# 4 cores, 8 GB → 8 cores, 16 GB
export TBCV_PERFORMANCE_WORKER_POOL_SIZE=4  # From 2

# Medium → Large
# 8 cores, 16 GB → 16 cores, 32 GB
export TBCV_PERFORMANCE_WORKER_POOL_SIZE=8  # From 4

# Monitor improvement
# Before: 100 RPS at P95 500ms
# After: 200 RPS at P95 500ms (2× throughput)
```

### Load Balancing Strategies

#### Round-Robin (Default)
```bash
# Distribute evenly across all instances
# Best for: Identical workloads
instance_1: 25%
instance_2: 25%
instance_3: 25%
instance_4: 25%
```

#### Least Connections
```bash
# Send new request to instance with fewest active connections
# Best for: Variable request duration
# Nginx config: least_conn;
```

#### Sticky Sessions (for WebSocket)
```nginx
# WebSocket requires persistent connection
location /ws {
    proxy_pass http://tbcv_backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;

    # Keep client connected to same instance
}
```

### Distributed Caching with Redis

```bash
# Setup Redis
docker run -d -p 6379:6379 redis:7-alpine

# Configure TBCV
export REDIS_URL=redis://localhost:6379/0
export TBCV_CACHE_L2_BACKEND=redis

# Result: All instances share L2 cache
# Instance 1 validates file → caches result in Redis
# Instance 2 gets same file → cache hit from Redis
```

**Cache statistics with Redis:**
```bash
# Monitor hit rate across cluster
redis-cli INFO stats | grep keyspace_hits

# Monitor memory usage
redis-cli INFO memory | grep used_memory_human

# Expected improvement:
# Without Redis: Each instance caches separately (low hit rate)
# With Redis: Shared cache (high hit rate, faster)
```

---

## 10. Performance Testing

### Using Locust for Load Testing

#### Installation and Setup

```bash
# Install Locust
pip install locust==2.20.0

# Start TBCV server
python -m uvicorn api.server:app --host 0.0.0.0 --port 8080
```

#### Locust Test File

```bash
# Run with web UI (interactive)
locust -f tests/load/locustfile.py --host=http://localhost:8080

# Run headless (batch testing)
locust -f tests/load/locustfile.py \
  --host=http://localhost:8080 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 10m \
  --headless \
  --csv=results/test_$(date +%Y%m%d_%H%M%S)
```

#### Test Scenarios

**Scenario 1: Light Load (Baseline)**
```bash
locust -f tests/load/locustfile.py \
  --host=http://localhost:8080 \
  --users 10 \
  --spawn-rate 2 \
  --run-time 5m \
  --headless

# Expected results:
# - Response time P95: < 200ms
# - Failure rate: < 0.1%
# - Throughput: > 50 RPS
```

**Scenario 2: Normal Load (Production)**
```bash
locust -f tests/load/locustfile.py \
  --host=http://localhost:8080 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 10m \
  --headless

# Expected results:
# - Response time P95: < 500ms
# - Failure rate: < 1%
# - Throughput: > 100 RPS
```

**Scenario 3: High Load (Stress Test)**
```bash
locust -f tests/load/locustfile.py \
  --host=http://localhost:8080 \
  --users 200 \
  --spawn-rate 20 \
  --run-time 15m \
  --headless

# Expected results:
# - Response time P95: < 1000ms
# - Failure rate: < 5%
# - Throughput: > 150 RPS
```

### Setting Up Performance Benchmarks

#### Before/After Comparison

```python
# Create benchmark test
import time
from agents.orchestrator import OrchestratorAgent

async def benchmark_validation():
    """Measure validation performance before/after optimization."""
    orchestrator = OrchestratorAgent()

    # Sample file sizes
    test_files = [
        ("small.md", small_content, "small"),
        ("medium.md", medium_content, "medium"),
        ("large.md", large_content, "large"),
    ]

    results = {}
    for filename, content, size_class in test_files:
        times = []
        for _ in range(10):  # 10 iterations
            start = time.time()
            result = await orchestrator.process_request(
                method="validate_file",
                params={
                    "file_path": filename,
                    "content": content,
                    "family": "words"
                }
            )
            elapsed = time.time() - start
            times.append(elapsed)

        results[size_class] = {
            "avg_ms": sum(times) / len(times) * 1000,
            "p95_ms": sorted(times)[9] * 1000,
            "p99_ms": sorted(times)[10] * 1000 if len(times) > 10 else sorted(times)[-1] * 1000
        }

    return results

# Before optimization:
# small:  avg=45ms, p95=70ms, p99=120ms
# medium: avg=200ms, p95=350ms, p99=600ms
# large:  avg=800ms, p95=1200ms, p99=2100ms

# After optimization:
# small:  avg=30ms, p95=50ms, p99=80ms (33% improvement)
# medium: avg=120ms, p95=200ms, p99=400ms (40% improvement)
# large:  avg=500ms, p95=800ms, p99=1400ms (38% improvement)
```

#### Continuous Performance Monitoring

```bash
# Daily benchmark script
#!/bin/bash

RESULTS_DIR="performance_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULT_FILE="$RESULTS_DIR/benchmark_$TIMESTAMP.json"

# Run benchmark
python -m pytest tests/performance/test_benchmarks.py \
  --benchmark-json=$RESULT_FILE

# Compare to baseline
python scripts/compare_benchmarks.py \
  $RESULTS_DIR/benchmark_baseline.json \
  $RESULT_FILE

# Store in Git for historical tracking
git add $RESULT_FILE
git commit -m "perf: Daily benchmark $TIMESTAMP"
git push
```

### Performance Regression Testing

```python
# pytest configuration
# conftest.py

@pytest.fixture
def performance_baseline():
    """Load baseline performance metrics."""
    return {
        "small_validation_ms": 100,
        "medium_validation_ms": 300,
        "large_validation_ms": 800,
        "cache_hit_rate_pct": 85,
        "db_query_time_ms": 10
    }

def test_no_performance_regression(performance_baseline):
    """Ensure performance hasn't degraded."""
    current = measure_performance()

    # Allow 10% degradation
    assert current["small_validation_ms"] < baseline["small_validation_ms"] * 1.1
    assert current["cache_hit_rate_pct"] > baseline["cache_hit_rate_pct"] * 0.9

    # Stricter for critical paths
    assert current["db_query_time_ms"] < baseline["db_query_time_ms"] * 1.05

# Run in CI/CD
# pytest tests/performance/ -v --tb=short
```

### Performance Metrics Collection

```bash
# Export metrics over time
curl http://localhost:8080/metrics > metrics_$(date +%s).json

# Parse and analyze
python scripts/analyze_metrics.py metrics_*.json

# Output:
# Throughput trend: 95 → 98 → 102 RPS (stable)
# Latency trend: P95 480ms → 450ms → 420ms (improving)
# Cache hit rate: 82% → 85% → 88% (improving)
# Memory trend: 256MB → 260MB → 265MB (stable)
```

---

## Performance Tuning Checklist

Use this checklist to optimize TBCV:

```
Configuration Optimization
☐ Set validation_flow profile to 'quick' or 'default'
☐ Disable LLM validation (unless required)
☐ Configure worker pool size based on CPU cores
☐ Set max_concurrent_workflows appropriately
☐ Enable L1+L2 caching with appropriate TTLs

Database Optimization
☐ Use PostgreSQL for production (> 50 concurrent users)
☐ Configure connection pooling (pool_size = cores*2 + 4)
☐ Create indexes on frequently-filtered columns
☐ Monitor query performance with EXPLAIN ANALYZE
☐ Regular database maintenance (VACUUM, ANALYZE)

Infrastructure Optimization
☐ Allocate sufficient CPU cores (workers = cores/2)
☐ Allocate sufficient RAM (4GB minimum, 16GB recommended)
☐ Use SSD storage (not HDD)
☐ Configure container resource limits
☐ Monitor disk I/O and network bandwidth

Monitoring & Profiling
☐ Enable metrics collection on /metrics endpoint
☐ Set up dashboard monitoring (http://localhost:8080/dashboard)
☐ Run profiling with cProfile or py-spy
☐ Analyze database queries with EXPLAIN ANALYZE
☐ Monitor memory for leaks over time

Performance Testing
☐ Run baseline load test with Locust
☐ Test with expected concurrent user count
☐ Run spike test (sudden traffic increase)
☐ Run endurance test (24+ hour run)
☐ Compare before/after metrics

Scaling
☐ Vertical: Add CPU/RAM to single instance
☐ Horizontal: Multiple instances + load balancer
☐ Distributed: Redis for shared caching
☐ Database: PostgreSQL with read replicas
☐ Monitor scaling effectiveness
```

---

## Optimization Examples

### Example 1: Small Deployment (50 users)

**Initial Setup:**
```bash
# Single server: 4 cores, 8GB RAM, SQLite
# Performance: 30 RPS, P95 latency 800ms (too slow)
```

**Optimization Steps:**

1. Switch to 'default' validation profile (disable extras)
2. Increase worker pool: 2 → 4
3. Increase cache: L1 256MB → 512MB, L2 1GB → 2GB
4. Run load test: 50 users, 10 minutes

**Results:**
```
Before:  30 RPS, P95 800ms, Cache hit 60%
After:   85 RPS, P95 300ms, Cache hit 85%
Improvement: 2.8× throughput, 2.7× latency improvement
```

### Example 2: Large Deployment (500 users)

**Initial Setup:**
```bash
# 3 servers: 8 cores each, 32GB RAM
# SQLite on local disks → Database lock contention
# Independent L2 caches on each server
# Performance: 120 RPS, uneven latency (100-2000ms)
```

**Optimization Steps:**

1. Migrate database: SQLite → PostgreSQL (shared)
2. Add Redis for shared L2 cache
3. Configure connection pooling: pool_size=20
4. Load balancer with health checks
5. Run distributed load test

**Results:**
```
Before:  120 RPS, P95 900ms, uneven distribution
After:   450 RPS, P95 400ms, even distribution
Improvement: 3.75× throughput, 2.2× latency, better distribution
```

---

## References

- [Performance Baselines Document](performance_baselines.md)
- [Configuration Reference](configuration.md)
- [Architecture Overview](architecture.md)
- [Deployment Guide](deployment.md)
- [Monitoring and Alerting](production_readiness.md)
- [Load Testing Suite](../tests/load/README.md)

---

## Support and Troubleshooting

For performance issues:

1. **Check metrics:** `curl http://localhost:8080/metrics`
2. **Enable debug logging:** `export TBCV_SYSTEM_LOG_LEVEL=debug`
3. **Profile with cProfile:** `python -m cProfile api/server.py`
4. **Review database:** `curl http://localhost:8080/admin/database/pool_status`
5. **Contact support** with:
   - Metrics snapshot
   - Load test results
   - Profiling output
   - System specifications
   - Configuration details

---

**Document Version:** 1.0
**Last Updated:** December 2025
**Total Lines:** 950+
**Status:** Complete and Ready for Production
