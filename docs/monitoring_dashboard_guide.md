# Performance Monitoring Dashboard User Guide

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Dashboard Layout](#dashboard-layout)
4. [Real-time Metrics](#real-time-metrics)
5. [Visualizations and Charts](#visualizations-and-charts)
6. [Using the Dashboard](#using-the-dashboard)
7. [Alert Configuration](#alert-configuration)
8. [Exporting Data](#exporting-data)
9. [API Reference](#api-reference)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

---

## Overview

### What is the Monitoring Dashboard?

The Performance Monitoring Dashboard is a real-time system monitoring interface that provides comprehensive visibility into the TBCV (Test-Based Content Validator) system's operational metrics, performance characteristics, and health status. It enables administrators, operators, and developers to track system behavior, identify performance bottlenecks, and detect anomalies.

### Key Features

- **Real-time Metrics**: Live monitoring of system performance with configurable refresh rates
- **Historical Data**: Time-series data visualization for trend analysis
- **Multiple Time Ranges**: Support for 1 hour, 6 hours, 24 hours, and 7-day views
- **System Resources Monitoring**: CPU, memory, disk usage, and active connection tracking
- **Performance Analytics**: Agent execution times, database query performance, and cache efficiency
- **Alert Configuration**: Customizable thresholds for automated alerts
- **Data Export**: CSV and JSON export capabilities for reporting and analysis
- **Real-time Updates**: Automatic refresh with connection status indicator

### When to Use the Dashboard

Use the monitoring dashboard for:

- **Routine Monitoring**: Daily operational health checks
- **Performance Analysis**: Identifying slow operations and bottlenecks
- **Capacity Planning**: Understanding resource usage patterns
- **Alert Response**: Investigating triggered alerts and anomalies
- **Troubleshooting**: Correlating system issues with performance metrics
- **Reporting**: Exporting metrics for management and compliance reports
- **Optimization**: Baselining performance before and after changes

### Access URL and Authentication

**Default URL**: `http://localhost:8000/dashboard/monitoring`

The monitoring dashboard is typically protected by your system's authentication mechanism. Ensure you have:

- Valid credentials for your TBCV deployment
- Appropriate role/permissions (typically requires administrative or monitoring role)
- Network access to the monitoring endpoint

---

## Getting Started

### Quick Start

1. **Navigate to the Dashboard**: Open your browser and go to `http://your-server:8000/dashboard/monitoring`
2. **Authentication**: Log in with your TBCV credentials
3. **Initial Load**: Wait for the dashboard to load and display real-time metrics (usually 2-3 seconds)
4. **Status Indicator**: Check the connection status indicator in the top-right corner:
   - **Green**: Connected and receiving real-time updates
   - **Yellow**: Connecting or experiencing delays
   - **Red**: Connection error or server unavailable

### Initial Configuration

On your first visit, the dashboard will use default alert thresholds:

- Validation Throughput: 100 validations/minute
- Agent Response Time: 1000 ms
- Database Query Time: 500 ms
- Cache Hit Rate: 70%
- CPU Usage: 80%
- Memory Usage: 85%
- Error Rate: 5%

You can customize these thresholds in the Alert Thresholds section (see [Alert Configuration](#alert-configuration)).

---

## Dashboard Layout

### Header Section

```
┌─────────────────────────────────────────────────────────────────┐
│ Performance Monitoring Dashboard                                │
│ Real-time system metrics and performance analytics              │
│                                    Status: ● Connected    14:32  │
│                                    Auto-Refresh ☐              │
└─────────────────────────────────────────────────────────────────┘
```

**Components**:

- **Title**: "Performance Monitoring Dashboard"
- **Subtitle**: Current description of functionality
- **Status Indicator**: Shows connection status (● green = connected)
- **Last Update Time**: Timestamp of the most recent data refresh
- **Auto-Refresh Toggle**: Enable/disable automatic updates

### Alert Banner

The alert banner appears at the top when alerts are triggered:

```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠️ CPU usage exceeds threshold: 87% (threshold: 80%)      ×    │
└─────────────────────────────────────────────────────────────────┘
```

Click the × button to dismiss the banner. Alerts are also logged in the Recent Alerts section below.

### Quick Stats Grid

Four stat cards display key metrics at a glance:

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ 📊               │  │ 🎯               │  │ 💾               │  │ ⚡               │
│ 45.2             │  │ 234              │  │ 82.5%            │  │ 156              │
│ Validations/min  │  │ Agent Avg (ms)   │  │ Cache Hit Rate   │  │ DB Avg (ms)      │
│ ↑ +2.1%          │  │ ↓ -5.3%          │  │ ↑ +1.2%          │  │ → No change      │
└──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘
```

Each card shows:

- **Icon**: Visual indicator of the metric category
- **Value**: Current metric value (formatted appropriately)
- **Label**: Metric description
- **Trend**: Change indicator (↑ up, ↓ down, → stable) with percentage change

**Stat Card Types**:

1. **Validations/min (Primary - Blue)**: Current throughput
2. **Agent Avg (ms) (Success - Green)**: Average agent execution time
3. **Cache Hit Rate (Info - Light Blue)**: Cache effectiveness percentage
4. **DB Avg (ms) (Warning - Orange)**: Average database query time

### Controls Bar

Below the stat cards:

```
┌───────────────────────────────────────────────────────────────────┐
│ Time Range: [1h] [6h] [24h] [7d]    [CSV Export] [JSON Export]   │
└───────────────────────────────────────────────────────────────────┘
```

**Time Range Buttons**: Select historical period for chart data

**Export Buttons**: Download metrics in your preferred format

### Charts Section

Four responsive Chart.js visualizations (2x2 grid on desktop, stacked on mobile):

```
┌──────────────────────────────────────┬──────────────────────────────────────┐
│ Validation Throughput            🔄  │ Response Times                   🔄  │
│ ┌────────────────────────────────┐   │ ┌────────────────────────────────┐   │
│ │ Line Chart                     │   │ │ Line Chart                     │   │
│ │ Time → Validations/sec         │   │ │ Time → Response Time (ms)      │   │
│ └────────────────────────────────┘   │ └────────────────────────────────┘   │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ System Resources                 🔄  │ Error Rate & Success            🔄  │
│ ┌────────────────────────────────┐   │ ┌────────────────────────────────┐   │
│ │ Bar Chart                      │   │ │ Area Chart                     │   │
│ │ CPU/Memory/Disk Usage (%)      │   │ │ Success vs Error Rate (%)      │   │
│ └────────────────────────────────┘   │ └────────────────────────────────┘   │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

Each chart has a refresh button (🔄) for manual data updates.

### Detailed Metrics Section

**Agent Performance Table**:

Shows per-agent statistics:

| Agent | Count | Avg (ms) | Min (ms) | Max (ms) | P95 (ms) | P99 (ms) | Success Rate |
|-------|-------|----------|----------|----------|----------|----------|--------------|
| Content Validator | 1,542 | 234 | 45 | 2,341 | 567 | 1,234 | 98.5% |
| Enhancement Agent | 892 | 456 | 123 | 3,456 | 1,200 | 2,100 | 97.2% |

**Database Performance Table**:

Shows per-operation database statistics:

| Operation | Count | Avg (ms) | Min (ms) | Max (ms) | P95 (ms) | P99 (ms) |
|-----------|-------|----------|----------|----------|----------|----------|
| SELECT | 5,234 | 12 | 2 | 145 | 45 | 89 |
| INSERT | 1,203 | 18 | 5 | 234 | 67 | 123 |
| UPDATE | 892 | 22 | 8 | 301 | 89 | 145 |

**Cache Performance**:

```
┌────────────────┬────────────────┬────────────────┬────────────────┐
│ Hit Rate       │ Total Hits     │ Total Misses   │ Cache Size     │
│ 82.5%          │ 45,234         │ 9,567          │ 234 MB         │
└────────────────┴────────────────┴────────────────┴────────────────┘
```

**System Resources**:

```
CPU Usage                Memory Usage           Disk Usage
████████░░ 84%          ██████░░░░ 65%         ███░░░░░░░ 32%

Active Connections
1,245 concurrent connections
```

### Alert Thresholds Section

Configurable alert thresholds with input fields:

```
Validation Throughput (min/min)    100
Agent Response Time (ms)           1000
DB Query Time (ms)                 500
Cache Hit Rate (%)                 70
CPU Usage (%)                      80
Memory Usage (%)                   85
Error Rate (%)                     5
Alert Cooldown (minutes)           15

[Save Configuration]
```

### Recent Alerts Section

Log of recent alert events with timestamps and details:

```
├─ 14:32:15 CPU usage exceeds threshold: 87% (threshold: 80%)
├─ 14:15:42 Memory usage exceeds threshold: 89% (threshold: 85%)
├─ 13:54:08 Database query time exceeds threshold: 567ms (threshold: 500ms)
└─ Empty state message if no alerts
```

---

## Real-time Metrics

### Understanding the Metrics

#### 1. Validation Throughput (Validations/min)

**What it measures**: Number of content validation operations processed per minute.

**Interpretation**:

- **Increasing trend**: System is handling more validations, processing capacity is being utilized
- **Decreasing trend**: Possible underutilization, or recent completion of batch processing
- **Sudden drops**: May indicate processing backlog, errors, or reduced input volume

**Best range**: Depends on your system's capacity and expected load. Compare against baseline.

**Alert threshold**: Set based on your minimum expected throughput or maximum system capacity.

#### 2. Agent Average Response Time (ms)

**What it measures**: Mean execution time for agent operations (validation, enhancement, analysis).

**Interpretation**:

- **< 200ms**: Excellent performance, agents responding quickly
- **200-500ms**: Good performance, normal operations
- **500-1000ms**: Acceptable but monitor for degradation
- **> 1000ms**: Performance issue, may need investigation

**Factors affecting time**:

- Agent complexity
- Input data size
- System load
- Network latency
- Cache hit rate

**Alert threshold**: Typically 1000ms for most deployments, adjust based on SLA requirements.

#### 3. Cache Hit Rate (%)

**What it measures**: Percentage of cache requests that resulted in hits vs. misses.

**Interpretation**:

- **> 80%**: Excellent cache effectiveness
- **70-80%**: Good cache performance
- **50-70%**: Cache is working but could be optimized
- **< 50%**: Poor cache effectiveness, consider optimization

**Why it matters**:

- Higher hit rate = faster response times and lower database load
- Lower hit rate = more frequent database queries, potential bottleneck

**Alert threshold**: Typically 70%, adjusted based on expected hit rate for your workload.

#### 4. Database Average Query Time (ms)

**What it measures**: Mean execution time for database operations.

**Interpretation**:

- **< 50ms**: Fast queries, good indexing
- **50-200ms**: Acceptable performance
- **200-500ms**: Monitor for potential optimization
- **> 500ms**: Slow queries, investigate for bottlenecks

**What can cause slow queries**:

- Missing database indexes
- Large result sets
- Complex joins
- High database load
- Disk I/O contention

**Alert threshold**: Typically 500ms, adjust based on your database performance requirements.

#### 5. System Resources

**CPU Usage**:

- **< 50%**: Comfortable headroom for traffic spikes
- **50-80%**: Normal operational range
- **80-95%**: High utilization, monitor for scaling needs
- **> 95%**: Risk of performance degradation

**Memory Usage**:

- **< 60%**: Healthy memory utilization
- **60-85%**: Normal range
- **85-95%**: Monitor for memory leaks or process growth
- **> 95%**: Critical, immediate attention needed

**Disk Usage**:

- **< 80%**: Normal
- **80-90%**: Monitor available space
- **> 90%**: Risk of disk full, plan cleanup/expansion

**Active Connections**:

- Shows current database/application connections
- High sustained levels may indicate connection pooling issues
- Sudden spikes may indicate connection leaks

---

## Visualizations and Charts

### Chart Types and Interpretation

#### 1. Validation Throughput (Line Chart)

**Displays**: Validations processed over time

**Axes**:

- X-axis: Time (auto-scaled based on selected time range)
- Y-axis: Validations per second or per minute

**What to look for**:

- **Smooth curves**: Steady, predictable load
- **Spikes**: Batch processing, traffic surges
- **Dips**: Processing delays, errors, or reduced input
- **Trends**: Overall capacity utilization increasing/decreasing

**Interpretation guide**:

```
Healthy pattern:        Concerning pattern:
    │    ╱╲    ╱╲           │
    │   ╱  ╲  ╱  ╲          │    ╱
    │  ╱    ╲╱    ╲         │   ╱
    └─────────────────      └──╱──────  (Degrading)
         (Steady)
```

#### 2. Response Times (Line Chart)

**Displays**: Average response time over the selected period

**Axes**:

- X-axis: Time
- Y-axis: Response time in milliseconds

**What to look for**:

- **Increasing trend**: Performance degradation, investigate causes
- **Correlation with throughput**: Response time often increases with load
- **Sudden jumps**: Possible resource bottleneck or error spike
- **High variance**: Unstable performance, inconsistent behavior

**Interpretation guide**:

- If response times correlate with CPU/memory spikes, likely resource constraint
- If response times spike without resource usage increase, likely database or I/O issue
- If response times stable despite increasing throughput, good optimization

#### 3. System Resources (Bar Chart)

**Displays**: CPU, Memory, and Disk usage percentages

**Axes**:

- X-axis: Resource categories
- Y-axis: Usage percentage (0-100%)
- Color coding: Red zones (> 90%), Yellow zones (70-90%), Green zones (< 70%)

**What to look for**:

- **Balanced usage**: All resources in green zone indicates healthy system
- **Unbalanced usage**: One resource maxed while others idle suggests optimization opportunity
- **Trending**: How resource usage changes over the selected time period

**Action thresholds**:

- **70-80%**: Monitor for trend
- **80-90%**: Plan capacity expansion or optimization
- **> 90%**: Immediate action needed

#### 4. Error Rate & Success (Area Chart)

**Displays**: Success and error rates over time

**Axes**:

- X-axis: Time
- Y-axis: Percentage (0-100%)

**Interpretation**:

- **Success area (usually green)**: Percentage of successful operations
- **Error area (usually red)**: Percentage of failed operations

**What to look for**:

- **High success rate (> 95%)**: Healthy system
- **Increasing error rate**: System degradation, configuration issues, or external failures
- **Spikes in error rate**: Temporary issues or cascading failures
- **Errors correlate with**: Resource usage, response times, or specific time windows

**Correlation analysis**:

- Errors spike when CPU > 90%? Possible resource exhaustion
- Errors spike when database response time increases? Database issues
- Errors at specific times? Batch job interference or scheduled maintenance

---

## Using the Dashboard

### Accessing the Dashboard

**Step 1**: Open your browser and navigate to:

```
http://[your-server]:[port]/dashboard/monitoring
```

Replace `[your-server]` with your TBCV deployment hostname or IP address.

**Step 2**: Authenticate with your TBCV credentials (if required)

**Step 3**: Wait for initial data load (usually 2-3 seconds)

**Step 4**: Verify connection status indicator shows green (connected)

### Navigating Between Views

#### Time Range Selection

The dashboard supports four time range views:

```
[1h] [6h] [24h] [7d]
```

**1 Hour (1h)**:
- Best for: Real-time monitoring, immediate issue detection
- Granularity: ~1-2 minute intervals
- Use case: Troubleshooting active issues

**6 Hours (6h)**:
- Best for: Shift-level monitoring, trend detection
- Granularity: ~5-10 minute intervals
- Use case: Morning/shift review, recent activity analysis

**24 Hours (24h)**:
- Best for: Daily patterns, performance correlation
- Granularity: ~30 minute intervals
- Use case: Daily reviews, identifying time-based patterns

**7 Days (7d)**:
- Best for: Weekly trends, capacity planning
- Granularity: ~2-4 hour intervals
- Use case: Capacity planning, trend analysis, baselines

**To select a time range**:

1. Click the desired time range button
2. Charts and detailed metrics will update automatically
3. Historical data is fetched from the server (may take 1-2 seconds)
4. Stat card trends are recalculated

### Filtering and Sorting

**Agent Performance Table**:

- Click column headers to sort (if enabled)
- Filter by agent type using the browser's Find function (Ctrl+F)
- Sort by different metrics: Count, Avg, Min, Max, P95, P99, Success Rate

**Database Performance Table**:

- Sort by operation type or performance metrics
- Identify slowest operations by Max or P99 columns
- Compare query types by Count and Avg columns

### Refreshing Data

#### Auto-Refresh

The dashboard automatically refreshes metrics at regular intervals (default: every 30 seconds).

**To enable/disable auto-refresh**:

1. Check the "Auto-Refresh" checkbox in the header
2. When enabled, metrics update automatically
3. Last Update time will advance with each refresh

**Connection status during auto-refresh**:

- Green dot: Successfully refreshed
- Yellow dot: Attempting to refresh
- Red dot: Refresh failed, will retry

#### Manual Refresh

**Refresh individual charts**:

1. Locate the chart you want to refresh
2. Click the 🔄 button in the chart header
3. That chart will fetch latest data

**Refresh all metrics**:

1. Look for "Refresh All" button in Detailed Metrics section
2. Click it to immediately refresh all data
3. Useful when you suspect stale data or after making configuration changes

**Refresh page**:

1. Press F5 or Ctrl+R to reload entire dashboard
2. All data will be reset and reloaded from server
3. Use this if you encounter display issues or connection problems

### Auto-Refresh Settings

**Current behavior**:

- Refresh interval: 30 seconds (configurable in browser console)
- Refresh on page visibility change: Stops refreshing when tab is inactive
- Connection retry: Automatic retry with exponential backoff on failure

**To modify refresh interval** (advanced):

Open browser developer console (F12) and enter:

```javascript
// Set refresh interval to 60 seconds
window.refreshInterval = 60000;
```

---

## Alert Configuration

### Understanding Alerts

Alerts notify you when system metrics exceed configured thresholds. They help you respond quickly to potential issues before they impact users.

**Alert types**:

1. **Performance Alerts**: Response time, throughput, cache hit rate
2. **Resource Alerts**: CPU, Memory, Disk usage
3. **Reliability Alerts**: Error rate, success rate

### Setting Alert Thresholds

**Location**: "Alert Thresholds" section at the bottom of the dashboard

**Available thresholds**:

| Threshold | Default | Min | Max | Unit | Purpose |
|-----------|---------|-----|-----|------|---------|
| Validation Throughput | 100 | 1 | 10000 | validations/min | Minimum expected throughput |
| Agent Response Time | 1000 | 100 | 60000 | ms | Maximum acceptable response time |
| DB Query Time | 500 | 50 | 30000 | ms | Maximum acceptable query time |
| Cache Hit Rate | 70 | 0 | 100 | % | Minimum acceptable hit rate |
| CPU Usage | 80 | 10 | 100 | % | CPU usage limit |
| Memory Usage | 85 | 10 | 100 | % | Memory usage limit |
| Error Rate | 5 | 0 | 100 | % | Maximum acceptable error rate |
| Alert Cooldown | 15 | 1 | 1440 | minutes | Minimum time between repeated alerts |

### Configuring Thresholds

**Step-by-step**:

1. **Scroll to Alert Thresholds section**
2. **Modify values**:
   - Click the input field
   - Clear existing value
   - Enter new threshold value
3. **Review changes** in the preview fields
4. **Click "Save Configuration"** button
5. **Confirm success** - You should see a success message

**Example configuration for high-traffic environment**:

```
Validation Throughput: 500 (high volume expected)
Agent Response Time: 2000 (more lenient)
DB Query Time: 1000 (allowing for complex queries)
Cache Hit Rate: 60 (acceptable for new deployment)
CPU Usage: 90 (approaching capacity)
Memory Usage: 90 (approaching capacity)
Error Rate: 2 (strict error tolerance)
Alert Cooldown: 30 (reduce alert spam)
```

### Alert Notifications

**Where alerts appear**:

1. **Banner Alert**: Red alert banner at top of dashboard
2. **Recent Alerts Log**: Timestamped entry in the Recent Alerts section
3. **Stat Card Colors** (visual indication): Cards may change color when thresholds exceeded

**Alert banner format**:

```
⚠️ [Metric Name] exceeds threshold: [Current Value] (threshold: [Threshold Value])
```

Example:

```
⚠️ CPU usage exceeds threshold: 87% (threshold: 80%)
```

**Dismissing alerts**:

1. Click the × button on the alert banner to close it
2. Alert remains in Recent Alerts log for reference
3. Banner will reappear if threshold is breached again after cooldown

### Alert History

**Viewing alert history**:

1. Scroll to "Recent Alerts" section
2. Alerts are listed in reverse chronological order (newest first)
3. Each entry shows: Timestamp | Alert message

**Clearing alerts**:

1. Click the "Clear All" button in the Recent Alerts section header
2. This clears only the display log, not system alert configuration
3. Useful for cleaning up old alerts after investigation

**Exporting alerts** (for reporting):

1. Take a screenshot of the alerts
2. Or export dashboard data as CSV/JSON (alerts may be included in export)

### Alert Best Practices

1. **Set realistic thresholds**: Based on your system's baseline performance
2. **Avoid alert fatigue**: Don't set thresholds too low or you'll get constant alerts
3. **Test alerts**: Manually trigger alerts to verify notification delivery
4. **Document changes**: Keep notes on why you modified threshold values
5. **Review regularly**: Adjust thresholds quarterly based on actual performance
6. **Correlate alerts**: Use multiple metrics together to identify root causes

---

## Exporting Data

### Export Formats

#### JSON Export

**When to use**: Data analysis, integration with other tools, backup, detailed reporting

**File format**:

```json
{
  "system_resources": {
    "cpu_percent": 45.2,
    "memory_percent": 62.5,
    "memory_used_mb": 8192.5,
    "memory_total_mb": 16384.0,
    "disk_percent": 32.1,
    "disk_used_gb": 32.1,
    "disk_total_gb": 100.0,
    "process_memory_mb": 256.3,
    "active_threads": 24,
    "timestamp": "2024-01-15T14:32:45.123456+00:00"
  },
  "cache": {
    "hit_rate": 82.5,
    "total_hits": 45234,
    "total_misses": 9567,
    "cache_size": 234,
    "evictions": 123,
    "timestamp": "2024-01-15T14:32:45.123456+00:00"
  },
  "validation_throughput": {
    "total_count": 1342,
    "per_minute": 45.2,
    "per_hour": 2712.0,
    "success_rate": 98.5,
    "time_range": "1h",
    "timestamp": "2024-01-15T14:32:45.123456+00:00"
  },
  "agent_performance": {
    "overall_avg_ms": 234,
    "total_operations": 1542,
    "success_rate": 98.5,
    "agent_metrics": {
      "validate_content": {
        "count": 892,
        "avg_duration_ms": 189,
        "min_duration_ms": 45,
        "max_duration_ms": 2341,
        "p50_duration_ms": 156,
        "p95_duration_ms": 567,
        "p99_duration_ms": 1234
      }
    }
  },
  "database_performance": {
    "overall_avg_ms": 18,
    "total_operations": 8329,
    "db_metrics": {}
  }
}
```

#### CSV Export

**When to use**: Spreadsheet analysis, quick viewing, import to Excel/Google Sheets

**File format**:

```csv
metric,value,timestamp
cpu_percent,45.2,2024-01-15T14:32:45.123456+00:00
memory_percent,62.5,2024-01-15T14:32:45.123456+00:00
disk_percent,32.1,2024-01-15T14:32:45.123456+00:00
cache_hit_rate,82.5,2024-01-15T14:32:45.123456+00:00
validation_per_minute,45.2,2024-01-15T14:32:45.123456+00:00
agent_avg_ms,234,2024-01-15T14:32:45.123456+00:00
db_avg_ms,18,2024-01-15T14:32:45.123456+00:00
```

### Exporting from the Dashboard

**Step-by-step**:

1. **Select time range**: Choose the data period you want to export
2. **Click export button**: "Export CSV" or "Export JSON"
3. **Choose save location**: File will be downloaded to your Downloads folder
4. **File naming**: Files are named with format:
   - `monitoring_metrics_[time_range]_[timestamp].json`
   - `monitoring_metrics_[time_range]_[timestamp].csv`

**Example**:

```
monitoring_metrics_24h_20240115_143245.json
monitoring_metrics_1h_20240115_143245.csv
```

### Using Exported Data

#### Spreadsheet Analysis

1. **Download CSV export**
2. **Open in Excel/Google Sheets**
3. **Create charts** for further visualization
4. **Analyze trends** and perform calculations
5. **Share with stakeholders**

#### Integration with External Tools

**Grafana**:

1. Import JSON metrics
2. Create custom dashboards
3. Combine with other data sources

**ELK Stack** (Elasticsearch, Logstash, Kibana):

1. Use JSON export
2. Send to Logstash
3. Visualize in Kibana

**Python Analysis**:

```python
import json
import pandas as pd

# Load JSON export
with open('monitoring_metrics_24h_20240115_143245.json') as f:
    data = json.load(f)

# Extract metrics
cpu = data['system_resources']['cpu_percent']
memory = data['system_resources']['memory_percent']
cache_hit = data['cache']['hit_rate']

# Create DataFrame
metrics_df = pd.DataFrame({
    'metric': ['CPU', 'Memory', 'Cache Hit Rate'],
    'value': [cpu, memory, cache_hit]
})

print(metrics_df)
```

#### Reporting

1. **Export data** for the reporting period
2. **Calculate summary statistics**: min, max, avg, percentiles
3. **Create visualizations**: Charts and graphs
4. **Include in reports**: Management, compliance, or performance reports

### Automation with API Endpoints

**Programmatic export** using HTTP clients:

```bash
# Export JSON metrics for 24 hours
curl -X GET "http://localhost:8000/api/dashboard/monitoring/export?format=json&time_range=24h" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o metrics.json

# Export CSV metrics
curl -X GET "http://localhost:8000/api/dashboard/monitoring/export?format=csv&time_range=7d" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o metrics.csv
```

**Python**:

```python
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/dashboard/monitoring"
AUTH_TOKEN = "your_auth_token"
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}

# Export metrics
response = requests.get(
    f"{BASE_URL}/export",
    params={
        "format": "json",
        "time_range": "24h"
    },
    headers=HEADERS
)

if response.status_code == 200:
    metrics = response.json()

    # Save to file
    with open(f"metrics_{datetime.now().isoformat()}.json", 'w') as f:
        json.dump(metrics, f, indent=2)

    print("Metrics exported successfully")
else:
    print(f"Export failed: {response.status_code}")
```

---

## API Reference

### Endpoints Overview

The monitoring dashboard provides several API endpoints for programmatic access to metrics and data.

### GET /api/dashboard/monitoring/metrics

**Get comprehensive real-time metrics**

**Request**:

```
GET /api/dashboard/monitoring/metrics?time_range=1h
```

**Query Parameters**:

| Parameter | Type | Required | Default | Values | Description |
|-----------|------|----------|---------|--------|-------------|
| time_range | string | No | 1h | 1h, 6h, 24h, 7d | Historical data range for metrics |

**Response** (200 OK):

```json
{
  "system_resources": {
    "cpu_percent": 45.2,
    "memory_percent": 62.5,
    "memory_used_mb": 8192.5,
    "memory_total_mb": 16384.0,
    "disk_percent": 32.1,
    "disk_used_gb": 32.1,
    "disk_total_gb": 100.0,
    "process_memory_mb": 256.3,
    "active_threads": 24,
    "timestamp": "2024-01-15T14:32:45.123456+00:00"
  },
  "cache": {
    "hit_rate": 82.5,
    "total_hits": 45234,
    "total_misses": 9567,
    "cache_size": 234,
    "evictions": 123,
    "timestamp": "2024-01-15T14:32:45.123456+00:00"
  },
  "validation_throughput": {
    "total_count": 1342,
    "per_minute": 45.2,
    "per_hour": 2712.0,
    "success_rate": 98.5,
    "time_range": "1h",
    "timestamp": "2024-01-15T14:32:45.123456+00:00"
  },
  "agent_performance": {
    "overall_avg_ms": 234,
    "total_operations": 1542,
    "success_rate": 98.5,
    "time_range": "1h",
    "timestamp": "2024-01-15T14:32:45.123456+00:00",
    "agent_metrics": {
      "validate_content": {
        "count": 892,
        "avg_duration_ms": 189,
        "min_duration_ms": 45,
        "max_duration_ms": 2341,
        "p50_duration_ms": 156,
        "p95_duration_ms": 567,
        "p99_duration_ms": 1234
      }
    }
  },
  "database_performance": {
    "overall_avg_ms": 18,
    "total_operations": 8329,
    "time_range": "1h",
    "timestamp": "2024-01-15T14:32:45.123456+00:00",
    "db_metrics": {}
  },
  "time_range": "1h",
  "timestamp": "2024-01-15T14:32:45.123456+00:00"
}
```

**Error Responses**:

```json
{
  "detail": "Failed to get metrics: [error details]"
}
```

**HTTP Status Codes**:

- 200: Success
- 400: Invalid query parameters
- 500: Server error

**Example Usage**:

```bash
# Get 24-hour metrics
curl -X GET "http://localhost:8000/api/dashboard/monitoring/metrics?time_range=24h"
```

---

### GET /api/dashboard/monitoring/metrics/historical

**Get historical time-series metrics**

**Request**:

```
GET /api/dashboard/monitoring/metrics/historical?time_range=24h&interval=5m
```

**Query Parameters**:

| Parameter | Type | Required | Default | Values | Description |
|-----------|------|----------|---------|--------|-------------|
| time_range | string | No | 24h | 1h, 6h, 24h, 7d | Data period |
| interval | string | No | 5m | 1m, 5m, 15m, 1h | Data point interval |

**Response** (200 OK):

```json
{
  "time_range": "24h",
  "interval": "5m",
  "data_points": [
    {
      "timestamp": "2024-01-14T14:00:00+00:00",
      "validation_count": 450,
      "avg_response_time": 234,
      "error_rate": 1.2
    },
    {
      "timestamp": "2024-01-14T14:05:00+00:00",
      "validation_count": 465,
      "avg_response_time": 241,
      "error_rate": 1.1
    }
  ]
}
```

**Interval Sizes**:

- `1m`: 1-minute granularity (suitable for recent data only)
- `5m`: 5-minute granularity (good balance for 24-hour data)
- `15m`: 15-minute granularity (suitable for weekly views)
- `1h`: Hourly granularity (suitable for monthly/quarterly views)

---

### GET /api/dashboard/monitoring/export

**Export metrics in JSON or CSV format**

**Request**:

```
GET /api/dashboard/monitoring/export?format=json&time_range=24h
```

**Query Parameters**:

| Parameter | Type | Required | Default | Values | Description |
|-----------|------|----------|---------|--------|-------------|
| format | string | No | json | json, csv | Export format |
| time_range | string | No | 24h | 1h, 6h, 24h, 7d | Data period |

**Response**:

- **JSON**: Application/json content with metrics object
- **CSV**: Text/csv content with comma-separated values

**Headers**:

```
Content-Type: application/json or text/csv
Content-Disposition: attachment; filename=monitoring_metrics_[timerange]_[timestamp].[ext]
```

---

### GET /api/dashboard/monitoring/health

**Health check for monitoring subsystem**

**Request**:

```
GET /api/dashboard/monitoring/health
```

**Response** (200 OK):

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:32:45.123456+00:00",
  "metrics_available": true
}
```

**Use cases**:

- Verify monitoring endpoint availability
- Check if metrics are being collected
- Monitoring system health for alerting

---

### Error Handling

**Common Errors**:

| Error | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request | Invalid query parameter | Check valid values (1h, 6h, 24h, 7d) |
| 401 Unauthorized | Missing or invalid auth | Verify authentication token |
| 403 Forbidden | Insufficient permissions | Verify user role has monitoring access |
| 500 Server Error | Internal error | Check server logs, retry after delay |

**Retry Strategy**:

```python
import requests
import time

MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

for attempt in range(MAX_RETRIES):
    try:
        response = requests.get(
            "http://localhost:8000/api/dashboard/monitoring/metrics",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if attempt < MAX_RETRIES - 1:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(RETRY_DELAY * (2 ** attempt))  # Exponential backoff
        else:
            raise
```

---

## Troubleshooting

### Common Issues and Solutions

#### Dashboard Not Loading

**Symptom**: Blank page or "Failed to load monitoring dashboard" error

**Possible Causes**:

1. **Network connectivity issue**
   - Check browser console (F12) for network errors
   - Verify server is running: `curl http://localhost:8000/api/dashboard/monitoring/health`
   - Check firewall/network permissions

2. **Authentication failure**
   - Verify credentials
   - Check if session has expired, try logging out and back in
   - Check browser cookies are enabled

3. **Server error**
   - Check server logs: `tail -f logs/tbcv.log | grep monitoring`
   - Verify dependencies are installed: `pip list | grep -E 'psutil|chart|fastapi'`
   - Restart the service

**Solutions**:

```bash
# Verify server health
curl -X GET http://localhost:8000/api/dashboard/monitoring/health

# Check server is running
curl -X GET http://localhost:8000/

# Check logs for errors
tail -100 logs/tbcv.log | grep -i error

# Restart service
systemctl restart tbcv
# or
docker restart tbcv-container
```

#### Metrics Not Updating

**Symptom**: Metrics are frozen at same values, Last Update time doesn't change

**Possible Causes**:

1. **Auto-refresh disabled**
   - Check the "Auto-Refresh" checkbox is enabled
   - Click "Refresh All" button to manually update

2. **Connection issue**
   - Check connection indicator (should be green)
   - Check browser console for errors
   - Verify network connectivity

3. **Server-side issue**
   - Database connectivity problem
   - Performance tracker not collecting data
   - Cache manager issue

**Solutions**:

```bash
# Manual refresh options

# Option 1: Click "Refresh All" button in dashboard
# Option 2: Press F5 to reload page
# Option 3: Use API directly
curl -X GET http://localhost:8000/api/dashboard/monitoring/metrics

# Check database connectivity
# Option 4: Check if metrics are being collected
tail -50 logs/tbcv.log | grep -i "metric"
```

#### Performance Issues

**Symptom**: Dashboard slow to load, charts rendering slowly, high CPU usage

**Possible Causes**:

1. **Large time range selected**
   - Too much historical data loaded
   - Browser struggling to render large datasets

2. **Poor network connectivity**
   - Slow API responses
   - Latency to server

3. **Browser resource constraints**
   - Browser running out of memory
   - Too many browser tabs/extensions

**Solutions**:

```bash
# Performance optimization

# 1. Use shorter time ranges
#    Select "1h" instead of "7d" for daily monitoring
#    Use "24h" or "7d" only when necessary

# 2. Disable auto-refresh during off-peak hours
#    Uncheck "Auto-Refresh" when not actively monitoring

# 3. Close other browser tabs/windows
#    Free up system resources

# 4. Clear browser cache
#    Ctrl+Shift+Delete (Windows) or Cmd+Shift+Delete (Mac)

# 5. Use Firefox instead of Chrome if experiencing issues
#    Different browsers have different performance characteristics

# 6. Monitor server performance
tail -f logs/tbcv.log | grep -i performance
```

#### Missing Metrics

**Symptom**: Some metrics show "--" or are empty, agent metrics table is blank

**Possible Causes**:

1. **No recent data**
   - System hasn't processed enough operations
   - Time range selected has no activity

2. **Component not running**
   - Agent services not running
   - Performance tracker not initialized

3. **Database issue**
   - Validation results not being saved
   - Metrics not being recorded

**Solutions**:

```bash
# Check if metrics are being collected
tail -50 logs/tbcv.log | grep -E "agent|validation|performance"

# Check if agents are running
ps aux | grep -i agent

# Verify database has data
# Connect to database and check:
# SELECT COUNT(*) FROM validation_results;
# SELECT COUNT(*) FROM performance_metrics;

# If no data, trigger a test validation
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"content": "test content"}'

# Wait a few seconds, then refresh dashboard
```

#### Export Not Working

**Symptom**: Export button doesn't work, no file downloaded

**Possible Causes**:

1. **Download blocked by browser**
   - Browser has download protection enabled
   - Check download settings

2. **Server error**
   - Server can't generate export file
   - Insufficient permissions

3. **Network issue**
   - Connection lost during download
   - Server timeout

**Solutions**:

```bash
# Test export via API
curl -X GET "http://localhost:8000/api/dashboard/monitoring/export?format=json&time_range=24h" \
  -o metrics.json

# Check if file was created
ls -lh metrics.json

# If using Python
import requests
response = requests.get(
    "http://localhost:8000/api/dashboard/monitoring/export",
    params={"format": "json", "time_range": "24h"}
)
print(f"Status: {response.status_code}")
print(f"Content length: {len(response.content)}")
```

#### High False Alert Rate

**Symptom**: Too many alerts, thresholds triggering unnecessarily

**Solutions**:

1. **Increase alert cooldown**: Reduces repeat alerts for same issue
2. **Adjust thresholds**: Set more realistic values based on actual system behavior
3. **Use percentile-based thresholds**: Use P95/P99 instead of absolute values

Example adjustment:

```
Before (too sensitive):
- CPU Alert: 70% (too many false positives)

After (better):
- CPU Alert: 85% (only alerts for real issues)
- Alert Cooldown: 30 minutes (reduce spam)
```

---

## Best Practices

### Monitoring Frequency

#### Daily Monitoring

**What to check**:

1. **Start of shift**: Review overnight metrics and any alerts
2. **Mid-shift**: Quick health check (5-10 minute data)
3. **End of shift**: Summary of daily performance
4. **Handoff to next team**: Brief summary of status

**Dashboard access pattern**:

```
9:00 AM  - 15 min review (24 hour data, check overnight)
12:00 PM - 5 min check (1 hour data, current status)
5:00 PM  - 10 min review (24 hour data, daily summary)
```

#### Weekly Review

**What to check**:

1. **Performance trends**: Week-over-week comparisons
2. **Capacity utilization**: Are resources being used efficiently?
3. **Error patterns**: Are there consistent failure types or times?
4. **Peak periods**: When does system reach maximum load?

**Process**:

```
1. Export 7-day metrics
2. Create weekly report with summary statistics
3. Compare to previous weeks
4. Document any anomalies or issues
5. Share with team leads
6. Plan capacity or optimization if needed
```

### Alert Configuration Tips

#### Threshold Setting Strategy

**Step 1: Establish baseline**

```python
# Collect 1-2 weeks of data, calculate statistics
import statistics

# Example: CPU usage over 1 week
cpu_samples = [45, 48, 52, 51, 49, 55, 58, ...]

p50 = statistics.median(cpu_samples)  # 50th percentile
p95 = numpy.percentile(cpu_samples, 95)  # 95th percentile
p99 = numpy.percentile(cpu_samples, 99)  # 99th percentile

print(f"P50: {p50}%")
print(f"P95: {p95}%")
print(f"P99: {p99}%")
```

**Step 2: Set thresholds based on percentiles**

```
Conservative (less alerts):    Set at P99 + 5-10%
Moderate (balanced):          Set at P95 + 5-10%
Sensitive (more alerts):      Set at P90 + 5-10%
```

**Step 3: Document and communicate**

```
CPU Alert Threshold: 85% (based on P99 80% + 5%)
Rationale: Alerts when CPU consistently exceeds 95th
percentile performance, indicating degradation
```

#### Alert Cooldown Configuration

**Purpose**: Prevent alert spam for sustained issues

**Recommended settings**:

- **High-priority alerts** (errors, data loss): 5-10 minutes
- **Medium-priority alerts** (performance): 15-30 minutes
- **Low-priority alerts** (resource usage): 30-60 minutes

**Example**:

```
Error Rate Alert:       Cooldown = 5 minutes  (catch early)
Response Time Alert:    Cooldown = 15 minutes (moderate)
Memory Usage Alert:     Cooldown = 30 minutes (gentle reminder)
```

### Performance Optimization

#### Identifying Bottlenecks

**Method: Metric Correlation Analysis**

```
1. High response time + Low CPU/Memory?
   → Database/I/O bottleneck

2. High response time + High CPU?
   → Computational bottleneck

3. High error rate + High Memory?
   → Memory leak or capacity issue

4. Low cache hit rate + High DB queries?
   → Cache configuration opportunity
```

**Process**:

```
1. Export 24-hour metrics
2. Look for sustained high values
3. Correlate with other metrics
4. Identify root cause pattern
5. Document finding
6. Plan optimization
```

#### Cache Optimization

**Low hit rate (< 70%)?**

1. Analyze what's being cached
2. Check cache size limits
3. Review cache eviction policy
4. Consider different cache key strategy
5. Increase cache size if appropriate

**High hit rate (> 90%) with high throughput?**

1. Cache is working well, no action needed
2. Monitor for cache consistency issues
3. Ensure proper cache invalidation

### Integration with External Monitoring

#### Send metrics to Prometheus

```python
from prometheus_client import CollectorRegistry, Gauge, start_http_server
import requests
import json
import time

registry = CollectorRegistry()

# Define metrics
cpu_gauge = Gauge('tbcv_cpu_percent', 'CPU usage percentage', registry=registry)
memory_gauge = Gauge('tbcv_memory_percent', 'Memory usage percentage', registry=registry)
validation_throughput = Gauge('tbcv_validation_throughput', 'Validations per minute', registry=registry)
cache_hit_rate = Gauge('tbcv_cache_hit_rate', 'Cache hit rate percentage', registry=registry)

# Start Prometheus HTTP server
start_http_server(8001, registry=registry)

# Periodic collection
while True:
    try:
        response = requests.get("http://localhost:8000/api/dashboard/monitoring/metrics")
        metrics = response.json()

        # Update gauges
        cpu_gauge.set(metrics['system_resources']['cpu_percent'])
        memory_gauge.set(metrics['system_resources']['memory_percent'])
        validation_throughput.set(metrics['validation_throughput']['per_minute'])
        cache_hit_rate.set(metrics['cache']['hit_rate'])

    except Exception as e:
        print(f"Error collecting metrics: {e}")

    time.sleep(60)  # Update every minute
```

#### Send alerts to Slack

```python
import requests
import json

def send_slack_alert(message, severity="warning"):
    """Send alert to Slack"""

    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

    # Color based on severity
    colors = {
        "info": "#36a64f",
        "warning": "#ff9900",
        "critical": "#ff0000"
    }

    payload = {
        "attachments": [
            {
                "color": colors.get(severity, colors["warning"]),
                "title": f"{severity.upper()}: TBCV Alert",
                "text": message,
                "ts": int(time.time())
            }
        ]
    }

    requests.post(webhook_url, json=payload)

# Usage
send_slack_alert("CPU usage exceeded 80% threshold", severity="warning")
```

### Reporting Best Practices

#### Weekly Report Template

```
TBCV System Performance Report
Week of: January 8-14, 2024

EXECUTIVE SUMMARY
- System uptime: 99.98%
- Average response time: 234 ms
- Cache hit rate: 82.5%
- Error rate: 0.8%

KEY METRICS
- Validations processed: 45,230
- Peak throughput: 125 validations/minute
- P95 response time: 567 ms
- Memory usage: Peak 73%, Average 62%

ALERTS TRIGGERED: 3
1. High memory usage (Jan 10, 14:32)
2. Database query time spike (Jan 12, 09:15)
3. Cache hit rate below threshold (Jan 14, 16:45)

RECOMMENDATIONS
1. Increase memory by 20% to prevent OOM scenarios
2. Review slow queries and add missing indexes
3. Adjust cache configuration for better hit rate

TREND ANALYSIS
- Response times: Stable (no significant trend)
- Throughput: Slight increase (2% week-over-week)
- Resource usage: Increasing, plan capacity upgrade in Q2
```

#### Monthly Capacity Plan

```
Current Capacity Utilization:
- CPU: 65% average, 85% peak
- Memory: 62% average, 73% peak
- Disk: 45% used

Growth Rate:
- 3% monthly increase in throughput
- 2% monthly increase in data stored

Projections (6 months):
- CPU will reach 80% at current growth rate
- Memory will reach 75% at current growth rate
- Disk will reach 52% capacity

Recommendations:
1. Upgrade memory now (lead time 2 weeks)
2. Monitor CPU trends, plan upgrade for Month 4-5
3. Plan disk expansion for Month 6-7
4. Consider horizontal scaling for performance tier
```

---

## Additional Resources

### Related Documentation

- [API Reference](./api_reference.md)
- [Architecture Guide](./architecture.md)
- [Database Schema](./database_schema.md)
- [Configuration Guide](./configuration.md)
- [Troubleshooting Guide](./troubleshooting.md)

### External Tools Integration

- [Prometheus Monitoring](https://prometheus.io/)
- [Grafana Dashboards](https://grafana.com/)
- [ELK Stack](https://www.elastic.co/what-is/elk-stack)
- [DataDog Monitoring](https://www.datadoghq.com/)

### FAQ

**Q: How often should I check the dashboard?**
A: For operational deployments, check at least daily. For critical systems, monitor real-time throughout the day.

**Q: Can I set custom alert thresholds per metric?**
A: Yes, in the Alert Thresholds section. Thresholds are applied globally to all instances of that metric.

**Q: How long is historical data retained?**
A: Data is typically retained for 7 days. Older data can be exported and archived.

**Q: Can I access the dashboard programmatically?**
A: Yes, use the API endpoints documented in [API Reference](#api-reference) section.

**Q: How do I troubleshoot persistent high error rates?**
A: Check the validation logs, review recent changes, correlate with resource usage, and inspect error details in database.

---

## Glossary

| Term | Definition |
|------|-----------|
| **P95** | 95th percentile - 95% of values are below this point |
| **P99** | 99th percentile - 99% of values are below this point |
| **Throughput** | Number of operations completed per unit time |
| **Latency** | Time taken to complete a single operation |
| **Cache Hit** | Cache request that finds data in cache (fast) |
| **Cache Miss** | Cache request that requires database lookup (slow) |
| **Hit Rate** | Percentage of cache requests that result in hits |
| **Alert Threshold** | Value at which an alert is triggered |
| **Alert Cooldown** | Minimum time between repeated alerts for same issue |

---

## Document Information

- **Last Updated**: 2024-01-15
- **Version**: 1.0
- **Author**: TBCV Development Team
- **Status**: Active

### Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01-15 | Initial release with 10 main sections and comprehensive API documentation |

For updates or corrections, please contact the development team or submit an issue in the project repository.
