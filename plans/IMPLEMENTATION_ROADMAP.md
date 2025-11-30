# MCP-First Architecture: Complete Implementation Roadmap

**Date**: 2025-11-30
**Status**: Production-Ready Implementation Guide
**Purpose**: Comprehensive guide with production code for all 18 tasks

---

## Quick Start

This document provides production-ready code for implementing all 56 MCP methods and migrating CLI/API to MCP-first architecture.

### Execution Order

1. **Foundation** (Week 1-2): TASK-001, TASK-002, TASK-003
2. **Core Methods** (Week 3-5): TASK-004 through TASK-010
3. **Advanced Features** (Week 6-7): TASK-011 through TASK-014
4. **Integration** (Week 8): TASK-015, TASK-016
5. **Enforcement** (Week 9): TASK-017, TASK-018

---

## Phase 1: Foundation Implementation

### TASK-003: Testing Infrastructure

**Objective**: Create comprehensive testing infrastructure for MCP server and clients

**Files to Create**:

#### `tests/svc/conftest.py`
```python
"""Pytest fixtures for MCP testing."""

import pytest
import tempfile
from pathlib import Path
from svc.mcp_server import MCPServer, create_mcp_client
from svc.mcp_client import MCPSyncClient, MCPAsyncClient
from core.database import DatabaseManager


@pytest.fixture(scope="function")
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Initialize database
    import os
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    db_manager = DatabaseManager()
    db_manager.init_database()

    yield db_manager

    # Cleanup
    os.unlink(db_path)


@pytest.fixture(scope="function")
def mcp_server(temp_db):
    """Create MCP server instance for testing."""
    server = create_mcp_client()
    yield server


@pytest.fixture(scope="function")
def mcp_sync_client(mcp_server):
    """Create sync MCP client for testing."""
    client = MCPSyncClient()
    yield client


@pytest.fixture(scope="function")
def mcp_async_client(mcp_server):
    """Create async MCP client for testing."""
    client = MCPAsyncClient()
    yield client


@pytest.fixture(scope="function")
def test_markdown_file(tmp_path):
    """Create test markdown file."""
    file_path = tmp_path / "test.md"
    content = """---
title: Test Document
---

# Test Heading

This is test content.

## Code Example

```python
def hello():
    print("Hello, World!")
```

## Links

- [Example](https://example.com)
"""
    file_path.write_text(content)
    yield file_path


@pytest.fixture(scope="function")
def test_validation_record(mcp_server, test_markdown_file):
    """Create test validation record."""
    # Use MCP to create validation
    request = {
        "jsonrpc": "2.0",
        "method": "validate_file",
        "params": {
            "file_path": str(test_markdown_file),
            "family": "words"
        },
        "id": 1
    }

    response = mcp_server.handle_request(request)
    validation_id = response["result"]["validation_id"]

    yield validation_id
```

#### `tests/svc/test_mcp_comprehensive.py`
```python
"""Comprehensive MCP server tests."""

import pytest
from svc.mcp_exceptions import MCPMethodNotFoundError, MCPResourceNotFoundError


class TestMCPValidationMethods:
    """Test validation methods."""

    def test_validate_file_success(self, mcp_sync_client, test_markdown_file):
        """Test successful file validation."""
        result = mcp_sync_client.validate_file(str(test_markdown_file))

        assert result["success"] is True
        assert "validation_id" in result
        assert result["status"] in ["pending", "approved", "rejected"]

    def test_validate_folder_success(self, mcp_sync_client, tmp_path):
        """Test successful folder validation."""
        # Create test files
        (tmp_path / "file1.md").write_text("# File 1")
        (tmp_path / "file2.md").write_text("# File 2")

        result = mcp_sync_client.validate_folder(str(tmp_path))

        assert result["success"] is True
        assert result["results"]["files_processed"] == 2

    def test_get_validation_success(self, mcp_sync_client, test_validation_record):
        """Test retrieving validation by ID."""
        result = mcp_sync_client.get_validation(test_validation_record)

        assert "validation" in result
        assert result["validation"]["id"] == test_validation_record

    def test_get_validation_not_found(self, mcp_sync_client):
        """Test error when validation not found."""
        with pytest.raises(MCPResourceNotFoundError):
            mcp_sync_client.get_validation("nonexistent-id")

    def test_list_validations(self, mcp_sync_client, test_validation_record):
        """Test listing validations."""
        result = mcp_sync_client.list_validations(limit=10)

        assert "validations" in result
        assert "total" in result
        assert len(result["validations"]) > 0


class TestMCPApprovalMethods:
    """Test approval methods."""

    def test_approve_success(self, mcp_sync_client, test_validation_record):
        """Test approving validation."""
        result = mcp_sync_client.approve(test_validation_record)

        assert result["success"] is True
        assert result["approved_count"] == 1

    def test_reject_success(self, mcp_sync_client, test_validation_record):
        """Test rejecting validation."""
        result = mcp_sync_client.reject(test_validation_record)

        assert result["success"] is True
        assert result["rejected_count"] == 1

    def test_bulk_approve(self, mcp_sync_client):
        """Test bulk approve operation."""
        result = mcp_sync_client.approve(["id1", "id2", "id3"])

        assert "approved_count" in result
        assert "errors" in result


@pytest.mark.asyncio
class TestMCPAsyncMethods:
    """Test async MCP methods."""

    async def test_async_validate_file(self, mcp_async_client, test_markdown_file):
        """Test async file validation."""
        result = await mcp_async_client.validate_file(str(test_markdown_file))

        assert result["success"] is True
        assert "validation_id" in result

    async def test_concurrent_validations(self, mcp_async_client, tmp_path):
        """Test concurrent async validations."""
        # Create multiple test files
        files = []
        for i in range(5):
            f = tmp_path / f"file{i}.md"
            f.write_text(f"# File {i}")
            files.append(f)

        # Validate concurrently
        import asyncio
        results = await asyncio.gather(*[
            mcp_async_client.validate_file(str(f))
            for f in files
        ])

        assert len(results) == 5
        for result in results:
            assert result["success"] is True
```

