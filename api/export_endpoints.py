# file: tbcv/api/export_endpoints.py
"""
Export functionality for reports and audit history (D05, I08, I26).
Provides JSON, Markdown, and CSV export capabilities.
"""

from __future__ import annotations

import io
import csv
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from core.database import db_manager
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/export", tags=["export"])

@router.get("/validations.json")
async def export_validations_json(
    status: Optional[str] = Query(None, description="Filter by validation status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(1000, description="Maximum number of records")
):
    """Export validation results as JSON."""
    try:
        validations = db_manager.list_validation_results(
            status=status,
            severity=severity, 
            limit=limit
        )
        
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "filters": {
                "status": status,
                "severity": severity,
                "limit": limit
            },
            "total_records": len(validations),
            "validations": [v.to_dict() for v in validations]
        }
        
        json_str = json.dumps(export_data, indent=2, default=str)
        
        def generate():
            yield json_str
        
        return StreamingResponse(
            generate(),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=validations_export.json"}
        )
        
    except Exception as e:
        logger.error(f"Failed to export validations: {e}")
        raise HTTPException(status_code=500, detail="Export failed")

@router.get("/validations.csv")
async def export_validations_csv(
    status: Optional[str] = Query(None, description="Filter by validation status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(1000, description="Maximum number of records")
):
    """Export validation results as CSV."""
    try:
        validations = db_manager.list_validation_results(
            status=status,
            severity=severity,
            limit=limit
        )
        
        def generate():
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "ID", "File Path", "Family", "Status", "Severity", "Owner Score",
                "Risk Level", "Created At", "Updated At", "Summary"
            ])
            
            for validation in validations:
                writer.writerow([
                    validation.id,
                    validation.file_path,
                    validation.family,
                    validation.status.value if validation.status else "",
                    validation.severity,
                    validation.owner_score,
                    validation.risk_level,
                    validation.created_at.isoformat() if validation.created_at else "",
                    validation.updated_at.isoformat() if validation.updated_at else "",
                    validation.summary or ""
                ])
            
            content = output.getvalue()
            output.close()
            yield content
        
        return StreamingResponse(
            generate(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=validations_export.csv"}
        )
        
    except Exception as e:
        logger.error(f"Failed to export validations CSV: {e}")
        raise HTTPException(status_code=500, detail="Export failed")

@router.get("/recommendations.json")
async def export_recommendations_json(
    status: Optional[str] = Query(None, description="Filter by recommendation status"),
    type: Optional[str] = Query(None, description="Filter by recommendation type"),
    limit: int = Query(1000, description="Maximum number of records")
):
    """Export recommendations as JSON."""
    try:
        recommendations = db_manager.list_recommendations(
            status=status,
            type=type,
            limit=limit
        )
        
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "filters": {
                "status": status,
                "type": type,
                "limit": limit
            },
            "total_records": len(recommendations),
            "recommendations": [r.to_dict() for r in recommendations]
        }
        
        json_str = json.dumps(export_data, indent=2, default=str)
        
        def generate():
            yield json_str
        
        return StreamingResponse(
            generate(),
            media_type="application/json", 
            headers={"Content-Disposition": "attachment; filename=recommendations_export.json"}
        )
        
    except Exception as e:
        logger.error(f"Failed to export recommendations: {e}")
        raise HTTPException(status_code=500, detail="Export failed")

@router.get("/audit-logs.json") 
async def export_audit_logs_json(
    action: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(1000, description="Maximum number of records")
):
    """Export audit logs as JSON."""
    try:
        logs = db_manager.list_audit_logs(
            action=action,
            limit=limit
        )
        
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "filters": {
                "action": action,
                "limit": limit
            },
            "total_records": len(logs),
            "audit_logs": [log.to_dict() for log in logs]
        }
        
        json_str = json.dumps(export_data, indent=2, default=str)
        
        def generate():
            yield json_str
        
        return StreamingResponse(
            generate(),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=audit_logs_export.json"}
        )
        
    except Exception as e:
        logger.error(f"Failed to export audit logs: {e}")
        raise HTTPException(status_code=500, detail="Export failed")

