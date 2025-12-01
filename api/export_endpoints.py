# file: api/export_endpoints.py
"""
Export endpoints for TBCV API.

Provides endpoints for exporting validation results, recommendations,
audit logs, and reports in various formats (JSON, CSV, Markdown).
"""

import csv
import io
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response, StreamingResponse

from core.database import db_manager

# Create router for export endpoints
# Note: prefix includes /api for test compatibility
router = APIRouter(prefix="/api/export", tags=["export"])


def _format_datetime(dt: Optional[datetime]) -> str:
    """Format datetime for export."""
    if dt is None:
        return ""
    return dt.isoformat()


def _safe_to_dict(obj: Any) -> Dict[str, Any]:
    """Safely convert object to dict."""
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    return {}


def generate_diff_report(validation_id: str) -> Dict[str, Any]:
    """
    Generate a diff report for a validation.

    Args:
        validation_id: The validation ID to generate report for

    Returns:
        Dict containing validation, recommendations, and diffs
    """
    validation = db_manager.get_validation_result(validation_id)
    if not validation:
        return {}

    recommendations = db_manager.list_recommendations(validation_id=validation_id)

    diffs = []
    for rec in recommendations:
        if hasattr(rec, 'diff') and rec.diff:
            diffs.append({
                "recommendation_id": rec.id if hasattr(rec, 'id') else str(rec),
                "title": getattr(rec, 'title', ''),
                "diff": rec.diff,
                "original_content": getattr(rec, 'original_content', ''),
                "proposed_content": getattr(rec, 'proposed_content', '')
            })

    return {
        "validation": _safe_to_dict(validation),
        "recommendations": [_safe_to_dict(r) for r in recommendations],
        "diffs": diffs
    }


# --- Validation Exports ---