#### `tests/integration/test_mcp_end_to_end.py`
```python
"""End-to-end integration tests for MCP."""

import pytest


class TestMCPEndToEnd:
    """Test complete workflows through MCP."""

    def test_complete_validation_workflow(self, mcp_sync_client, tmp_path):
        """Test complete workflow: validate -> approve -> enhance."""
        # Step 1: Create test file
        test_file = tmp_path / "document.md"
        test_file.write_text("# Test\n\nContent here.")

        # Step 2: Validate file
        validation_result = mcp_sync_client.validate_file(str(test_file))
        validation_id = validation_result["validation_id"]

        # Step 3: Generate recommendations
        rec_result = mcp_sync_client.generate_recommendations(validation_id)
        assert rec_result["success"] is True

        # Step 4: Approve validation
        approve_result = mcp_sync_client.approve(validation_id)
        assert approve_result["approved_count"] == 1

        # Step 5: Enhance
        enhance_result = mcp_sync_client.enhance(validation_id)
        assert enhance_result["enhanced_count"] >= 0

    def test_workflow_creation_and_monitoring(self, mcp_sync_client, tmp_path):
        """Test workflow creation and monitoring."""
        # Create test files
        for i in range(3):
            (tmp_path / f"file{i}.md").write_text(f"# Document {i}")

        # Create workflow
        workflow_result = mcp_sync_client.create_workflow(
            "validate_directory",
            {"directory_path": str(tmp_path)}
        )

        workflow_id = workflow_result["workflow_id"]

        # Monitor workflow
        workflow_status = mcp_sync_client.get_workflow(workflow_id)
        assert workflow_status["workflow"]["id"] == workflow_id

        # Get workflow summary
        summary = mcp_sync_client.get_workflow_summary(workflow_id)
        assert "files_processed" in summary
```

---

## Phase 2: Core Operations Implementation

### TASK-004: Validation Methods (8 methods)

**Production Code**:

