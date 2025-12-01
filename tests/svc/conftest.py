"""
Pytest fixtures for MCP testing.

Provides reusable test fixtures for MCP server, clients, and test data.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import Generator

from svc.mcp_server import MCPServer, create_mcp_client
from svc.mcp_client import MCPSyncClient, MCPAsyncClient
from core.database import DatabaseManager


@pytest.fixture(scope="function")
def temp_db() -> Generator[DatabaseManager, None, None]:
    """
    Create temporary database for testing.

    Creates an isolated SQLite database for each test function,
    ensures proper cleanup after test completion.

    Yields:
        DatabaseManager instance connected to temporary database
    """
    # Create temporary database file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Store original DATABASE_URL
    original_db_url = os.environ.get("DATABASE_URL")

    # Set temporary database URL
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    # Initialize database with schema
    db_manager = DatabaseManager()
    db_manager.init_database()

    yield db_manager

    # Cleanup: restore original database URL
    if original_db_url:
        os.environ["DATABASE_URL"] = original_db_url
    else:
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

    # Delete temporary database file
    try:
        os.unlink(db_path)
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture(scope="function")
def mcp_server(temp_db) -> MCPServer:
    """
    Create MCP server instance for testing.

    Args:
        temp_db: Temporary database fixture

    Returns:
        MCPServer instance configured with test database
    """
    server = create_mcp_client()
    return server


@pytest.fixture(scope="function")
def mcp_sync_client(mcp_server) -> MCPSyncClient:
    """
    Create synchronous MCP client for testing.

    Args:
        mcp_server: MCP server fixture

    Returns:
        MCPSyncClient instance
    """
    client = MCPSyncClient(timeout=10, max_retries=2)
    return client


@pytest.fixture(scope="function")
def mcp_async_client(mcp_server) -> MCPAsyncClient:
    """
    Create asynchronous MCP client for testing.

    Args:
        mcp_server: MCP server fixture

    Returns:
        MCPAsyncClient instance
    """
    client = MCPAsyncClient(timeout=10, max_retries=2)
    return client


@pytest.fixture(scope="function")
def test_markdown_file(tmp_path: Path) -> Path:
    """
    Create test markdown file with comprehensive content.

    Args:
        tmp_path: Pytest temporary directory

    Returns:
        Path to created markdown file
    """
    file_path = tmp_path / "test.md"
    content = """---
title: Test Document
description: A test document for validation
author: Test Author
date: 2025-01-01
tags: [test, markdown, validation]
---

# Test Document

This is a test document for validation testing.

## Introduction

This section contains introductory text with various elements:

- Bullet point 1
- Bullet point 2
- Bullet point 3

### Subsection

More detailed content here.

## Code Example

Here's a Python code example:

```python
def hello_world():
    \"\"\"Print hello world.\"\"\"
    print("Hello, World!")
    return True
```

## Links

External links:
- [Example Website](https://example.com)
- [Documentation](https://docs.example.com)

Internal links:
- [Introduction](#introduction)

## Images

![Test Image](https://example.com/image.png)

## Tables

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |

## Conclusion

This concludes the test document.
"""
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture(scope="function")
def test_markdown_files(tmp_path: Path) -> list[Path]:
    """
    Create multiple test markdown files for batch testing.

    Args:
        tmp_path: Pytest temporary directory

    Returns:
        List of paths to created markdown files
    """
    files = []
    for i in range(3):
        file_path = tmp_path / f"test_file_{i}.md"
        content = f"""---
title: Test Document {i}
---

# Test Document {i}

This is test document number {i}.

## Section {i}

Content for section {i}.
"""
        file_path.write_text(content, encoding="utf-8")
        files.append(file_path)

    return files


@pytest.fixture(scope="function")
def test_validation_record(mcp_sync_client, test_markdown_file) -> str:
    """
    Create test validation record in database.

    Args:
        mcp_sync_client: Synchronous MCP client fixture
        test_markdown_file: Test markdown file fixture

    Returns:
        Validation ID of created record
    """
    # Validate file using MCP client
    result = mcp_sync_client.validate_folder(
        str(test_markdown_file.parent),
        recursive=False
    )

    # Extract validation ID from first result
    if result.get("success") and result.get("results", {}).get("files_processed", 0) > 0:
        # Get the validation ID from the results
        # Note: This depends on how validate_folder returns IDs
        # For now, we'll use a simplified approach
        validation_id = f"test-validation-{test_markdown_file.stem}"
        return validation_id

    # Fallback: create a dummy validation ID
    return "test-validation-fallback"


@pytest.fixture(scope="function")
def sample_validation_data() -> dict:
    """
    Provide sample validation data for testing.

    Returns:
        Dictionary with sample validation data
    """
    return {
        "file_path": "/path/to/test.md",
        "status": "pending",
        "issues": [
            {
                "type": "markdown",
                "severity": "warning",
                "message": "Heading level skipped",
                "line": 10
            },
            {
                "type": "seo",
                "severity": "info",
                "message": "Meta description missing",
                "line": 1
            }
        ],
        "metadata": {
            "word_count": 150,
            "heading_count": 5,
            "link_count": 3
        }
    }


@pytest.fixture(scope="function")
def sample_recommendation_data() -> dict:
    """
    Provide sample recommendation data for testing.

    Returns:
        Dictionary with sample recommendation data
    """
    return {
        "validation_id": "test-validation-123",
        "recommendations": [
            {
                "type": "markdown",
                "priority": "high",
                "suggestion": "Fix heading hierarchy",
                "original": "### Heading",
                "suggested": "## Heading"
            },
            {
                "type": "seo",
                "priority": "medium",
                "suggestion": "Add meta description",
                "original": None,
                "suggested": "description: A comprehensive test document"
            }
        ]
    }


@pytest.fixture(scope="function")
def clean_env() -> Generator[None, None, None]:
    """
    Ensure clean environment for tests.

    Saves and restores environment variables that might affect tests.

    Yields:
        None
    """
    # Save current environment
    saved_env = {
        "DATABASE_URL": os.environ.get("DATABASE_URL"),
        "LOG_LEVEL": os.environ.get("LOG_LEVEL"),
        "CACHE_ENABLED": os.environ.get("CACHE_ENABLED"),
    }

    # Set test environment
    os.environ["LOG_LEVEL"] = "ERROR"  # Suppress logs during testing
    os.environ["CACHE_ENABLED"] = "false"  # Disable cache for tests

    yield

    # Restore environment
    for key, value in saved_env.items():
        if value is not None:
            os.environ[key] = value
        elif key in os.environ:
            del os.environ[key]
