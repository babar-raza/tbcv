"""Export utilities for JSON exports."""

import json
from typing import Dict, Any
from datetime import datetime, timezone

EXPORT_SCHEMA_VERSION = "1.0"


def export_to_json(data: Dict[str, Any], schema_version: str = EXPORT_SCHEMA_VERSION) -> str:
    """
    Export data to JSON format.

    Args:
        data: Data to export
        schema_version: Schema version

    Returns:
        JSON string
    """
    export_data = {
        "schema_version": schema_version,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "data": data
    }

    return json.dumps(export_data, indent=2, default=str)


def create_export_metadata(filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create export metadata.

    Args:
        filters: Filters applied to export

    Returns:
        Metadata dictionary
    """
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": EXPORT_SCHEMA_VERSION,
        "filters": filters or {}
    }