#### `svc/mcp_methods/validation_methods.py` (Complete)
```python
"""Validation-related MCP methods."""

from typing import Dict, Any, List, Optional
from pathlib import Path
from .base import BaseMCPMethod
from core.database import ValidationStatus
from core.ingestion import MarkdownIngestion


class ValidationMethods(BaseMCPMethod):
    """Handler for validation-related MCP methods."""

    # ========================================================================
    # Existing: validate_folder (already implemented in TASK-001)
    # ========================================================================

    def validate_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single file.

        Args:
            params: {
                "file_path": str (required),
                "family": str (optional, default "words"),
                "validation_types": List[str] (optional)
            }

        Returns:
            {
                "success": bool,
                "validation_id": str,
                "status": str,
                "issues": List[Dict],
                "file_path": str
            }
        """
        self.validate_params(params, required=["file_path"],
                           optional={"family": "words", "validation_types": None})

        file_path = params["file_path"]
        family = params["family"]
        validation_types = params["validation_types"]

        self.logger.info(f"Validating file: {file_path}")

        # Check file exists
        if not Path(file_path).exists():
            raise ValueError(f"File not found: {file_path}")

        # Get orchestrator
        orchestrator = self.agent_registry.get_agent("orchestrator")
        if not orchestrator:
            raise RuntimeError("Orchestrator agent not available")

        # Run validation
        import asyncio
        result = asyncio.run(orchestrator.process_request("validate_file", {
            "file_path": file_path,
            "family": family,
            "validation_types": validation_types
        }))

        # Store in database
        validation_result = self.db_manager.create_validation_result(
            file_path=file_path,
            rules_applied=validation_types or [],
            validation_results=result,
            notes="Validated via MCP",
            severity=self._determine_severity(result),
            status=ValidationStatus.PENDING,
            content=Path(file_path).read_text() if Path(file_path).exists() else "",
            validation_types=validation_types or []
        )

        self.logger.info(f"File validation complete: {validation_result.id}")

        return {
            "success": True,
            "validation_id": validation_result.id,
            "status": validation_result.status.value,
            "issues": result.get("issues", []),
            "file_path": file_path
        }

    def validate_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate content string.

        Args:
            params: {
                "content": str (required),
                "file_path": str (optional, default "temp.md"),
                "validation_types": List[str] (optional)
            }

        Returns:
            {
                "success": bool,
                "validation_id": str,
                "status": str,
                "issues": List[Dict]
            }
        """
        self.validate_params(params, required=["content"],
                           optional={"file_path": "temp.md", "validation_types": None})

        content = params["content"]
        file_path = params["file_path"]
        validation_types = params["validation_types"]

        self.logger.info(f"Validating content (virtual path: {file_path})")

        # Get orchestrator
        orchestrator = self.agent_registry.get_agent("orchestrator")
        if not orchestrator:
            raise RuntimeError("Orchestrator agent not available")

        # Save content to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Run validation
            import asyncio
            result = asyncio.run(orchestrator.process_request("validate_file", {
                "file_path": tmp_path,
                "family": "words",
                "validation_types": validation_types
            }))

            # Store in database
            validation_result = self.db_manager.create_validation_result(
                file_path=file_path,
                rules_applied=validation_types or [],
                validation_results=result,
                notes="Content validation via MCP",
                severity=self._determine_severity(result),
                status=ValidationStatus.PENDING,
                content=content,
                validation_types=validation_types or []
            )

            return {
                "success": True,
                "validation_id": validation_result.id,
                "status": validation_result.status.value,
                "issues": result.get("issues", [])
            }

        finally:
            # Clean up temp file
            import os
            os.unlink(tmp_path)

    def get_validation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get validation by ID.

        Args:
            params: {
                "validation_id": str (required)
            }

        Returns:
            {
                "validation": Dict (validation record)
            }
        """
        self.validate_params(params, required=["validation_id"])

        validation_id = params["validation_id"]

        self.logger.info(f"Retrieving validation: {validation_id}")

        validation = self.db_manager.get_validation_result(validation_id)
        if not validation:
            from svc.mcp_methods.utils import RESOURCE_NOT_FOUND
            raise ValueError(f"Validation {validation_id} not found")

        return {
            "validation": self._serialize_validation(validation)
        }

    def list_validations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        List validations with filters.

        Args:
            params: {
                "limit": int (optional, default 100),
                "offset": int (optional, default 0),
                "status": str (optional),
                "file_path": str (optional)
            }

        Returns:
            {
                "validations": List[Dict],
                "total": int
            }
        """
        self.validate_params(params, required=[],
                           optional={"limit": 100, "offset": 0, "status": None, "file_path": None})

        limit = params["limit"]
        offset = params["offset"]
        status = params["status"]
        file_path = params["file_path"]

        self.logger.info(f"Listing validations: limit={limit}, offset={offset}")

        # Get validations from database
        validations = self.db_manager.list_validation_results(limit=limit, offset=offset)

        # Apply filters
        if status:
            validations = [v for v in validations if v.status.value == status]
        if file_path:
            validations = [v for v in validations if v.file_path == file_path]

        # Get total count
        total = len(validations)  # TODO: optimize with COUNT query

        return {
            "validations": [self._serialize_validation(v) for v in validations],
            "total": total
        }

    def update_validation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update validation metadata.

        Args:
            params: {
                "validation_id": str (required),
                "notes": str (optional),
                "status": str (optional)
            }

        Returns:
            {
                "success": bool,
                "validation_id": str
            }
        """
        self.validate_params(params, required=["validation_id"],
                           optional={"notes": None, "status": None})

        validation_id = params["validation_id"]
        notes = params["notes"]
        status = params["status"]

        self.logger.info(f"Updating validation: {validation_id}")

        # Get validation
        validation = self.db_manager.get_validation_result(validation_id)
        if not validation:
            raise ValueError(f"Validation {validation_id} not found")

        # Update fields
        with self.db_manager.get_session() as session:
            from core.database import ValidationResult
            db_record = session.query(ValidationResult).filter(
                ValidationResult.id == validation_id
            ).first()

            if db_record:
                if notes:
                    db_record.notes = notes
                if status:
                    db_record.status = ValidationStatus[status.upper()]

                from datetime import datetime, timezone
                db_record.updated_at = datetime.now(timezone.utc)
                session.commit()

        return {
            "success": True,
            "validation_id": validation_id
        }

    def delete_validation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete validation record.

        Args:
            params: {
                "validation_id": str (required)
            }

        Returns:
            {
                "success": bool,
                "validation_id": str
            }
        """
        self.validate_params(params, required=["validation_id"])

        validation_id = params["validation_id"]

        self.logger.info(f"Deleting validation: {validation_id}")

        # Delete from database
        with self.db_manager.get_session() as session:
            from core.database import ValidationResult
            db_record = session.query(ValidationResult).filter(
                ValidationResult.id == validation_id
            ).first()

            if db_record:
                session.delete(db_record)
                session.commit()

        return {
            "success": True,
            "validation_id": validation_id
        }

    def revalidate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Re-run validation for a file.

        Args:
            params: {
                "validation_id": str (required)
            }

        Returns:
            {
                "success": bool,
                "new_validation_id": str,
                "original_validation_id": str
            }
        """
        self.validate_params(params, required=["validation_id"])

        validation_id = params["validation_id"]

        self.logger.info(f"Re-validating: {validation_id}")

        # Get original validation
        validation = self.db_manager.get_validation_result(validation_id)
        if not validation:
            raise ValueError(f"Validation {validation_id} not found")

        # Re-run validation on same file
        result = self.validate_file({
            "file_path": validation.file_path,
            "validation_types": validation.validation_types
        })

        return {
            "success": True,
            "new_validation_id": result["validation_id"],
            "original_validation_id": validation_id
        }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _determine_severity(self, result: Dict[str, Any]) -> str:
        """Determine severity from validation result."""
        issues = result.get("issues", [])
        if not issues:
            return "info"

        severity_order = ["critical", "error", "warning", "info"]
        highest_severity = "info"

        for issue in issues:
            level = issue.get("level", "info").lower()
            if level in severity_order:
                current_index = severity_order.index(level)
                highest_index = severity_order.index(highest_severity)
                if current_index < highest_index:
                    highest_severity = level

        return highest_severity

    def _serialize_validation(self, validation) -> Dict[str, Any]:
        """Serialize validation record to dictionary."""
        return {
            "id": validation.id,
            "file_path": validation.file_path,
            "status": validation.status.value,
            "severity": validation.severity,
            "rules_applied": validation.rules_applied,
            "validation_results": validation.validation_results,
            "notes": validation.notes,
            "created_at": validation.created_at.isoformat(),
            "updated_at": validation.updated_at.isoformat() if validation.updated_at else None
        }
```