@router.get("/report.md")
async def export_comprehensive_report_markdown(
    include_validations: bool = Query(True, description="Include validation results"),
    include_recommendations: bool = Query(True, description="Include recommendations"),
    include_audit_logs: bool = Query(False, description="Include audit logs"),
    limit: int = Query(100, description="Maximum records per section")
):
    """Export comprehensive report as Markdown."""
    try:
        def generate():
            # Header
            yield f"# TBCV System Report\n\n"
            yield f"**Generated:** {datetime.utcnow().isoformat()}\n\n"
            
            # Summary statistics
            if include_validations:
                validations = db_manager.list_validation_results(limit=limit)
                yield f"## Validation Summary\n\n"
                yield f"- **Total Validations:** {len(validations)}\n"
                
                if validations:
                    statuses = {}
                    severities = {}
                    for v in validations:
                        status = v.status.value if v.status else "unknown"
                        statuses[status] = statuses.get(status, 0) + 1
                        severities[v.severity] = severities.get(v.severity, 0) + 1
                    
                    yield f"\n### By Status\n"
                    for status, count in statuses.items():
                        yield f"- **{status.title()}:** {count}\n"
                    
                    yield f"\n### By Severity\n"
                    for severity, count in severities.items():
                        yield f"- **{severity}:** {count}\n"
                
                yield f"\n### Recent Validations\n\n"
                for validation in validations[:10]:  # Top 10
                    yield f"#### {validation.file_path}\n"
                    yield f"- **Status:** {validation.status.value if validation.status else 'unknown'}\n"
                    yield f"- **Severity:** {validation.severity}\n"
                    yield f"- **Created:** {validation.created_at}\n"
                    if validation.summary:
                        yield f"- **Summary:** {validation.summary}\n"
                    yield f"\n"
            
            if include_recommendations:
                recommendations = db_manager.list_recommendations(limit=limit)
                yield f"\n## Recommendations Summary\n\n"
                yield f"- **Total Recommendations:** {len(recommendations)}\n"
                
                if recommendations:
                    statuses = {}
                    for r in recommendations:
                        status = r.status.value if r.status else "unknown"
                        statuses[status] = statuses.get(status, 0) + 1
                    
                    yield f"\n### By Status\n"
                    for status, count in statuses.items():
                        yield f"- **{status.title()}:** {count}\n"
                
                yield f"\n### Recent Recommendations\n\n"
                for rec in recommendations[:10]:  # Top 10
                    yield f"#### {rec.title}\n"
                    yield f"- **Type:** {rec.type}\n"
                    yield f"- **Status:** {rec.status.value if rec.status else 'unknown'}\n"
                    yield f"- **Priority:** {rec.priority}\n"
                    yield f"- **Confidence:** {rec.confidence}\n"
                    if rec.description:
                        yield f"- **Description:** {rec.description}\n"
                    yield f"\n"
            
            if include_audit_logs:
                logs = db_manager.list_audit_logs(limit=50)  # Fewer audit logs
                yield f"\n## Recent Audit Activity\n\n"
                
                for log in logs:
                    yield f"### {log.action} by {log.actor or 'system'}\n"
                    yield f"- **Time:** {log.created_at}\n"
                    yield f"- **Actor Type:** {log.actor_type}\n"
                    if log.notes:
                        yield f"- **Notes:** {log.notes}\n"
                    yield f"\n"
            
            yield f"\n---\n*Report generated by TBCV System*\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=tbcv_report.md"}
        )
        
    except Exception as e:
        logger.error(f"Failed to export markdown report: {e}")
        raise HTTPException(status_code=500, detail="Export failed")

@router.get("/workflows.json")
async def export_workflows_json(
    state: Optional[str] = Query(None, description="Filter by workflow state"),
    limit: int = Query(1000, description="Maximum number of records")
):
    """Export workflows as JSON."""
    try:
        workflows = db_manager.list_workflows(state=state, limit=limit)
        
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "filters": {
                "state": state,
                "limit": limit
            },
            "total_records": len(workflows),
            "workflows": [w.to_dict() for w in workflows]
        }
        
        json_str = json.dumps(export_data, indent=2, default=str)
        
        def generate():
            yield json_str
        
        return StreamingResponse(
            generate(),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=workflows_export.json"}
        )
        
    except Exception as e:
        logger.error(f"Failed to export workflows: {e}")
        raise HTTPException(status_code=500, detail="Export failed")

# Helper function to generate diff reports
def generate_diff_report(validation_id: str) -> Dict[str, Any]:
    """Generate a detailed diff report for a specific validation."""
    validation = db_manager.get_validation_result(validation_id)
    if not validation:
        return {}
    
    recommendations = db_manager.list_recommendations(validation_id=validation_id)
    
    return {
        "validation": validation.to_dict(),
        "recommendations": [r.to_dict() for r in recommendations],
        "diffs": [
            {
                "recommendation_id": r.id,
                "diff": r.diff,
                "original": r.original_content,
                "proposed": r.proposed_content
            }
            for r in recommendations if r.diff
        ]
    }

@router.get("/validation/{validation_id}/diff.json")
async def export_validation_diff_json(validation_id: str):
    """Export detailed diff report for a specific validation."""
    try:
        diff_report = generate_diff_report(validation_id)
        if not diff_report:
            raise HTTPException(status_code=404, detail="Validation not found")
        
        json_str = json.dumps(diff_report, indent=2, default=str)
        
        def generate():
            yield json_str
        
        return StreamingResponse(
            generate(),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=validation_{validation_id}_diff.json"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export validation diff: {e}")
        raise HTTPException(status_code=500, detail="Export failed")
