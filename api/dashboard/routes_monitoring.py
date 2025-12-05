# file: tbcv/api/dashboard/routes_monitoring.py
"""
Monitoring routes for performance dashboard.
Provides real-time metrics and historical data for system monitoring.
"""

from __future__ import annotations

import psutil
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
import json
import asyncio

try:
    from core.performance_tracker import performance_tracker
    from core.database import db_manager
    from core.cache import cache_manager
    from core.logging import get_logger
except ImportError:
    from core.performance_tracker import performance_tracker
    from core.database import db_manager
    from core.cache import cache_manager
    from core.logging import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# Global metrics storage for real-time updates
_metrics_cache = {
    "last_update": None,
    "metrics": {}
}


def _get_system_resources() -> Dict[str, Any]:
    """Get current system resource usage."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Get process-specific metrics
        process = psutil.Process()
        process_memory = process.memory_info()

        return {
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory.percent, 2),
            "memory_used_mb": round(memory.used / (1024 * 1024), 2),
            "memory_total_mb": round(memory.total / (1024 * 1024), 2),
            "disk_percent": round(disk.percent, 2),
            "disk_used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
            "disk_total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
            "process_memory_mb": round(process_memory.rss / (1024 * 1024), 2),
            "active_threads": process.num_threads(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get system resources: {e}")
        return {
            "cpu_percent": 0,
            "memory_percent": 0,
            "memory_used_mb": 0,
            "memory_total_mb": 0,
            "disk_percent": 0,
            "disk_used_gb": 0,
            "disk_total_gb": 0,
            "process_memory_mb": 0,
            "active_threads": 0,
            "error": str(e)
        }


def _get_cache_metrics() -> Dict[str, Any]:
    """Get cache performance metrics."""
    try:
        stats = cache_manager.get_stats()

        total_requests = stats.get("hits", 0) + stats.get("misses", 0)
        hit_rate = (stats.get("hits", 0) / total_requests * 100) if total_requests > 0 else 0

        return {
            "hit_rate": round(hit_rate, 2),
            "total_hits": stats.get("hits", 0),
            "total_misses": stats.get("misses", 0),
            "cache_size": stats.get("size", 0),
            "evictions": stats.get("evictions", 0),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get cache metrics: {e}")
        return {
            "hit_rate": 0,
            "total_hits": 0,
            "total_misses": 0,
            "cache_size": 0,
            "evictions": 0,
            "error": str(e)
        }


def _get_validation_throughput(time_range: str = "1h") -> Dict[str, Any]:
    """Calculate validation throughput for time range."""
    try:
        # Parse time range
        hours_map = {"1h": 1, "6h": 6, "24h": 24, "7d": 168}
        hours = hours_map.get(time_range, 1)

        # Get validations from database
        validations = db_manager.list_validation_results(limit=10000)

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        recent_validations = [
            v for v in validations
            if hasattr(v, 'created_at') and v.created_at and v.created_at > cutoff
        ]

        total_count = len(recent_validations)
        per_minute = round(total_count / (hours * 60), 2) if hours > 0 else 0
        per_hour = round(total_count / hours, 2) if hours > 0 else 0

        # Calculate success rate
        successful = len([v for v in recent_validations if hasattr(v, 'status') and v.status.value == 'pass'])
        success_rate = (successful / total_count * 100) if total_count > 0 else 0

        return {
            "total_count": total_count,
            "per_minute": per_minute,
            "per_hour": per_hour,
            "success_rate": round(success_rate, 2),
            "time_range": time_range,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get validation throughput: {e}")
        return {
            "total_count": 0,
            "per_minute": 0,
            "per_hour": 0,
            "success_rate": 0,
            "error": str(e)
        }


def _get_agent_performance(time_range: str = "24h") -> Dict[str, Any]:
    """Get agent performance metrics."""
    try:
        report = performance_tracker.get_report(time_range=time_range)

        agent_metrics = {}
        total_avg = 0
        total_ops = 0

        for op_name, metrics in report.get("operations", {}).items():
            # Filter agent operations
            if any(keyword in op_name.lower() for keyword in ['agent', 'validate', 'enhance', 'analyze']):
                agent_metrics[op_name] = {
                    "count": metrics["count"],
                    "avg_duration_ms": round(metrics["avg_duration_ms"], 2),
                    "min_duration_ms": round(metrics["min_duration_ms"], 2),
                    "max_duration_ms": round(metrics["max_duration_ms"], 2),
                    "p50_duration_ms": round(metrics["p50_duration_ms"], 2),
                    "p95_duration_ms": round(metrics["p95_duration_ms"], 2),
                    "p99_duration_ms": round(metrics["p99_duration_ms"], 2)
                }
                total_avg += metrics["avg_duration_ms"] * metrics["count"]
                total_ops += metrics["count"]

        overall_avg = round(total_avg / total_ops, 2) if total_ops > 0 else 0

        return {
            "overall_avg_ms": overall_avg,
            "total_operations": total_ops,
            "agent_metrics": agent_metrics,
            "success_rate": round(report.get("success_rate", 0) * 100, 2),
            "time_range": time_range,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get agent performance: {e}")
        return {
            "overall_avg_ms": 0,
            "total_operations": 0,
            "agent_metrics": {},
            "success_rate": 0,
            "error": str(e)
        }


def _get_database_performance(time_range: str = "24h") -> Dict[str, Any]:
    """Get database operation performance metrics."""
    try:
        report = performance_tracker.get_report(time_range=time_range)

        db_metrics = {}
        total_avg = 0
        total_ops = 0

        for op_name, metrics in report.get("operations", {}).items():
            # Filter database operations
            if any(keyword in op_name.lower() for keyword in ['db', 'database', 'query', 'insert', 'update', 'select']):
                db_metrics[op_name] = {
                    "count": metrics["count"],
                    "avg_duration_ms": round(metrics["avg_duration_ms"], 2),
                    "min_duration_ms": round(metrics["min_duration_ms"], 2),
                    "max_duration_ms": round(metrics["max_duration_ms"], 2),
                    "p95_duration_ms": round(metrics["p95_duration_ms"], 2),
                    "p99_duration_ms": round(metrics["p99_duration_ms"], 2)
                }
                total_avg += metrics["avg_duration_ms"] * metrics["count"]
                total_ops += metrics["count"]

        overall_avg = round(total_avg / total_ops, 2) if total_ops > 0 else 0

        return {
            "overall_avg_ms": overall_avg,
            "total_operations": total_ops,
            "db_metrics": db_metrics,
            "time_range": time_range,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get database performance: {e}")
        return {
            "overall_avg_ms": 0,
            "total_operations": 0,
            "db_metrics": {},
            "error": str(e)
        }


@router.get("/metrics")
async def get_metrics(time_range: str = Query("1h", pattern="^(1h|6h|24h|7d)$")):
    """
    Get comprehensive monitoring metrics.

    Args:
        time_range: Time range for metrics (1h, 6h, 24h, 7d)

    Returns:
        Comprehensive metrics including system resources, throughput, and performance
    """
    try:
        metrics = {
            "system_resources": _get_system_resources(),
            "cache": _get_cache_metrics(),
            "validation_throughput": _get_validation_throughput(time_range),
            "agent_performance": _get_agent_performance(time_range),
            "database_performance": _get_database_performance(time_range),
            "time_range": time_range,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Update cache
        _metrics_cache["last_update"] = time.time()
        _metrics_cache["metrics"] = metrics

        return JSONResponse(content=metrics)

    except Exception as e:
        logger.exception("Failed to get monitoring metrics")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/metrics/historical")
async def get_historical_metrics(
    time_range: str = Query("24h", pattern="^(1h|6h|24h|7d)$"),
    interval: str = Query("5m", pattern="^(1m|5m|15m|1h)$")
):
    """
    Get historical metrics for charting.

    Args:
        time_range: Time range for data (1h, 6h, 24h, 7d)
        interval: Data point interval (1m, 5m, 15m, 1h)

    Returns:
        Time-series data for visualization
    """
    try:
        # Parse intervals
        interval_minutes = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "1h": 60
        }[interval]

        hours_map = {"1h": 1, "6h": 6, "24h": 24, "7d": 168}
        hours = hours_map[time_range]

        # Generate time series (simplified for now - would need actual historical data storage)
        data_points = []
        now = datetime.now(timezone.utc)

        for i in range(0, int(hours * 60 / interval_minutes)):
            timestamp = now - timedelta(minutes=i * interval_minutes)
            data_points.append({
                "timestamp": timestamp.isoformat(),
                "validation_count": 0,  # Would fetch from actual data
                "avg_response_time": 0,
                "error_rate": 0
            })

        return JSONResponse(content={
            "time_range": time_range,
            "interval": interval,
            "data_points": list(reversed(data_points))
        })

    except Exception as e:
        logger.exception("Failed to get historical metrics")
        raise HTTPException(status_code=500, detail=f"Failed to get historical metrics: {str(e)}")


@router.get("/export")
async def export_metrics(
    format: str = Query("json", pattern="^(json|csv)$"),
    time_range: str = Query("24h", pattern="^(1h|6h|24h|7d)$")
):
    """
    Export metrics in JSON or CSV format.

    Args:
        format: Export format (json or csv)
        time_range: Time range for data

    Returns:
        StreamingResponse with exported data
    """
    try:
        metrics = {
            "system_resources": _get_system_resources(),
            "cache": _get_cache_metrics(),
            "validation_throughput": _get_validation_throughput(time_range),
            "agent_performance": _get_agent_performance(time_range),
            "database_performance": _get_database_performance(time_range)
        }

        if format == "json":
            content = json.dumps(metrics, indent=2)
            media_type = "application/json"
            filename = f"monitoring_metrics_{time_range}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:  # csv
            # Convert to CSV format
            lines = ["metric,value,timestamp"]

            # System resources
            sys_res = metrics.get('system_resources', {})
            if 'cpu_percent' in sys_res:
                lines.append(f"cpu_percent,{sys_res['cpu_percent']},{sys_res.get('timestamp', '')}")
            if 'memory_percent' in sys_res:
                lines.append(f"memory_percent,{sys_res['memory_percent']},{sys_res.get('timestamp', '')}")

            # Cache
            cache = metrics.get('cache', {})
            if 'hit_rate' in cache:
                lines.append(f"cache_hit_rate,{cache['hit_rate']},{cache.get('timestamp', '')}")

            # Validation throughput
            throughput = metrics.get('validation_throughput', {})
            if 'per_minute' in throughput:
                lines.append(f"validation_per_minute,{throughput['per_minute']},{throughput.get('timestamp', '')}")

            # Agent performance
            agent = metrics.get('agent_performance', {})
            if 'overall_avg_ms' in agent:
                lines.append(f"agent_avg_ms,{agent['overall_avg_ms']},{agent.get('timestamp', '')}")

            # Database performance
            db = metrics.get('database_performance', {})
            if 'overall_avg_ms' in db:
                lines.append(f"db_avg_ms,{db['overall_avg_ms']},{db.get('timestamp', '')}")

            content = "\n".join(lines)
            media_type = "text/csv"
            filename = f"monitoring_metrics_{time_range}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            iter([content]),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.exception("Failed to export metrics")
        raise HTTPException(status_code=500, detail=f"Failed to export metrics: {str(e)}")


@router.get("/health")
async def monitoring_health():
    """Health check endpoint for monitoring dashboard."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics_available": _metrics_cache["last_update"] is not None
    }