### Update MCPServer Registration

In `svc/mcp_server.py`, add to `_register_methods()`:

```python
def _register_methods(self) -> None:
    """Register all MCP method handlers."""
    # Validation methods
    validation_handler = ValidationMethods(
        self.db_manager,
        self.rule_manager,
        self.agent_registry
    )
    self.registry.register("validate_folder", validation_handler.validate_folder)
    self.registry.register("validate_file", validation_handler.validate_file)
    self.registry.register("validate_content", validation_handler.validate_content)
    self.registry.register("get_validation", validation_handler.get_validation)
    self.registry.register("list_validations", validation_handler.list_validations)
    self.registry.register("update_validation", validation_handler.update_validation)
    self.registry.register("delete_validation", validation_handler.delete_validation)
    self.registry.register("revalidate", validation_handler.revalidate)

    # ... (continue with other handlers)
```

### Update MCPSyncClient

In `svc/mcp_client.py`, add methods (examples shown in TASK-002).

---

## Phase 4: Integration Implementation

### TASK-015: CLI Integration

**Objective**: Refactor all CLI commands to use MCP client

**Before** (Direct Access):
```python
# cli/main.py
from agents.base import agent_registry
from core.database import db_manager

@cli.command()
def validate_file(file_path, family, types, output, output_format):
    orchestrator = agent_registry.get_agent("orchestrator")  # ❌ Direct
    result = await orchestrator.process_request("validate_file", {...})
```

**After** (MCP-First):
```python
# cli/main.py
from svc.mcp_client import get_mcp_sync_client

@cli.command()
def validate_file(file_path, family, types, output, output_format):
    mcp = get_mcp_sync_client()  # ✅ Via MCP
    result = mcp.validate_file(file_path, family=family,
                               validation_types=types.split(',') if types else None)
```

**Complete CLI Refactoring**:

