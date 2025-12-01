"""
Pytest configuration and fixtures for integration tests.

Imports fixtures from svc tests and provides additional integration-specific fixtures.
"""

import pytest
from pathlib import Path

# Import fixtures from svc tests
from tests.svc.conftest import (
    temp_db,
    mcp_server,
    mcp_sync_client,
    mcp_async_client,
    test_markdown_file,
    test_markdown_files,
    test_validation_record,
    sample_validation_data,
    sample_recommendation_data,
    clean_env
)

# Make fixtures available to integration tests
__all__ = [
    "temp_db",
    "mcp_server",
    "mcp_sync_client",
    "mcp_async_client",
    "test_markdown_file",
    "test_markdown_files",
    "test_validation_record",
    "sample_validation_data",
    "sample_recommendation_data",
    "clean_env"
]