@router.get("/validations.json")
async def export_validations_json(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(1000, description="Maximum records to export")
):
    """Export validations as JSON."""
    try:
        validations = db_manager.list_validation_results(
            status=status,
            severity=severity,
            limit=limit
        )

        data = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "filters": {
                "status": status,
                "severity": severity,
                "limit": limit
            },
            "total_records": len(validations),
            "validations": [_safe_to_dict(v) for v in validations]
        }

        import json
        content = json.dumps(data, indent=2, default=str)

        return Response(
            content=content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=validations_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/validations.csv")
async def export_validations_csv(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(1000, description="Maximum records to export")
):
    """Export validations as CSV."""
    try:
        validations = db_manager.list_validation_results(
            status=status,
            severity=severity,
            limit=limit
        )

        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow([
            "ID", "File Path", "Family", "Status", "Severity",
            "Owner Score", "Risk Level", "Created At", "Updated At", "Summary"
        ])

        # Data rows
        for v in validations:
            status_val = v.status.value if hasattr(v.status, 'value') else str(v.status)
            writer.writerow([
                getattr(v, 'id', ''),
                getattr(v, 'file_path', ''),
                getattr(v, 'family', ''),
                status_val,
                getattr(v, 'severity', ''),
                getattr(v, 'owner_score', ''),
                getattr(v, 'risk_level', ''),
                _format_datetime(getattr(v, 'created_at', None)),
                _format_datetime(getattr(v, 'updated_at', None)),
                getattr(v, 'summary', '')
            ])

        csv_content = output.getvalue()

        return Response(
            content=csv_content,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=validations_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# --- Recommendations Export ---

@router.get("/recommendations.json")
async def export_recommendations_json(
    status: Optional[str] = Query(None, description="Filter by status"),
    type: Optional[str] = Query(None, alias="type", description="Filter by type"),
    limit: int = Query(1000, description="Maximum records to export")
):
    """Export recommendations as JSON."""
    try:
        recommendations = db_manager.list_recommendations(
            status=status,
            limit=limit
        )

        data = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "filters": {
                "status": status,
                "type": type,
                "limit": limit
            },
            "total_records": len(recommendations),
            "recommendations": [_safe_to_dict(r) for r in recommendations]
        }

        import json
        content = json.dumps(data, indent=2, default=str)

        return Response(
            content=content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=recommendations_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# --- Audit Logs Export ---

@router.get("/audit-logs.json")
async def export_audit_logs_json(
    action: Optional[str] = Query(None, description="Filter by action"),
    limit: int = Query(1000, description="Maximum records to export")
):
    """Export audit logs as JSON."""
    try:
        audit_logs = db_manager.list_audit_logs(
            action=action,
            limit=limit
        )

        data = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "filters": {
                "action": action,
                "limit": limit
            },
            "total_records": len(audit_logs),
            "audit_logs": [_safe_to_dict(log) for log in audit_logs]
        }

        import json
        content = json.dumps(data, indent=2, default=str)

        return Response(
            content=content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# --- Workflows Export ---

@router.get("/workflows.json")
async def export_workflows_json(
    state: Optional[str] = Query(None, description="Filter by state"),
    limit: int = Query(1000, description="Maximum records to export")
):
    """Export workflows as JSON."""
    try:
        workflows = db_manager.list_workflows(
            state=state,
            limit=limit
        )

        data = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "filters": {
                "state": state,
                "limit": limit
            },
            "total_records": len(workflows),
            "workflows": [_safe_to_dict(w) for w in workflows]
        }

        import json
        content = json.dumps(data, indent=2, default=str)

        return Response(
            content=content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=workflows_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# --- Markdown Report ---

@router.get("/report.md")
async def export_markdown_report(
    include_validations: bool = Query(True, description="Include validations section"),
    include_recommendations: bool = Query(True, description="Include recommendations section"),
    include_audit_logs: bool = Query(False, description="Include audit logs section")
):
    """Generate and export a comprehensive Markdown report."""
    try:
        lines = []
        lines.append("# TBCV System Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now(timezone.utc).isoformat()}")
        lines.append("")

        # Validations section
        if include_validations:
            validations = db_manager.list_validation_results(limit=1000)
            lines.append("## Validation Summary")
            lines.append("")
            lines.append(f"**Total Validations:** {len(validations)}")
            lines.append("")

            if validations:
                lines.append("| ID | File | Status | Severity |")
                lines.append("|---|---|---|---|")
                for v in validations[:50]:  # Limit table rows
                    status_val = v.status.value if hasattr(v.status, 'value') else str(v.status)
                    lines.append(f"| {getattr(v, 'id', '')} | {getattr(v, 'file_path', '')} | {status_val} | {getattr(v, 'severity', '')} |")
                lines.append("")

        # Recommendations section
        if include_recommendations:
            recommendations = db_manager.list_recommendations(limit=1000)
            lines.append("## Recommendations Summary")
            lines.append("")
            lines.append(f"**Total Recommendations:** {len(recommendations)}")
            lines.append("")

            if recommendations:
                lines.append("| ID | Title | Type | Status |")
                lines.append("|---|---|---|---|")
                for r in recommendations[:50]:
                    status_val = r.status.value if hasattr(r.status, 'value') else str(r.status)
                    lines.append(f"| {getattr(r, 'id', '')} | {getattr(r, 'title', '')} | {getattr(r, 'type', '')} | {status_val} |")
                lines.append("")

        # Audit logs section
        if include_audit_logs:
            audit_logs = db_manager.list_audit_logs(limit=100)
            lines.append("## Recent Audit Activity")
            lines.append("")
            lines.append(f"**Recent Entries:** {len(audit_logs)}")
            lines.append("")

            if audit_logs:
                lines.append("| Action | Actor | Time |")
                lines.append("|---|---|---|")
                for log in audit_logs[:20]:
                    lines.append(f"| {getattr(log, 'action', '')} | {getattr(log, 'actor', '')} | {_format_datetime(getattr(log, 'created_at', None))} |")
                lines.append("")

        content = "\n".join(lines)

        return Response(
            content=content,
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=tbcv_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


# --- Validation Diff Export ---

@router.get("/validation/{validation_id}/diff.json")
async def export_validation_diff_json(validation_id: str):
    """Export validation diff report as JSON."""
    try:
        result = generate_diff_report(validation_id)

        if not result:
            raise HTTPException(status_code=404, detail=f"Validation {validation_id} not found")

        import json
        content = json.dumps(result, indent=2, default=str)

        return Response(
            content=content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=validation_{validation_id}_diff.json"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# --- Info endpoint (backwards compatible) ---

@router.get("/")
async def export_info():
    """Information about export functionality."""
    return {
        "status": "implemented",
        "message": "Export endpoints are available",
        "available_exports": [
            "/export/validations.json - Export validations as JSON",
            "/export/validations.csv - Export validations as CSV",
            "/export/recommendations.json - Export recommendations as JSON",
            "/export/audit-logs.json - Export audit logs as JSON",
            "/export/workflows.json - Export workflows as JSON",
            "/export/report.md - Generate comprehensive Markdown report",
            "/export/validation/{id}/diff.json - Export validation diff report"
        ]
    }