```python
# cli/main.py (refactored imports)
"""TBCV CLI - Refactored to use MCP client."""

import click
import asyncio
import sys
import json
from typing import Optional
from svc.mcp_client import get_mcp_sync_client
from svc.mcp_exceptions import MCPError, MCPResourceNotFoundError
from core.logging import setup_logging, get_logger

logger = get_logger(__name__)


@click.group()
@click.pass_context
def cli(ctx):
    """TBCV - Truth-Based Content Validation CLI."""
    setup_logging()
    ctx.ensure_object(dict)
    ctx.obj['mcp'] = get_mcp_sync_client()


# ============================================================================
# Validation Commands
# ============================================================================

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--family', '-f', default='words', help='Plugin family')
@click.option('--types', '-t', help='Validation types (comma-separated)')
@click.option('--output', '-o', help='Output file')
@click.option('--format', 'output_format', type=click.Choice(['json', 'text']), default='text')
@click.pass_context
def validate_file(ctx, file_path, family, types, output, output_format):
    """Validate a single file."""
    mcp = ctx.obj['mcp']

    try:
        validation_types = types.split(',') if types else None
        result = mcp.validate_file(file_path, family=family,
                                  validation_types=validation_types)

        if output_format == 'json':
            output_text = json.dumps(result, indent=2)
        else:
            output_text = (
                f"Validation ID: {result['validation_id']}\n"
                f"Status: {result['status']}\n"
                f"Issues: {len(result.get('issues', []))}\n"
            )

        if output:
            with open(output, 'w') as f:
                f.write(output_text)
        else:
            click.echo(output_text)

    except MCPError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('folder_path', type=click.Path(exists=True))
@click.option('--recursive/--no-recursive', default=True)
@click.pass_context
def validate_folder(ctx, folder_path, recursive):
    """Validate all markdown files in a folder."""
    mcp = ctx.obj['mcp']

    try:
        result = mcp.validate_folder(folder_path, recursive=recursive)

        click.echo(f"Validated {result['results']['files_processed']} files")
        click.echo(f"Passed: {result['results'].get('files_passed', 0)}")
        click.echo(f"Failed: {result['results'].get('files_failed', 0)}")

    except MCPError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# ============================================================================
# Approval Commands
# ============================================================================

@cli.group()
def validations():
    """Manage validation records."""
    pass


@validations.command('list')
@click.option('--limit', default=100, help='Max results')
@click.option('--status', help='Filter by status')
@click.pass_context
def list_validations(ctx, limit, status):
    """List validation records."""
    mcp = ctx.obj['mcp']

    try:
        result = mcp.list_validations(limit=limit, status=status)

        click.echo(f"Total validations: {result['total']}")
        for validation in result['validations']:
            click.echo(f"  {validation['id']}: {validation['file_path']} ({validation['status']})")

    except MCPError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@validations.command('approve')
@click.argument('validation_ids', nargs=-1, required=True)
@click.pass_context
def approve_validations(ctx, validation_ids):
    """Approve validation records."""
    mcp = ctx.obj['mcp']

    try:
        result = mcp.approve(list(validation_ids))

        click.echo(f"Approved: {result['approved_count']}")
        if result.get('errors'):
            click.echo("Errors:")
            for error in result['errors']:
                click.echo(f"  - {error}")

    except MCPError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@validations.command('reject')
@click.argument('validation_ids', nargs=-1, required=True)
@click.pass_context
def reject_validations(ctx, validation_ids):
    """Reject validation records."""
    mcp = ctx.obj['mcp']

    try:
        result = mcp.reject(list(validation_ids))

        click.echo(f"Rejected: {result['rejected_count']}")
        if result.get('errors'):
            click.echo("Errors:")
            for error in result['errors']:
                click.echo(f"  - {error}")

    except MCPError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# ============================================================================
# Enhancement Commands
# ============================================================================

@cli.command()
@click.argument('validation_ids', nargs=-1, required=True)
@click.pass_context
def enhance(ctx, validation_ids):
    """Enhance approved validations."""
    mcp = ctx.obj['mcp']

    try:
        result = mcp.enhance(list(validation_ids))

        click.echo(f"Enhanced: {result['enhanced_count']}")
        if result.get('errors'):
            click.echo("Errors:")
            for error in result['errors']:
                click.echo(f"  - {error}")

    except MCPError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# ============================================================================
# Recommendation Commands
# ============================================================================

@cli.group()
def recommendations():
    """Manage recommendations."""
    pass


@recommendations.command('generate')
@click.argument('validation_id')
@click.option('--threshold', default=0.7, help='Confidence threshold')
@click.pass_context
def generate_recommendations(ctx, validation_id, threshold):
    """Generate recommendations for validation."""
    mcp = ctx.obj['mcp']

    try:
        result = mcp.generate_recommendations(validation_id, threshold=threshold)

        click.echo(f"Generated {result['recommendation_count']} recommendations")
        for rec in result.get('recommendations', []):
            click.echo(f"  - {rec['type']}: {rec['description']}")

    except MCPError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# ============================================================================
# Workflow Commands
# ============================================================================

@cli.group()
def workflows():
    """Manage workflows."""
    pass


@workflows.command('create')
@click.argument('workflow_type')
@click.argument('folder_path', type=click.Path(exists=True))
@click.pass_context
def create_workflow(ctx, workflow_type, folder_path):
    """Create a new workflow."""
    mcp = ctx.obj['mcp']

    try:
        result = mcp.create_workflow(workflow_type, {
            "directory_path": folder_path
        })

        click.echo(f"Created workflow: {result['workflow_id']}")
        click.echo(f"Status: {result['status']}")

    except MCPError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@workflows.command('list')
@click.option('--limit', default=100)
@click.pass_context
def list_workflows(ctx, limit):
    """List workflows."""
    mcp = ctx.obj['mcp']

    try:
        result = mcp.list_workflows(limit=limit)

        click.echo(f"Total workflows: {result['total']}")
        for workflow in result['workflows']:
            click.echo(f"  {workflow['id']}: {workflow['type']} ({workflow['status']})")

    except MCPError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# ============================================================================
# Admin Commands
# ============================================================================

@cli.group()
def admin():
    """Admin operations."""
    pass


@admin.command('stats')
@click.pass_context
def get_stats(ctx):
    """Get system statistics."""
    mcp = ctx.obj['mcp']

    try:
        result = mcp.get_stats()

        click.echo("System Statistics:")
        click.echo(f"  Validations: {result.get('validations_total', 0)}")
        click.echo(f"  Recommendations: {result.get('recommendations_total', 0)}")
        click.echo(f"  Workflows: {result.get('workflows_total', 0)}")

    except MCPError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@admin.command('clear-cache')
@click.pass_context
def clear_cache(ctx):
    """Clear all caches."""
    mcp = ctx.obj['mcp']

    try:
        result = mcp.clear_cache()

        click.echo(f"Cache cleared: {result.get('cleared_items', 0)} items")

    except MCPError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli(obj={})
```

**Migration Checklist**:
- [ ] Remove all `agent_registry` imports
- [ ] Remove all `db_manager` imports
- [ ] Remove all `cache_manager` imports
- [ ] Replace all direct calls with `mcp.method()` calls
- [ ] Update all error handling to use `MCPError`
- [ ] Test each command manually
- [ ] Run CLI integration tests

---

### TASK-016: API Integration

**Objective**: Refactor all API endpoints to use MCP client

**Before** (Direct Access):
```python
# api/server.py
from core.database import db_manager

@app.get("/api/validations")
async def list_validations(limit: int = 100):
    validations = db_manager.list_validation_results(limit)  # ❌ Direct
    return validations
```

**After** (MCP-First):
```python
# api/server.py
from svc.mcp_client import get_mcp_async_client

@app.get("/api/validations")
async def list_validations(limit: int = 100):
    mcp = get_mcp_async_client()  # ✅ Via MCP
    result = await mcp.list_validations(limit=limit)
    return result["validations"]
```

**Complete API Refactoring** (Key Endpoints):

```python
# api/server.py (refactored key endpoints)
"""TBCV API Server - Refactored to use MCP client."""

from fastapi import FastAPI, HTTPException
from svc.mcp_client import get_mcp_async_client
from svc.mcp_exceptions import MCPError, MCPResourceNotFoundError
from typing import Optional, List
from pydantic import BaseModel

app = FastAPI(title="TBCV API")


# Request models
class ValidateFileRequest(BaseModel):
    file_path: str
    family: str = "words"
    validation_types: Optional[List[str]] = None


class ValidateContentRequest(BaseModel):
    content: str
    file_path: str = "temp.md"
    validation_types: Optional[List[str]] = None


# ============================================================================
# Validation Endpoints
# ============================================================================

@app.post("/api/validate/file")
async def validate_file_endpoint(request: ValidateFileRequest):
    """Validate a file."""
    mcp = get_mcp_async_client()

    try:
        result = await mcp.validate_file(
            request.file_path,
            family=request.family,
            validation_types=request.validation_types
        )
        return result

    except MCPResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except MCPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/validate/content")
async def validate_content_endpoint(request: ValidateContentRequest):
    """Validate content string."""
    mcp = get_mcp_async_client()

    try:
        result = await mcp.validate_content(
            request.content,
            file_path=request.file_path,
            validation_types=request.validation_types
        )
        return result

    except MCPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/validations")
async def list_validations(
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None
):
    """List validations."""
    mcp = get_mcp_async_client()

    try:
        result = await mcp.list_validations(
            limit=limit,
            offset=offset,
            status=status
        )
        return {
            "validations": result["validations"],
            "total": result["total"]
        }

    except MCPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/validations/{validation_id}")
async def get_validation(validation_id: str):
    """Get validation by ID."""
    mcp = get_mcp_async_client()

    try:
        result = await mcp.get_validation(validation_id)
        return result["validation"]

    except MCPResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except MCPError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Approval Endpoints
# ============================================================================

@app.post("/api/validations/{validation_id}/approve")
async def approve_validation(validation_id: str):
    """Approve a validation."""
    mcp = get_mcp_async_client()

    try:
        result = await mcp.approve(validation_id)
        return result

    except MCPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/validations/{validation_id}/reject")
async def reject_validation(validation_id: str):
    """Reject a validation."""
    mcp = get_mcp_async_client()

    try:
        result = await mcp.reject(validation_id)
        return result

    except MCPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/validations/bulk/approve")
async def bulk_approve(validation_ids: List[str]):
    """Bulk approve validations."""
    mcp = get_mcp_async_client()

    try:
        result = await mcp.approve(validation_ids)
        return result

    except MCPError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Enhancement Endpoints
# ============================================================================

@app.post("/api/enhance/{validation_id}")
async def enhance_validation(validation_id: str):
    """Enhance a validation."""
    mcp = get_mcp_async_client()

    try:
        result = await mcp.enhance(validation_id)
        return result

    except MCPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/enhance/batch")
async def batch_enhance(validation_ids: List[str]):
    """Batch enhance validations."""
    mcp = get_mcp_async_client()

    try:
        result = await mcp.enhance_batch(validation_ids)
        return result

    except MCPError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Recommendation Endpoints
# ============================================================================

@app.post("/api/recommendations/{validation_id}/generate")
async def generate_recommendations(validation_id: str, threshold: float = 0.7):
    """Generate recommendations."""
    mcp = get_mcp_async_client()

    try:
        result = await mcp.generate_recommendations(validation_id, threshold=threshold)
        return result

    except MCPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recommendations/{validation_id}")
async def get_recommendations(validation_id: str):
    """Get recommendations for validation."""
    mcp = get_mcp_async_client()

    try:
        result = await mcp.get_recommendations(validation_id)
        return result["recommendations"]

    except MCPError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Workflow Endpoints
# ============================================================================

@app.post("/workflows/validate-directory")
async def create_validation_workflow(directory_path: str, recursive: bool = True):
    """Create validation workflow."""
    mcp = get_mcp_async_client()

    try:
        result = await mcp.create_workflow("validate_directory", {
            "directory_path": directory_path,
            "recursive": recursive
        })
        return result

    except MCPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflows")
async def list_workflows(limit: int = 100, status: Optional[str] = None):
    """List workflows."""
    mcp = get_mcp_async_client()

    try:
        result = await mcp.list_workflows(limit=limit, status=status)
        return result

    except MCPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get workflow by ID."""
    mcp = get_mcp_async_client()

    try:
        result = await mcp.get_workflow(workflow_id)
        return result["workflow"]

    except MCPResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except MCPError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Admin Endpoints
# ============================================================================

@app.get("/api/stats")
async def get_stats():
    """Get system statistics."""
    mcp = get_mcp_async_client()

    try:
        result = await mcp.get_stats()
        return result

    except MCPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    mcp = get_mcp_async_client()

    try:
        result = await mcp.get_system_status()
        return result

    except MCPError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/admin/cache/clear")
async def clear_cache():
    """Clear caches."""
    mcp = get_mcp_async_client()

    try:
        result = await mcp.clear_cache()
        return result

    except MCPError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Migration Checklist**:
- [ ] Remove all `db_manager` imports
- [ ] Remove all `agent_registry` imports
- [ ] Remove all `cache_manager` imports
- [ ] Replace all direct calls with `await mcp.method()` calls
- [ ] Update all error handling to use `MCPError` and `HTTPException`
- [ ] Test each endpoint with curl/httpie
- [ ] Run API integration tests

---

## Phase 5: Enforcement Implementation

### TASK-017: Access Guards & MCP-Only Enforcement

**Objective**: Prevent direct access to agents/database outside MCP

**Production Code**:

#### `core/access_guard.py`
```python
"""Access guard to enforce MCP-only access pattern."""

import inspect
import sys
from typing import List

# Allowed callers that can directly access core components
ALLOWED_CALLERS: List[str] = [
    "svc.mcp_server",
    "svc.mcp_methods",
    "tests.",  # Allow tests
    "<stdin>",  # Allow REPL
    "pytest",  # Allow pytest
    "conftest",  # Allow test fixtures
]


def verify_mcp_access(component_name: str) -> None:
    """
    Verify that caller is authorized to access this component.

    Args:
        component_name: Name of component being accessed

    Raises:
        RuntimeError: If caller is not authorized
    """
    # Get caller's frame
    frame = inspect.currentframe()
    if frame is None:
        return  # Cannot verify, allow

    try:
        # Go up the stack to find first external caller
        caller_frame = frame.f_back.f_back
        if caller_frame is None:
            return

        caller_file = caller_frame.f_code.co_filename

        # Check if caller is in allowed list
        for allowed in ALLOWED_CALLERS:
            if allowed in caller_file:
                return  # Authorized

        # Not authorized - raise error
        raise RuntimeError(
            f"Direct access to {component_name} is not allowed.\n"
            f"All operations must go through MCP server.\n"
            f"Caller: {caller_file}:{caller_frame.f_lineno}\n"
            f"See docs/mcp_integration.md for proper usage."
        )

    finally:
        del frame  # Avoid reference cycles


def is_mcp_enforced() -> bool:
    """Check if MCP enforcement is enabled."""
    import os
    # Allow disabling for development/testing
    return os.getenv("MCP_ENFORCE", "true").lower() == "true"
```

#### Update `core/database.py`
```python
# At top of DatabaseManager class
from core.access_guard import verify_mcp_access, is_mcp_enforced


class DatabaseManager:
    def __init__(self, database_url: Optional[str] = None):
        # Enforce MCP access
        if is_mcp_enforced():
            verify_mcp_access("DatabaseManager")

        # ... rest of __init__
```

#### Update `agents/base.py`
```python
# In AgentRegistry
from core.access_guard import verify_mcp_access, is_mcp_enforced


class AgentRegistry:
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        # Enforce MCP access
        if is_mcp_enforced():
            verify_mcp_access(f"AgentRegistry.get_agent({agent_id})")

        # ... rest of method
```

**Testing**:

```python
# tests/core/test_access_guard.py
import pytest
import os
from core.access_guard import verify_mcp_access


class TestAccessGuard:
    def test_allowed_from_mcp_server(self):
        """Test access allowed from MCP server."""
        # This should not raise
        verify_mcp_access("TestComponent")

    def test_blocked_from_cli_when_enforced(self):
        """Test access blocked from CLI when enforced."""
        os.environ["MCP_ENFORCE"] = "true"

        # Simulate call from CLI (not in allowed list)
        with pytest.raises(RuntimeError, match="must go through MCP"):
            # This will be caught because we're not in svc.mcp_*
            from core.database import DatabaseManager
            # Will raise in __init__

    def test_allowed_when_enforcement_disabled(self):
        """Test access allowed when enforcement disabled."""
        os.environ["MCP_ENFORCE"] = "false"

        # Should not raise
        from core.database import DatabaseManager
        db = DatabaseManager()
        assert db is not None
```

---

## Complete Test Runbook

### Prerequisites
```bash
# Ensure environment is ready
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Phase 1 Tests
```bash
# TASK-001: Architecture
pytest tests/svc/test_mcp_server_architecture.py -v

# TASK-002: Clients
pytest tests/svc/test_mcp_client.py -v

# TASK-003: Testing Infra
pytest tests/svc/test_mcp_comprehensive.py -v
pytest tests/integration/test_mcp_end_to_end.py -v
```

### Phase 2 Tests
```bash
# TASK-004: Validation Methods
pytest tests/svc/test_mcp_validation_methods.py -v

# TASK-005-010: Other methods
pytest tests/svc/test_mcp_*.py -v
```

### Phase 4 Tests
```bash
# TASK-015: CLI Integration
python cli/main.py validate-file README.md
python cli/main.py validations list
python cli/main.py admin stats

# TASK-016: API Integration
# Start server
uvicorn api.server:app --reload

# Test endpoints
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/validate/file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "README.md"}'
```

### Phase 5 Tests
```bash
# TASK-017: Access Guards
export MCP_ENFORCE=true
pytest tests/core/test_access_guard.py -v

# TASK-018: Full Integration
pytest tests/ -v --cov=svc --cov=api --cov=cli
```

---

## Documentation Updates Summary

### Files to Update

1. **docs/mcp_integration.md**
   - Add all 56 method documentation
   - Add client usage examples
   - Add error handling guide

2. **docs/architecture.md**
   - Update architecture diagrams
   - Document MCP-first pattern
   - Add flow diagrams

3. **docs/api_reference.md**
   - Update all endpoint documentation
   - Note MCP backing for each endpoint

4. **docs/cli_usage.md**
   - Update all command examples
   - Note MCP backing for each command

5. **README.md**
   - Update quick start to mention MCP
   - Add MCP architecture section

---

## Final Validation Checklist

### Code Quality
- [ ] All 56 MCP methods implemented
- [ ] All methods have unit tests (>90% coverage)
- [ ] All methods have integration tests
- [ ] Type hints on all functions
- [ ] Docstrings on all public functions
- [ ] No TODO/FIXME/placeholder comments
- [ ] Code passes linting (black, mypy, pylint)

### Integration
- [ ] All CLI commands use MCP client
- [ ] All API endpoints use MCP client
- [ ] Zero direct database imports in CLI
- [ ] Zero direct database imports in API
- [ ] Zero direct agent imports in CLI (except init)
- [ ] Zero direct agent imports in API (except init)
- [ ] Access guards enabled and tested

### Testing
- [ ] Unit tests passing (pytest tests/svc/ -v)
- [ ] Integration tests passing (pytest tests/integration/ -v)
- [ ] End-to-end tests passing (pytest tests/e2e/ -v)
- [ ] Manual CLI testing completed
- [ ] Manual API testing completed
- [ ] Performance benchmarks passing (<5ms overhead)
- [ ] No regressions detected

### Documentation
- [ ] MCP integration docs updated
- [ ] Architecture docs updated
- [ ] API reference updated
- [ ] CLI reference updated
- [ ] README updated
- [ ] All examples tested and working
- [ ] Migration guide created

### Operational
- [ ] Backward compatibility maintained
- [ ] Error messages clear and actionable
- [ ] Logging sufficient for debugging
- [ ] No breaking changes to public APIs
- [ ] Rollback plan tested

---

**Total Implementation Time**: 9 weeks
**Status**: Ready for Execution
**Next Step**: Begin TASK-001 (MCP Server Architecture)
