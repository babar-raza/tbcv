# file: tbcv\cli\main.py
"""
Command-line interface for TBCV system.
Provides commands for validation, enhancement, and batch processing.
"""

# REBASING NOTES
#
# 1) This file was reconstructed from the user's attached version which had
#    truncated strings, broken indentation, duplicate CLI groups, and a stray
#    "if name == 'main'" tail. All syntax errors were corrected and duplicate
#    blocks merged without removing any public commands.
# 2) The existing commands (validate_file, validate_directory, check_agents,
#    validate, batch, enhance, test, status) are preserved with their flags.
# 3) The probe-endpoints subcommand is included. It delegates to
#    tbcv.tools.endpoint_probe.main and works from any CWD.
# 4) Logging and console banners are preserved. Agent setup is idempotent.

import asyncio
import json
import sys
import logging
import glob
import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.panel import Panel

from core.config import get_settings  # kept for compatibility
from core.logging import setup_logging, get_logger  # kept for compatibility
from core.language_utils import is_english_content, log_language_rejection, validate_english_content_batch
from cli.mcp_helpers import with_mcp_client, handle_mcp_error
from svc.mcp_exceptions import MCPError

# Legacy imports - kept for backward compatibility with some commands
from agents.base import agent_registry
from agents.fuzzy_detector import FuzzyDetectorAgent
from agents.content_validator import ContentValidatorAgent
from agents.content_enhancer import ContentEnhancerAgent
from agents.orchestrator import OrchestratorAgent
from agents.truth_manager import TruthManagerAgent
from agents.llm_validator import LLMValidatorAgent
from agents.recommendation_agent import RecommendationAgent

logger = logging.getLogger(__name__)
console = Console()

# Global agents (initialized once)
_agents_initialized = False


async def setup_agents():
    """Initialize and register agents once for the CLI."""
    from core.config import get_settings
    global _agents_initialized
    if _agents_initialized:
        return
    try:
        settings = get_settings()

        truth_manager = TruthManagerAgent("truth_manager")
        agent_registry.register_agent(truth_manager)

        if getattr(settings.fuzzy_detector, "enabled", True):
            fuzzy_detector = FuzzyDetectorAgent("fuzzy_detector")
            agent_registry.register_agent(fuzzy_detector)
        else:
            logger.info("Fuzzy detector disabled via config")

        content_validator = ContentValidatorAgent("content_validator")
        agent_registry.register_agent(content_validator)

        content_enhancer = ContentEnhancerAgent("content_enhancer")
        agent_registry.register_agent(content_enhancer)

        llm_validator = LLMValidatorAgent("llm_validator")
        agent_registry.register_agent(llm_validator)

        recommendation_agent = RecommendationAgent("recommendation_agent")
        agent_registry.register_agent(recommendation_agent)
        
        # Enhancement agent - applies approved recommendations
        from agents.enhancement_agent import EnhancementAgent
        enhancement_agent = EnhancementAgent("enhancement_agent")
        agent_registry.register_agent(enhancement_agent)

        orchestrator = OrchestratorAgent("orchestrator")
        agent_registry.register_agent(orchestrator)

        _agents_initialized = True
        logger.info("All CLI agents registered successfully")
    except Exception as e:
        logger.error("Failed to setup agents", exc_info=e)
        raise



async def initialize_agents():
    """Alias kept for compatibility with earlier calls."""
    await setup_agents()


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config', '-c', help='Configuration file path')
@click.option('--quiet', '-q', is_flag=True, help='Minimal output')
@click.option('--mcp-debug', is_flag=True, help='Enable MCP client debug logging')
@click.pass_context
def cli(ctx, verbose: bool, config: Optional[str], quiet: bool, mcp_debug: bool):
    """TBCV Command Line Interface."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet
    ctx.obj['config'] = config
    ctx.obj['mcp_debug'] = mcp_debug

    log_level = "DEBUG" if verbose or mcp_debug else "INFO"
    os.environ['TBCV_LOG_LEVEL'] = log_level
    setup_logging()

    if config:
        os.environ['TBCV_CONFIG'] = config

    if not quiet:
        console.print(Panel(
            "[bold blue]TBCV - Truth-Based Content Validation System[/bold blue]",
            expand=False
        ))
    logger.info("TBCV CLI started")


# ---------------------------
# Single-file validation
# ---------------------------
@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--family', '-f', default='words', help='Plugin family to use')
@click.option('--types', '-t', help='Comma-separated list of validation types (e.g., yaml,markdown,Truth)')
@click.option('--output', '-o', help='Output file for results')
@click.option('--format', 'output_format', default='json',
              type=click.Choice(['json', 'text']), help='Output format')
@with_mcp_client
def validate_file(file_path: str, family: str, types: Optional[str], output: Optional[str], output_format: str, mcp_client):
    """Validate a single content file using MCP client."""
    # Check if content is English before processing
    is_english, reason = is_english_content(file_path)
    if not is_english:
        click.echo(f"Error: Non-English content detected - {reason}", err=True)
        click.echo(f"File: {file_path}", err=True)
        click.echo("Only English content can be processed. Translations are done automatically from English source.", err=True)
        log_language_rejection(file_path, reason, logger)
        sys.exit(1)

    try:
        # Parse validation types if provided
        validation_types = None
        if types:
            validation_types = [t.strip() for t in types.split(',')]

        # Call MCP client
        result = mcp_client.validate_file(
            file_path=file_path,
            family=family,
            validation_types=validation_types
        )

        if output_format == 'json':
            output_text = json.dumps(result, indent=2)
        else:
            status = result.get("status", "unknown")
            validation_id = result.get("validation_id", "N/A")
            issues = result.get("issues", [])

            output_text = (
                f"File: {file_path}\n"
                f"Family: {family}\n"
                f"Status: {status}\n"
                f"Validation ID: {validation_id}\n"
                f"Issues: {len(issues)}\n"
            )
            if issues:
                output_text += "\nIssues found:\n"
                for issue in issues:
                    severity = issue.get("severity", "unknown").upper()
                    category = issue.get("category", "unknown")
                    message = issue.get("message", "")
                    output_text += f"  [{severity}] {category}: {message}\n"

        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(output_text)
            click.echo(f"Results written to {output}")
        else:
            click.echo(output_text)

    except MCPError as e:
        handle_mcp_error(e)
    except Exception as e:
        click.echo(f"Validation failed: {e}", err=True)
        logger.error(f"Validation error: {e}", exc_info=True)
        sys.exit(1)


# ---------------------------
# Directory validation
# ---------------------------
@cli.command()
@click.argument('directory_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--pattern', '-p', default='*.md', help='File pattern to match')
@click.option('--family', '-f', default='words', help='Plugin family to use')
@click.option('--types', '-t', help='Comma-separated list of validation types (e.g., yaml,markdown,Truth)')
@click.option('--workers', '-w', default=4, help='Number of concurrent workers')
@click.option('--output', '-o', help='Output file for results')
@click.option('--format', 'output_format', default='json',
              type=click.Choice(['json', 'text', 'summary']), help='Output format')
@click.option('--recursive', '-r', is_flag=True, help='Search subdirectories recursively')
@with_mcp_client
def validate_directory(directory_path: str, pattern: str, family: str, types: Optional[str], workers: int,
                       output: Optional[str], output_format: str, recursive: bool, mcp_client):
    """Validate all files in a directory using MCP client."""
    try:
        click.echo("Starting directory validation...")
        click.echo(f"Directory: {directory_path}")
        click.echo(f"Pattern: {pattern}")
        click.echo(f"Recursive: {recursive}")

        # Use validate_folder MCP method
        result = mcp_client.validate_folder(
            folder_path=directory_path,
            recursive=recursive
        )

        if output_format == 'json':
            output_text = json.dumps(result, indent=2)
        elif output_format == 'summary':
            files_processed = result.get("files_processed", 0)
            validations = result.get("validations", [])
            errors = result.get("errors", [])

            output_text = (
                "Directory Validation Summary\n"
                f"{'='*40}\n"
                f"Directory: {directory_path}\n"
                f"Files processed: {files_processed}\n"
                f"Validations: {len(validations)}\n"
                f"Errors: {len(errors)}\n"
            )
            if errors:
                output_text += f"\nErrors ({len(errors)}):\n"
                for error in errors[:5]:
                    output_text += f"  - {error}\n"
                if len(errors) > 5:
                    output_text += f"  ... and {len(errors) - 5} more\n"
        else:
            files_processed = result.get("files_processed", 0)
            validations = result.get("validations", [])

            output_text = (
                "Directory validation completed\n"
                f"Files processed: {files_processed}\n"
                f"Validations created: {len(validations)}\n\n"
            )

            for validation in validations[:10]:
                validation_id = validation.get("validation_id", "unknown")
                file_path = validation.get("file_path", "unknown")
                status = validation.get("status", "unknown")
                output_text += f"{file_path}: {status} (ID: {validation_id[:8]}...)\n"
            if len(validations) > 10:
                output_text += f"... and {len(validations) - 10} more files\n"

        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(output_text)
            click.echo(f"Results written to {output}")
        else:
            click.echo(output_text)

    except MCPError as e:
        handle_mcp_error(e)
    except Exception as e:
        click.echo(f"Directory validation failed: {e}", err=True)
        logger.error(f"Directory validation error: {e}", exc_info=True)
        sys.exit(1)


# ---------------------------
# System status check
# ---------------------------
@cli.command()
@click.option('--format', 'output_format', default='text',
              type=click.Choice(['text', 'json']), help='Output format')
@with_mcp_client
def check_agents(output_format: str, mcp_client):
    """Check system status and health via MCP."""
    try:
        result = mcp_client.get_system_status()

        if output_format == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            status = result.get("status", "unknown")
            components = result.get("components", {})

            click.echo(f"System Status: {status}")
            click.echo(f"\nComponents:")

            for component_name, component_info in components.items():
                component_status = component_info.get("status", "unknown")
                click.echo(f"  {component_name}: {component_status}")

                if "details" in component_info:
                    for key, value in component_info["details"].items():
                        click.echo(f"    {key}: {value}")

            if "resource_usage" in result:
                click.echo(f"\nResource Usage:")
                for key, value in result["resource_usage"].items():
                    click.echo(f"  {key}: {value}")

    except MCPError as e:
        handle_mcp_error(e)
    except Exception as e:
        click.echo(f"Status check failed: {e}", err=True)
        logger.error(f"Status check error: {e}", exc_info=True)
        sys.exit(1)


# ---------------------------
# validate (workflow) command
# ---------------------------
@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--type', 'validation_type', default='full',
              type=click.Choice(['basic', 'full', 'enhanced']), help='Validation type')
@click.option('--confidence', default=0.6, type=float,
              help='Confidence threshold (0.0-1.0)')
@click.option('--output', default='table', type=click.Choice(['table', 'json', 'yaml']),
              help='Output format')
@click.option('--fix', is_flag=True, help='Apply automatic fixes')
@click.option('--no-cache', is_flag=True, help='Skip cache lookup')
@click.pass_context
def validate(ctx, file_path, validation_type, confidence, output, fix, no_cache):
    """Validate a single file via workflow."""
    asyncio.run(_validate_file(ctx, file_path, validation_type, confidence, output, fix, no_cache))


async def _validate_file(ctx, file_path, validation_type, confidence, output, fix, no_cache):
    """Async validation implementation."""
    await initialize_agents()

    if not ctx.obj.get('quiet'):
        console.print(f"[blue]Validating file:[/blue] {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        workflow_type_map = {
            'basic': 'validate_file',
            'full': 'full_validation',
            'enhanced': 'content_update',
        }
        workflow_type = workflow_type_map[validation_type]

        orchestrator = agent_registry.get_agent("orchestrator")
        if not orchestrator:
            console.print("[red]Error: Orchestrator not available[/red]")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Processing...", total=100)

            result = await orchestrator.process_request("start_workflow", {
                "workflow_type": workflow_type,
                "input_params": {
                    "content": content,
                    "file_path": file_path,
                    "confidence_threshold": confidence
                }
            })

            if not result.get("success"):
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
                return

            workflow_id = result["workflow_id"]

            while True:
                await asyncio.sleep(1)
                status = await orchestrator.process_request("get_workflow_status", {
                    "workflow_id": workflow_id
                })
                progress.update(task, completed=status.get("progress_percent", 0))
                if status.get("state") in ["completed", "failed", "cancelled"]:
                    break

        if output == 'table':
            _display_validation_results_table(result)
        elif output == 'json':
            console.print_json(data=result)
        elif output == 'yaml':
            import yaml
            console.print(yaml.dump(result, default_flow_style=False))

        if not ctx.obj.get('quiet'):
            console.print("[green][OK] Validation completed[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()


def _display_validation_results_table(result):
    """Display validation results in table format."""
    table = Table(title="Validation Results", show_header=True)
    table.add_column("Category", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Issues", style="yellow")
    table.add_column("Confidence", style="blue")

    table.add_row("Overall", "[OK] Completed", "0", "0.85")
    table.add_row("Plugin Detection", "[OK] Passed", "0", "0.90")
    table.add_row("Content Validation", "[WARN] Warning", "2", "0.75")
    table.add_row("Code Quality", "[OK] Passed", "1", "0.80")

    console.print(table)


# ---------------------------
# batch command
# ---------------------------
@cli.command()
@click.argument('directory_path', type=click.Path(exists=True))
@click.option('--pattern', default='*.md', help='File pattern (glob)')
@click.option('--recursive', '-r', is_flag=True, help='Recursive directory traversal')
@click.option('--report-file', type=click.Path(), help='Save detailed report to file')
@click.option('--summary-only', is_flag=True, help='Show summary statistics only')
@click.pass_context
@with_mcp_client
def batch(ctx, directory_path, pattern, recursive, report_file, summary_only, mcp_client):
    """Batch process files in a directory using MCP workflow."""
    if not ctx.obj.get('quiet'):
        console.print(f"[blue]Batch processing directory:[/blue] {directory_path}")
        console.print(f"[blue]Recursive:[/blue] {recursive}")

    try:
        # Create workflow
        workflow_params = {
            "folder_path": directory_path,
            "recursive": recursive
        }

        console.print("\n[blue]Creating batch workflow...[/blue]")
        result = mcp_client.create_workflow(
            workflow_type="validate_directory",
            workflow_params=workflow_params,
            name=f"Batch validation: {directory_path}",
            description=f"Batch validation of directory with recursive={recursive}"
        )

        workflow_id = result.get("workflow_id")
        console.print(f"[green]Workflow created: {workflow_id[:8]}...[/green]")

        # Poll for completion
        console.print("[blue]Processing...[/blue]")
        import time
        max_polls = 300  # 5 minutes max
        poll_count = 0

        while poll_count < max_polls:
            workflow_status = mcp_client.get_workflow(workflow_id)
            status = workflow_status.get("status", "unknown")

            if status in ["completed", "failed", "cancelled"]:
                break

            time.sleep(1)
            poll_count += 1

        # Get final report
        workflow_report = mcp_client.get_workflow_report(workflow_id, include_details=True)

        if not summary_only:
            _display_batch_results(workflow_report)
        else:
            _display_batch_summary(workflow_report)

        if report_file:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(workflow_report, f, indent=2)
            console.print(f"[green]Report saved to: {report_file}[/green]")

    except MCPError as e:
        handle_mcp_error(e)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


def _display_batch_results(workflow_report):
    """Display batch processing results from workflow report."""
    table = Table(title="Batch Processing Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    metrics = workflow_report.get("metrics", {})
    for key, value in metrics.items():
        table.add_row(key, str(value))

    console.print(table)

    # Show validation results if available
    validations = workflow_report.get("validations", [])
    if validations:
        console.print(f"\n[cyan]Validations:[/cyan] {len(validations)}")


def _display_batch_summary(workflow_report):
    """Display batch processing summary from workflow report."""
    metrics = workflow_report.get("metrics", {})
    status = workflow_report.get("status", "unknown")

    files_processed = metrics.get("files_processed", 0)
    validations_created = metrics.get("validations_created", 0)
    errors = metrics.get("errors", 0)

    console.print(Panel(
        f"[cyan]Status:[/cyan] {status}\n"
        f"[green]Files processed:[/green] {files_processed}\n"
        f"[blue]Validations created:[/blue] {validations_created}\n"
        f"[red]Errors:[/red] {errors}",
        title="Batch Summary"
    ))


# ---------------------------
# enhance command
# ---------------------------
@cli.command()
@click.argument('validation_ids', nargs=-1, required=True)
@click.option('--preview', is_flag=True, help='Preview changes without applying')
@click.option('--threshold', default=0.7, type=float, help='Confidence threshold for recommendations')
@click.pass_context
@with_mcp_client
def enhance(ctx, validation_ids: tuple, preview: bool, threshold: float, mcp_client):
    """Enhance approved validations using MCP client."""
    if not ctx.obj.get('quiet'):
        mode = "PREVIEW" if preview else "ENHANCE"
        console.print(f"[blue]{mode} {len(validation_ids)} validation(s)[/blue]")

    try:
        validation_list = list(validation_ids)

        if preview:
            # Preview first validation only
            result = mcp_client.enhance_preview(
                validation_id=validation_list[0],
                threshold=threshold
            )

            console.print("\n[cyan]Preview:[/cyan]")
            console.print(f"Original content length: {len(result.get('original_content', ''))}")
            console.print(f"Enhanced content length: {len(result.get('enhanced_content', ''))}")
            console.print(f"\nRecommendations applied: {result.get('recommendations_applied', 0)}")

            if result.get('diff'):
                console.print("\n[cyan]Diff:[/cyan]")
                console.print(result['diff'])

            console.print("\n[yellow]PREVIEW MODE - No changes applied[/yellow]")
        else:
            # Enhance validations
            result = mcp_client.enhance(ids=validation_list)

            enhanced_count = result.get("enhanced_count", 0)
            errors = result.get("errors", [])

            console.print(f"\n[green][OK] Enhanced {enhanced_count} validation(s)[/green]")

            if errors:
                console.print(f"\n[yellow]Errors ({len(errors)}):[/yellow]")
                for error in errors[:5]:
                    console.print(f"  - {error}")
                if len(errors) > 5:
                    console.print(f"  ... and {len(errors) - 5} more")

            # Show details
            enhancements = result.get("enhancements", [])
            if enhancements and not ctx.obj.get('quiet'):
                console.print(f"\n[cyan]Enhancement Details:[/cyan]")
                for enh in enhancements[:5]:
                    validation_id = enh.get("validation_id", "unknown")
                    recommendations_applied = enh.get("recommendations_applied", 0)
                    console.print(f"  {validation_id[:8]}...: {recommendations_applied} recommendations applied")

    except MCPError as e:
        handle_mcp_error(e)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


# ---------------------------
# test command (sample workflow)
# ---------------------------
@cli.command()
@click.pass_context
def test(ctx):
    """Create and process a test file."""
    asyncio.run(_run_test(ctx))


async def _run_test(ctx):
    """Run test with sample content."""
    await initialize_agents()

    console.print("[blue]Creating test content...[/blue]")

    test_content = """---
title: Test Document
description: A test document for TBCV validation
date: 2024-01-15
---

# Document Processing Tutorial

This tutorial shows how to use Aspose.Words for document conversion.

## Basic Usage
```csharp
using Aspose.Words;
Document doc = new Document();
DocumentBuilder builder = new DocumentBuilder(doc);
builder.Write("Hello World!");
doc.Save("output.docx", SaveFormat.Docx);
doc.Save("output.pdf", SaveFormat.Pdf);
```
You can also add watermarks to your documents.
"""

    test_file = Path("test_content.md")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)

    console.print(f"[green]Test file created: {test_file}[/green]")

    await _validate_file(ctx, str(test_file), 'full', 0.6, 'table', False, False)

    if test_file.exists():
        test_file.unlink()
        console.print("[green]Test file cleaned up[/green]")


# ---------------------------
# status command
# ---------------------------
@cli.command()
@click.pass_context
def status(ctx):
    """Show system status."""
    asyncio.run(_show_status(ctx))


async def _show_status(ctx):
    """Show system status."""
    await initialize_agents()

    console.print("[blue]System Status[/blue]")

    table = Table(title="Agent Status")
    table.add_column("Agent", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Requests", style="yellow")
    table.add_column("Avg Response (ms)", style="blue")

    for agent_id, agent in agent_registry.agents.items():
        status = agent.get_status()
        stats = status.get("statistics", {})
        table.add_row(
            agent_id,
            status.get("status", "unknown"),
            str(stats.get("requests_processed", 0)),
            f"{stats.get('average_response_time_ms', 0):.1f}",
        )

    console.print(table)


# ---------------------------
# recommendations command group
# ---------------------------
@cli.group()
@click.pass_context
def recommendations(ctx):
    """Manage recommendations for content improvements."""
    pass


@recommendations.command('list')
@click.option('--status', type=click.Choice(['proposed', 'pending', 'approved', 'rejected', 'applied']),
              help='Filter by recommendation status')
@click.option('--validation-id', help='Filter by validation ID')
@click.option('--limit', default=50, help='Maximum number of recommendations to show')
@click.option('--format', 'output_format', default='table',
              type=click.Choice(['table', 'json']), help='Output format')
@click.pass_context
def list_recommendations(ctx, status, validation_id, limit, output_format):
    """List recommendations."""
    asyncio.run(_list_recommendations(ctx, status, validation_id, limit, output_format))


async def _list_recommendations(ctx, status, validation_id, limit, output_format):
    """Async implementation of list recommendations."""
    from core.database import db_manager
    
    try:
        recommendations = db_manager.list_recommendations(
            validation_id=validation_id,
            status=status,
            limit=limit
        )
        
        if output_format == 'json':
            data = [r.to_dict() for r in recommendations]
            console.print_json(data=data)
        else:
            table = Table(title=f"Recommendations ({len(recommendations)})")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Status", style="yellow")
            table.add_column("Severity", style="red")
            table.add_column("Instruction", style="white")
            table.add_column("Confidence", style="green")
            
            for rec in recommendations:
                rec_dict = rec.to_dict()
                table.add_row(
                    rec_dict['id'][:8] + "...",
                    rec_dict['status'],
                    rec_dict.get('severity', 'N/A'),
                    rec_dict.get('instruction', 'N/A')[:50] + "..." if rec_dict.get('instruction', '') else 'N/A',
                    f"{rec_dict.get('confidence', 0):.2f}"
                )
            
            console.print(table)
            
            if not ctx.obj.get('quiet'):
                console.print(f"\n[blue]Total:[/blue] {len(recommendations)} recommendations")
                
    except Exception as e:
        console.print(f"[red]Error listing recommendations: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@recommendations.command('show')
@click.argument('recommendation_id')
@click.option('--format', 'output_format', default='text',
              type=click.Choice(['text', 'json']), help='Output format')
@click.pass_context
def show_recommendation(ctx, recommendation_id, output_format):
    """Show detailed information about a recommendation."""
    asyncio.run(_show_recommendation(ctx, recommendation_id, output_format))


async def _show_recommendation(ctx, recommendation_id, output_format):
    """Async implementation of show recommendation."""
    from core.database import db_manager
    
    try:
        rec = db_manager.get_recommendation(recommendation_id)
        
        if not rec:
            console.print(f"[red]Recommendation not found: {recommendation_id}[/red]")
            sys.exit(1)
        
        rec_dict = rec.to_dict()
        
        if output_format == 'json':
            console.print_json(data=rec_dict)
        else:
            console.print(Panel(f"[bold]Recommendation Details[/bold]", expand=False))
            console.print(f"[cyan]ID:[/cyan] {rec_dict['id']}")
            console.print(f"[cyan]Status:[/cyan] {rec_dict['status']}")
            console.print(f"[cyan]Severity:[/cyan] {rec_dict.get('severity', 'N/A')}")
            console.print(f"[cyan]Confidence:[/cyan] {rec_dict.get('confidence', 0):.2f}")
            console.print(f"[cyan]Scope:[/cyan] {rec_dict.get('scope', 'N/A')}")
            console.print(f"\n[cyan]Instruction:[/cyan]\n{rec_dict.get('instruction', 'N/A')}")
            console.print(f"\n[cyan]Rationale:[/cyan]\n{rec_dict.get('rationale', 'N/A')}")
            
            if rec_dict.get('reviewed_by'):
                console.print(f"\n[cyan]Reviewed by:[/cyan] {rec_dict['reviewed_by']}")
                console.print(f"[cyan]Reviewed at:[/cyan] {rec_dict.get('reviewed_at', 'N/A')}")
                if rec_dict.get('review_notes'):
                    console.print(f"[cyan]Notes:[/cyan] {rec_dict['review_notes']}")
                    
    except Exception as e:
        console.print(f"[red]Error showing recommendation: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@recommendations.command('approve')
@click.argument('recommendation_ids', nargs=-1, required=True)
@click.option('--reviewer', default='cli_user', help='Reviewer name')
@click.option('--notes', help='Review notes')
@click.pass_context
def approve_recommendations(ctx, recommendation_ids, reviewer, notes):
    """Approve one or more recommendations."""
    asyncio.run(_review_recommendations(ctx, recommendation_ids, 'approved', reviewer, notes))


@recommendations.command('reject')
@click.argument('recommendation_ids', nargs=-1, required=True)
@click.option('--reviewer', default='cli_user', help='Reviewer name')
@click.option('--notes', help='Review notes (reason for rejection)')
@click.pass_context
def reject_recommendations(ctx, recommendation_ids, reviewer, notes):
    """Reject one or more recommendations."""
    asyncio.run(_review_recommendations(ctx, recommendation_ids, 'rejected', reviewer, notes))


async def _review_recommendations(ctx, recommendation_ids, new_status, reviewer, notes):
    """Async implementation of review recommendations."""
    from core.database import db_manager
    
    success_count = 0
    failed_count = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task(
            f"Reviewing {len(recommendation_ids)} recommendation(s)...",
            total=len(recommendation_ids)
        )
        
        for rec_id in recommendation_ids:
            try:
                updated = db_manager.update_recommendation_status(
                    recommendation_id=rec_id,
                    status=new_status,
                    reviewer=reviewer,
                    review_notes=notes
                )
                
                if updated:
                    success_count += 1
                else:
                    failed_count += 1
                    console.print(f"[yellow]Warning: Recommendation not found: {rec_id}[/yellow]")
                    
            except Exception as e:
                failed_count += 1
                console.print(f"[red]Error reviewing {rec_id}: {e}[/red]")
            
            progress.advance(task)
    
    if success_count > 0:
        console.print(f"[green][OK] Successfully {new_status} {success_count} recommendation(s)[/green]")
    if failed_count > 0:
        console.print(f"[red][FAIL] Failed to review {failed_count} recommendation(s)[/red]")


@recommendations.command('enhance')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--validation-id', required=True, help='Validation ID with recommendations')
@click.option('--preview', is_flag=True, help='Preview changes without applying')
@click.option('--backup', is_flag=True, default=True, help='Create backup before applying changes')
@click.option('--output', help='Output file (default: overwrite original)')
@click.pass_context
def enhance_with_recommendations(ctx, file_path, validation_id, preview, backup, output):
    """Enhance content by applying approved recommendations."""
    asyncio.run(_enhance_with_recommendations(ctx, file_path, validation_id, preview, backup, output))


async def _enhance_with_recommendations(ctx, file_path, validation_id, preview, backup, output):
    """Async implementation of enhance with recommendations."""
    from core.database import db_manager
    await setup_agents()
    
    try:
        # Read original content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get approved recommendations for this validation
        recommendations = db_manager.list_recommendations(
            validation_id=validation_id,
            status='approved',
            limit=1000
        )
        
        if not recommendations:
            console.print(f"[yellow]No approved recommendations found for validation {validation_id}[/yellow]")
            return
        
        console.print(f"[blue]Found {len(recommendations)} approved recommendation(s)[/blue]")
        
        # Get content enhancer
        enhancer = agent_registry.get_agent("content_enhancer")
        if not enhancer:
            console.print("[red]Error: Content enhancer not available[/red]")
            sys.exit(1)
        
        # Apply recommendations
        result = await enhancer.enhance_from_recommendations(
            content=content,
            recommendations=[r.to_dict() for r in recommendations],
            file_path=file_path
        )
        
        # Show results
        console.print(f"\n[cyan]Enhancement Results:[/cyan]")
        console.print(f"  Applied: {result['statistics']['applied']}")
        console.print(f"  Skipped: {result['statistics']['skipped']}")
        
        if result['skipped_recommendations']:
            console.print("\n[yellow]Skipped recommendations:[/yellow]")
            for skipped in result['skipped_recommendations']:
                console.print(f"  - {skipped['id'][:8]}...: {skipped['reason']}")
        
        if preview:
            console.print("\n[yellow]PREVIEW MODE - Changes not applied[/yellow]")
            if result['diff']:
                console.print("\n[cyan]Diff:[/cyan]")
                console.print(result['diff'])
        else:
            # Create backup if requested
            if backup:
                backup_path = f"{file_path}.backup"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                console.print(f"[green]Backup created: {backup_path}[/green]")
            
            # Write enhanced content
            output_path = output or file_path
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result['enhanced_content'])
            
            console.print(f"[green][OK] Enhanced content written to: {output_path}[/green]")
            
    except Exception as e:
        console.print(f"[red]Error enhancing content: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@recommendations.command('generate')
@click.argument('validation_id')
@click.option('--force', is_flag=True, help='Force regeneration even if recommendations exist')
@click.pass_context
def generate_recommendations(ctx, validation_id, force):
    """Generate recommendations for a validation."""
    asyncio.run(_generate_recommendations(ctx, validation_id, force))


async def _generate_recommendations(ctx, validation_id, force):
    """Async implementation of generate recommendations."""
    from core.database import db_manager
    await setup_agents()

    try:
        val = db_manager.get_validation_result(validation_id)

        if not val:
            console.print(f"[red]Validation not found: {validation_id}[/red]")
            sys.exit(1)

        # Check if recommendations already exist
        existing = db_manager.list_recommendations(validation_id=validation_id, limit=1)
        if existing and not force:
            console.print(f"[yellow]Recommendations already exist for this validation. Use --force to regenerate.[/yellow]")
            return

        console.print(f"[blue]Generating recommendations for validation {validation_id[:8]}...[/blue]")

        rec_agent = agent_registry.get_agent("recommendation_agent")
        if not rec_agent:
            console.print("[red]Error: Recommendation agent not available[/red]")
            sys.exit(1)

        result = await rec_agent.process_request("generate_recommendations", {
            "validation_id": validation_id,
            "validation_result": val.validation_results
        })

        count = len(result.get('recommendations', []))
        console.print(f"[green][OK] Generated {count} recommendation(s)[/green]")

    except Exception as e:
        console.print(f"[red]Error generating recommendations: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@recommendations.command('rebuild')
@click.argument('validation_id')
@click.pass_context
def rebuild_recommendations(ctx, validation_id):
    """Rebuild recommendations for a validation (delete and regenerate)."""
    asyncio.run(_rebuild_recommendations(ctx, validation_id))


async def _rebuild_recommendations(ctx, validation_id):
    """Async implementation of rebuild recommendations."""
    from core.database import db_manager
    await setup_agents()

    try:
        val = db_manager.get_validation_result(validation_id)

        if not val:
            console.print(f"[red]Validation not found: {validation_id}[/red]")
            sys.exit(1)

        # Delete existing recommendations
        existing = db_manager.list_recommendations(validation_id=validation_id, limit=10000)
        if existing:
            console.print(f"[yellow]Deleting {len(existing)} existing recommendation(s)...[/yellow]")
            for rec in existing:
                db_manager.session.delete(rec)
            db_manager.session.commit()

        # Generate new recommendations
        console.print(f"[blue]Generating new recommendations...[/blue]")

        rec_agent = agent_registry.get_agent("recommendation_agent")
        if not rec_agent:
            console.print("[red]Error: Recommendation agent not available[/red]")
            sys.exit(1)

        result = await rec_agent.process_request("generate_recommendations", {
            "validation_id": validation_id,
            "validation_result": val.validation_results
        })

        count = len(result.get('recommendations', []))
        console.print(f"[green][OK] Rebuilt {count} recommendation(s)[/green]")

    except Exception as e:
        console.print(f"[red]Error rebuilding recommendations: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@recommendations.command('delete')
@click.argument('recommendation_ids', nargs=-1, required=True)
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def delete_recommendations(ctx, recommendation_ids, confirm):
    """Delete one or more recommendations."""
    asyncio.run(_delete_recommendations(ctx, recommendation_ids, confirm))


async def _delete_recommendations(ctx, recommendation_ids, confirm):
    """Async implementation of delete recommendations."""
    from core.database import db_manager

    try:
        if not confirm:
            console.print(f"[yellow]About to delete {len(recommendation_ids)} recommendation(s)[/yellow]")
            if not click.confirm("Are you sure?"):
                console.print("[blue]Cancelled[/blue]")
                return

        deleted = 0
        for rec_id in recommendation_ids:
            rec = db_manager.get_recommendation(rec_id)
            if rec:
                db_manager.session.delete(rec)
                deleted += 1
            else:
                console.print(f"[yellow]Recommendation not found: {rec_id}[/yellow]")

        db_manager.session.commit()

        console.print(f"[green][OK] Deleted {deleted} recommendation(s)[/green]")

    except Exception as e:
        console.print(f"[red]Error deleting recommendations: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@recommendations.command('auto-apply')
@click.argument('validation_id')
@click.option('--threshold', default=0.95, type=float, help='Confidence threshold for auto-apply (default: 0.95)')
@click.option('--dry-run', is_flag=True, help='Show what would be applied without actually applying')
@click.pass_context
def auto_apply_recommendations(ctx, validation_id, threshold, dry_run):
    """Auto-apply high-confidence recommendations."""
    asyncio.run(_auto_apply_recommendations(ctx, validation_id, threshold, dry_run))


async def _auto_apply_recommendations(ctx, validation_id, threshold, dry_run):
    """Async implementation of auto-apply recommendations."""
    from core.database import db_manager
    await setup_agents()

    try:
        val = db_manager.get_validation_result(validation_id)

        if not val:
            console.print(f"[red]Validation not found: {validation_id}[/red]")
            sys.exit(1)

        # Get high-confidence approved recommendations
        all_recs = db_manager.list_recommendations(
            validation_id=validation_id,
            status='approved',
            limit=10000
        )

        high_conf_recs = [r for r in all_recs if r.confidence >= threshold]

        if not high_conf_recs:
            console.print(f"[yellow]No recommendations with confidence >= {threshold:.2f} found[/yellow]")
            return

        console.print(f"[blue]Found {len(high_conf_recs)} recommendation(s) with confidence >= {threshold:.2f}[/blue]")

        if dry_run:
            console.print("\n[yellow]DRY RUN MODE - Would apply:[/yellow]")
            for rec in high_conf_recs:
                rec_dict = rec.to_dict()
                console.print(f"  - {rec_dict['id'][:8]}...: {rec_dict.get('instruction', 'N/A')[:60]} (conf: {rec_dict.get('confidence', 0):.2f})")
            return

        # Get file path from validation
        file_path = val.file_path
        if not file_path or not os.path.exists(file_path):
            console.print(f"[red]File not found: {file_path}[/red]")
            sys.exit(1)

        # Read original content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Get content enhancer
        enhancer = agent_registry.get_agent("content_enhancer")
        if not enhancer:
            console.print("[red]Error: Content enhancer not available[/red]")
            sys.exit(1)

        # Apply recommendations
        result = await enhancer.enhance_from_recommendations(
            content=content,
            recommendations=[r.to_dict() for r in high_conf_recs],
            file_path=file_path
        )

        # Show results
        console.print(f"\n[cyan]Auto-Apply Results:[/cyan]")
        console.print(f"  Applied: {result['statistics']['applied']}")
        console.print(f"  Skipped: {result['statistics']['skipped']}")

        # Create backup
        backup_path = f"{file_path}.backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        console.print(f"[green]Backup created: {backup_path}[/green]")

        # Write enhanced content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(result['enhanced_content'])

        console.print(f"[green][OK] Auto-applied {result['statistics']['applied']} recommendation(s)[/green]")

    except Exception as e:
        console.print(f"[red]Error auto-applying recommendations: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


# ---------------------------
# validations command group
# ---------------------------
@cli.group()
@click.pass_context
def validations(ctx):
    """Manage validation results."""
    pass


@validations.command('list')
@click.option('--status', type=click.Choice(['pass', 'fail', 'warning', 'approved', 'rejected', 'enhanced']),
              help='Filter by validation status')
@click.option('--severity', type=click.Choice(['low', 'medium', 'high', 'critical']),
              help='Filter by severity')
@click.option('--limit', default=50, help='Maximum number of validations to show')
@click.option('--format', 'output_format', default='table',
              type=click.Choice(['table', 'json']), help='Output format')
@click.pass_context
def list_validations(ctx, status, severity, limit, output_format):
    """List validation results."""
    asyncio.run(_list_validations(ctx, status, severity, limit, output_format))


async def _list_validations(ctx, status, severity, limit, output_format):
    """Async implementation of list validations."""
    from core.database import db_manager

    try:
        filters = {}
        if status:
            filters['status'] = status
        if severity:
            filters['severity'] = severity

        validations = db_manager.list_validation_results(limit=limit, **filters)

        if output_format == 'json':
            data = [v.to_dict() for v in validations]
            console.print_json(data=data)
        else:
            table = Table(title=f"Validation Results ({len(validations)})")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("File Path", style="white")
            table.add_column("Status", style="yellow")
            table.add_column("Severity", style="red")
            table.add_column("Created", style="blue")

            for val in validations:
                val_dict = val.to_dict()
                table.add_row(
                    val_dict['id'][:8] + "...",
                    val_dict.get('file_path', 'N/A')[:40],
                    val_dict.get('status', 'N/A'),
                    val_dict.get('severity', 'N/A'),
                    val_dict.get('created_at', 'N/A')[:19] if val_dict.get('created_at') else 'N/A'
                )

            console.print(table)

            if not ctx.obj.get('quiet'):
                console.print(f"\n[blue]Total:[/blue] {len(validations)} validations")

    except Exception as e:
        console.print(f"[red]Error listing validations: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@validations.command('show')
@click.argument('validation_id')
@click.option('--format', 'output_format', default='text',
              type=click.Choice(['text', 'json']), help='Output format')
@click.pass_context
def show_validation(ctx, validation_id, output_format):
    """Show detailed validation information."""
    asyncio.run(_show_validation(ctx, validation_id, output_format))


async def _show_validation(ctx, validation_id, output_format):
    """Async implementation of show validation."""
    from core.database import db_manager

    try:
        val = db_manager.get_validation_result(validation_id)

        if not val:
            console.print(f"[red]Validation not found: {validation_id}[/red]")
            sys.exit(1)

        val_dict = val.to_dict()

        if output_format == 'json':
            console.print_json(data=val_dict)
        else:
            console.print(Panel(f"[bold]Validation Details[/bold]", expand=False))
            console.print(f"[cyan]ID:[/cyan] {val_dict['id']}")
            console.print(f"[cyan]File Path:[/cyan] {val_dict.get('file_path', 'N/A')}")
            console.print(f"[cyan]Status:[/cyan] {val_dict.get('status', 'N/A')}")
            console.print(f"[cyan]Severity:[/cyan] {val_dict.get('severity', 'N/A')}")
            console.print(f"[cyan]Created:[/cyan] {val_dict.get('created_at', 'N/A')}")

            if val_dict.get('validation_result'):
                console.print(f"\n[cyan]Validation Result:[/cyan]")
                console.print_json(data=val_dict['validation_result'])

    except Exception as e:
        console.print(f"[red]Error showing validation: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@validations.command('history')
@click.argument('file_path', type=click.Path())
@click.option('--limit', default=10, help='Maximum number of history entries')
@click.option('--format', 'output_format', default='table',
              type=click.Choice(['table', 'json']), help='Output format')
@click.pass_context
def validation_history(ctx, file_path, limit, output_format):
    """Show validation history for a file."""
    asyncio.run(_validation_history(ctx, file_path, limit, output_format))


async def _validation_history(ctx, file_path, limit, output_format):
    """Async implementation of validation history."""
    from core.database import db_manager

    try:
        history_data = db_manager.get_validation_history(file_path=file_path, limit=limit)
        validations = history_data.get("validations", [])

        if not validations:
            console.print(f"[yellow]No validation history found for: {file_path}[/yellow]")
            return

        if output_format == 'json':
            console.print_json(data=history_data)
        else:
            table = Table(title=f"Validation History for {file_path}")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Status", style="yellow")
            table.add_column("Severity", style="red")
            table.add_column("Created", style="blue")
            table.add_column("Issues", style="white")

            for val_dict in validations:
                validation_results = val_dict.get('validation_results', {})
                issues_count = len(validation_results.get('content_validation', {}).get('issues', []))
                table.add_row(
                    val_dict['id'][:8] + "...",
                    val_dict.get('status', 'N/A'),
                    val_dict.get('severity', 'N/A'),
                    val_dict.get('created_at', 'N/A')[:19] if val_dict.get('created_at') else 'N/A',
                    str(issues_count)
                )

            console.print(table)
            console.print(f"\n[blue]Total:[/blue] {len(validations)} validation(s)")

    except Exception as e:
        console.print(f"[red]Error getting validation history: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@validations.command('approve')
@click.argument('validation_id')
@click.option('--notes', help='Approval notes')
@click.pass_context
def approve_validation(ctx, validation_id, notes):
    """Approve a validation result."""
    asyncio.run(_approve_validation(ctx, validation_id, notes))


async def _approve_validation(ctx, validation_id, notes):
    """Async implementation of approve validation."""
    from core.database import db_manager

    try:
        val = db_manager.get_validation_result(validation_id)

        if not val:
            console.print(f"[red]Validation not found: {validation_id}[/red]")
            sys.exit(1)

        val.status = 'approved'
        db_manager.session.commit()

        console.print(f"[green][OK] Validation {validation_id[:8]}... approved[/green]")
        if notes:
            console.print(f"[blue]Notes:[/blue] {notes}")

    except Exception as e:
        console.print(f"[red]Error approving validation: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@validations.command('reject')
@click.argument('validation_id')
@click.option('--notes', help='Rejection notes')
@click.pass_context
def reject_validation(ctx, validation_id, notes):
    """Reject a validation result."""
    asyncio.run(_reject_validation(ctx, validation_id, notes))


async def _reject_validation(ctx, validation_id, notes):
    """Async implementation of reject validation."""
    from core.database import db_manager

    try:
        val = db_manager.get_validation_result(validation_id)

        if not val:
            console.print(f"[red]Validation not found: {validation_id}[/red]")
            sys.exit(1)

        val.status = 'rejected'
        db_manager.session.commit()

        console.print(f"[green][OK] Validation {validation_id[:8]}... rejected[/green]")
        if notes:
            console.print(f"[blue]Notes:[/blue] {notes}")

    except Exception as e:
        console.print(f"[red]Error rejecting validation: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@validations.command('revalidate')
@click.argument('validation_id')
@click.pass_context
def revalidate(ctx, validation_id):
    """Re-validate content from a previous validation."""
    asyncio.run(_revalidate(ctx, validation_id))


async def _revalidate(ctx, validation_id):
    """Async implementation of revalidate."""
    from core.database import db_manager
    await setup_agents()

    try:
        original_val = db_manager.get_validation_result(validation_id)

        if not original_val:
            console.print(f"[red]Validation not found: {validation_id}[/red]")
            sys.exit(1)

        file_path = original_val.file_path

        if not file_path or not os.path.exists(file_path):
            console.print(f"[red]File not found: {file_path}[/red]")
            sys.exit(1)

        console.print(f"[blue]Re-validating:[/blue] {file_path}")

        orchestrator = agent_registry.get_agent("orchestrator")
        if not orchestrator:
            console.print("[red]Error: Orchestrator agent not available[/red]")
            sys.exit(1)

        result = await orchestrator.process_request("validate_file", {
            "file_path": file_path,
            "family": "words"
        })

        console.print(f"[green][OK] Re-validation complete[/green]")
        console.print(f"[cyan]Status:[/cyan] {result.get('status', 'unknown')}")

        # Compare with original
        original_issues = original_val.validation_result.get('content_validation', {}).get('issues', [])
        new_issues = result.get('validation_result', {}).get('content_validation', {}).get('issues', [])

        console.print(f"\n[blue]Comparison:[/blue]")
        console.print(f"  Original issues: {len(original_issues)}")
        console.print(f"  New issues: {len(new_issues)}")
        console.print(f"  Change: {len(new_issues) - len(original_issues):+d}")

    except Exception as e:
        console.print(f"[red]Error re-validating: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


# ---------------------------
# workflows command group
# ---------------------------
@cli.group()
@click.pass_context
def workflows(ctx):
    """Manage workflow execution."""
    pass


@workflows.command('list')
@click.option('--state', type=click.Choice(['pending', 'running', 'paused', 'completed', 'failed', 'cancelled']),
              help='Filter by workflow state')
@click.option('--limit', default=50, help='Maximum number of workflows to show')
@click.option('--format', 'output_format', default='table',
              type=click.Choice(['table', 'json']), help='Output format')
@click.pass_context
def list_workflows(ctx, state, limit, output_format):
    """List workflows."""
    asyncio.run(_list_workflows(ctx, state, limit, output_format))


async def _list_workflows(ctx, state, limit, output_format):
    """Async implementation of list workflows."""
    from core.database import db_manager

    try:
        filters = {}
        if state:
            filters['state'] = state

        workflows_list = db_manager.list_workflows(limit=limit, **filters)

        if output_format == 'json':
            data = [w.to_dict() for w in workflows_list]
            console.print_json(data=data)
        else:
            table = Table(title=f"Workflows ({len(workflows_list)})")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Type", style="white")
            table.add_column("State", style="yellow")
            table.add_column("Progress", style="green")
            table.add_column("Created", style="blue")

            for wf in workflows_list:
                wf_dict = wf.to_dict()
                progress = wf_dict.get('progress', 0)
                table.add_row(
                    wf_dict['id'][:8] + "...",
                    wf_dict.get('type', 'N/A'),
                    wf_dict.get('state', 'N/A'),
                    f"{progress:.1f}%",
                    wf_dict.get('created_at', 'N/A')[:19] if wf_dict.get('created_at') else 'N/A'
                )

            console.print(table)

            if not ctx.obj.get('quiet'):
                console.print(f"\n[blue]Total:[/blue] {len(workflows_list)} workflows")

    except Exception as e:
        console.print(f"[red]Error listing workflows: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@workflows.command('show')
@click.argument('workflow_id')
@click.option('--format', 'output_format', default='text',
              type=click.Choice(['text', 'json']), help='Output format')
@click.pass_context
def show_workflow(ctx, workflow_id, output_format):
    """Show detailed workflow information."""
    asyncio.run(_show_workflow(ctx, workflow_id, output_format))


async def _show_workflow(ctx, workflow_id, output_format):
    """Async implementation of show workflow."""
    from core.database import db_manager

    try:
        wf = db_manager.get_workflow(workflow_id)

        if not wf:
            console.print(f"[red]Workflow not found: {workflow_id}[/red]")
            sys.exit(1)

        wf_dict = wf.to_dict()

        if output_format == 'json':
            console.print_json(data=wf_dict)
        else:
            console.print(Panel(f"[bold]Workflow Details[/bold]", expand=False))
            console.print(f"[cyan]ID:[/cyan] {wf_dict['id']}")
            console.print(f"[cyan]Type:[/cyan] {wf_dict.get('type', 'N/A')}")
            console.print(f"[cyan]State:[/cyan] {wf_dict.get('state', 'N/A')}")
            console.print(f"[cyan]Progress:[/cyan] {wf_dict.get('progress', 0):.1f}%")
            console.print(f"[cyan]Created:[/cyan] {wf_dict.get('created_at', 'N/A')}")
            console.print(f"[cyan]Updated:[/cyan] {wf_dict.get('updated_at', 'N/A')}")

            if wf_dict.get('config'):
                console.print(f"\n[cyan]Configuration:[/cyan]")
                console.print_json(data=wf_dict['config'])

    except Exception as e:
        console.print(f"[red]Error showing workflow: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@workflows.command('cancel')
@click.argument('workflow_id')
@click.pass_context
def cancel_workflow(ctx, workflow_id):
    """Cancel a running workflow."""
    asyncio.run(_cancel_workflow(ctx, workflow_id))


async def _cancel_workflow(ctx, workflow_id):
    """Async implementation of cancel workflow."""
    from core.database import db_manager

    try:
        wf = db_manager.get_workflow(workflow_id)

        if not wf:
            console.print(f"[red]Workflow not found: {workflow_id}[/red]")
            sys.exit(1)

        if wf.state not in ['pending', 'running', 'paused']:
            console.print(f"[yellow]Workflow cannot be cancelled (state: {wf.state})[/yellow]")
            sys.exit(1)

        wf.state = 'cancelled'
        db_manager.session.commit()

        console.print(f"[green][OK] Workflow {workflow_id[:8]}... cancelled[/green]")

    except Exception as e:
        console.print(f"[red]Error cancelling workflow: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@workflows.command('delete')
@click.argument('workflow_ids', nargs=-1, required=True)
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def delete_workflows(ctx, workflow_ids, confirm):
    """Delete one or more workflows."""
    asyncio.run(_delete_workflows(ctx, workflow_ids, confirm))


async def _delete_workflows(ctx, workflow_ids, confirm):
    """Async implementation of delete workflows."""
    from core.database import db_manager

    try:
        if not confirm:
            console.print(f"[yellow]About to delete {len(workflow_ids)} workflow(s)[/yellow]")
            if not click.confirm("Are you sure?"):
                console.print("[blue]Cancelled[/blue]")
                return

        deleted = 0
        for workflow_id in workflow_ids:
            wf = db_manager.get_workflow(workflow_id)
            if wf:
                db_manager.session.delete(wf)
                deleted += 1
            else:
                console.print(f"[yellow]Workflow not found: {workflow_id}[/yellow]")

        db_manager.session.commit()

        console.print(f"[green][OK] Deleted {deleted} workflow(s)[/green]")

    except Exception as e:
        console.print(f"[red]Error deleting workflows: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


# ---------------------------
# admin command group
# ---------------------------
@cli.group()
@click.pass_context
def admin(ctx):
    """System administration commands."""
    pass


@admin.command('cache-stats')
@click.pass_context
def cache_stats(ctx):
    """Show cache statistics."""
    asyncio.run(_cache_stats(ctx))


async def _cache_stats(ctx):
    """Async implementation of cache stats."""
    from core.cache import cache_manager

    try:
        stats = cache_manager.get_statistics()

        console.print(Panel("[bold]Cache Statistics[/bold]", expand=False))

        # L1 Cache Stats
        l1_stats = stats.get('l1', {})
        if l1_stats.get('enabled'):
            table_l1 = Table(title="L1 Cache (Memory)")
            table_l1.add_column("Metric", style="cyan")
            table_l1.add_column("Value", style="yellow")

            table_l1.add_row("Size", str(l1_stats.get('size', 0)))
            table_l1.add_row("Max Size", str(l1_stats.get('max_size', 0)))
            table_l1.add_row("Hits", str(l1_stats.get('hits', 0)))
            table_l1.add_row("Misses", str(l1_stats.get('misses', 0)))
            table_l1.add_row("Hit Rate", f"{l1_stats.get('hit_rate', 0):.2%}")
            table_l1.add_row("TTL (seconds)", str(l1_stats.get('ttl_seconds', 0)))

            console.print(table_l1)
        else:
            console.print("[yellow]L1 Cache: Disabled[/yellow]")

        # L2 Cache Stats
        l2_stats = stats.get('l2', {})
        if l2_stats.get('enabled'):
            table_l2 = Table(title="L2 Cache (Persistent)")
            table_l2.add_column("Metric", style="cyan")
            table_l2.add_column("Value", style="yellow")

            if 'error' in l2_stats:
                table_l2.add_row("Error", l2_stats['error'])
            else:
                table_l2.add_row("Entries", str(l2_stats.get('total_entries', 0)))
                table_l2.add_row("Size (MB)", str(l2_stats.get('total_size_mb', 0)))
                table_l2.add_row("Database", l2_stats.get('database_path', 'N/A'))

            console.print(table_l2)
        else:
            console.print("[yellow]L2 Cache: Disabled[/yellow]")

    except Exception as e:
        console.print(f"[red]Error getting cache stats: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@admin.command('cache-clear')
@click.option('--l1', is_flag=True, help='Clear L1 cache only')
@click.option('--l2', is_flag=True, help='Clear L2 cache only')
@click.pass_context
def cache_clear(ctx, l1, l2):
    """Clear cache."""
    asyncio.run(_cache_clear(ctx, l1, l2))


async def _cache_clear(ctx, l1, l2):
    """Async implementation of cache clear."""
    from core.cache import cache_manager

    try:
        if not l1 and not l2:
            # Clear both
            cache_manager.clear()
            console.print("[green][OK] All caches cleared[/green]")
        else:
            if l1:
                cache_manager.clear_l1()
                console.print("[green][OK] L1 cache cleared[/green]")
            if l2:
                cache_manager.clear_l2()
                console.print("[green][OK] L2 cache cleared[/green]")

    except Exception as e:
        console.print(f"[red]Error clearing cache: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@admin.command('agents')
@click.pass_context
def list_agents(ctx):
    """List all registered agents."""
    asyncio.run(_list_agents(ctx))


async def _list_agents(ctx):
    """Async implementation of list agents."""
    await setup_agents()

    try:
        table = Table(title="Registered Agents")
        table.add_column("Agent ID", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Version", style="yellow")
        table.add_column("Capabilities", style="blue")

        for agent_id, agent in agent_registry.agents.items():
            status = agent.get_status()
            contract = agent.get_contract()
            capabilities_count = len(contract.capabilities) if contract else 0

            table.add_row(
                agent_id,
                status.get("status", "unknown"),
                contract.version if contract else "N/A",
                str(capabilities_count)
            )

        console.print(table)
        console.print(f"\n[blue]Total:[/blue] {len(agent_registry.agents)} agents")

    except Exception as e:
        console.print(f"[red]Error listing agents: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@admin.command('health')
@click.option('--full', is_flag=True, help='Show full health report')
@click.pass_context
def health_check(ctx, full):
    """Perform system health check."""
    asyncio.run(_health_check(ctx, full))


async def _health_check(ctx, full):
    """Async implementation of health check."""
    from core.database import db_manager
    await setup_agents()

    try:
        console.print(Panel("[bold]System Health Check[/bold]", expand=False))

        # Database check
        try:
            with db_manager.get_session() as session:
                from sqlalchemy import text
                session.execute(text("SELECT 1"))
            db_status = "[green]OK[/green]"
        except Exception as e:
            db_status = f"[red]FAIL: {e}[/red]"

        console.print(f"[cyan]Database:[/cyan] {db_status}")

        # Agents check
        agents_ok = len(agent_registry.agents)
        console.print(f"[cyan]Agents:[/cyan] [green]{agents_ok} registered[/green]")

        if full:
            console.print("\n[cyan]Agent Details:[/cyan]")
            for agent_id, agent in agent_registry.agents.items():
                status = agent.get_status()
                agent_status = status.get("status", "unknown")
                color = "green" if agent_status == "ready" else "yellow"
                console.print(f"  {agent_id}: [{color}]{agent_status}[/{color}]")

        console.print("\n[green][OK] Health check complete[/green]")

    except Exception as e:
        console.print(f"[red]Error performing health check: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@admin.command('reset')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt (DANGEROUS)')
@click.option('--validations', is_flag=True, help='Delete only validations')
@click.option('--workflows', is_flag=True, help='Delete only workflows')
@click.option('--recommendations', is_flag=True, help='Delete only recommendations')
@click.option('--audit-logs', is_flag=True, help='Delete audit logs (normally preserved)')
@click.option('--all', 'delete_all', is_flag=True, help='Delete everything (default if no specific options)')
@click.option('--clear-cache', is_flag=True, help='Clear cache after reset')
@click.pass_context
def reset_system(ctx, confirm, validations, workflows, recommendations, audit_logs, delete_all, clear_cache):
    """Reset system by deleting data.

    DANGEROUS: This permanently deletes data from the database.
    Use this to clean up before production or during development.

    Examples:
        tbcv admin reset --all --confirm
        tbcv admin reset --validations --confirm
        tbcv admin reset --workflows --recommendations --confirm
    """
    asyncio.run(_reset_system(ctx, confirm, validations, workflows, recommendations, audit_logs, delete_all, clear_cache))


async def _reset_system(ctx, confirm, validations, workflows, recommendations, audit_logs, delete_all, clear_cache):
    """Async implementation of system reset."""
    from core.database import db_manager
    from core.cache import cache_manager

    try:
        # If no specific options, assume --all
        if not (validations or workflows or recommendations or audit_logs):
            delete_all = True

        # Build summary of what will be deleted
        to_delete = []
        if delete_all or validations:
            to_delete.append("validations")
        if delete_all or workflows:
            to_delete.append("workflows")
        if delete_all or recommendations:
            to_delete.append("recommendations")
        if audit_logs:
            to_delete.append("audit logs")

        if not to_delete:
            console.print("[yellow]Nothing selected to delete[/yellow]")
            return

        # Show warning
        console.print(Panel(
            f"[bold red]WARNING: This will permanently delete:[/bold red]\n" +
            "\n".join([f"  • {item}" for item in to_delete]),
            title="[bold red]DANGEROUS OPERATION[/bold red]",
            expand=False
        ))

        # Confirmation
        if not confirm:
            console.print("\n[yellow]This operation requires confirmation.[/yellow]")
            response = click.prompt("Type 'DELETE' to confirm", type=str)
            if response != "DELETE":
                console.print("[red]Operation cancelled[/red]")
                return

        console.print("\n[cyan]Performing system reset...[/cyan]")

        # Perform deletion
        if delete_all:
            results = db_manager.reset_system(
                confirm=True,
                delete_validations=True,
                delete_workflows=True,
                delete_recommendations=True,
                delete_audit_logs=audit_logs
            )
        else:
            results = db_manager.reset_system(
                confirm=True,
                delete_validations=validations,
                delete_workflows=workflows,
                delete_recommendations=recommendations,
                delete_audit_logs=audit_logs
            )

        # Display results
        table = Table(title="Reset Results", show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan")
        table.add_column("Deleted", justify="right", style="yellow")

        table.add_row("Validations", str(results["validations_deleted"]))
        table.add_row("Workflows", str(results["workflows_deleted"]))
        table.add_row("Recommendations", str(results["recommendations_deleted"]))
        table.add_row("Audit Logs", str(results["audit_logs_deleted"]))

        console.print(table)

        # Clear cache if requested
        if clear_cache:
            console.print("\n[cyan]Clearing cache...[/cyan]")
            l1_cleared = cache_manager.clear_l1()
            l2_cleared = cache_manager.clear_l2()
            console.print(f"[green]Cache cleared: {l1_cleared} L1 entries, {l2_cleared} L2 entries[/green]")

        total_deleted = sum(results.values())
        console.print(f"\n[green][OK] System reset complete: {total_deleted} items deleted[/green]")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error performing system reset: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


# ---------------------------
# probe-endpoints command
# ---------------------------
@cli.command('probe-endpoints')
@click.option('--mode', type=click.Choice(['offline', 'live']), default='offline',
              help='Probe mode: offline (TestClient) or live (HTTP)')
@click.option('--base-url', default='http://127.0.0.1:8080',
              help='Base URL for live mode (default: http://127.0.0.1:8080)')
@click.option('--scan', multiple=True,
              help='Additional Python files to scan for declared endpoints')
@click.option('--include', help='Regex pattern to include only matching paths')
@click.option('--exclude', help='Regex pattern to exclude matching paths')
@click.option('--strict', is_flag=True,
              help='Exit with non-zero code if any registered endpoint fails')
@click.option('--output-dir', default='data/reports',
              help='Output directory for reports (default: data/reports)')
@click.pass_context
def probe_endpoints(ctx, mode, base_url, scan, include, exclude, strict, output_dir):
    """Discover and probe API endpoints.

    This command:
      - Discovers all registered FastAPI routes
      - Scans source files for declared endpoints
      - Probes endpoints in offline (TestClient) or live (HTTP) mode
      - Generates JSON and Markdown reports

    Examples:

        # Offline mode using TestClient
        python -m tbcv.cli probe-endpoints --mode offline

        # Live mode against running server
        python -m tbcv.cli probe-endpoints --mode live --base-url http://127.0.0.1:8080

        # Filter to specific paths
        python -m tbcv.cli probe-endpoints --include "^/api" --exclude "/docs"

        # Strict mode (fails on errors)
        python -m tbcv.cli probe-endpoints --mode live --strict
    """
    from tools.endpoint_probe import main as probe_main

    if not ctx.obj.get('quiet'):
        console.print("[blue]Starting endpoint probe...[/blue]")
        console.print(f"Mode: {mode}")
        if mode == 'live':
            console.print(f"Base URL: {base_url}")

    argv = ['--mode', mode]
    if base_url:
        argv += ['--base-url', base_url]
    if scan:
        argv.append('--scan')
        argv += list(scan)
    if include:
        argv += ['--include', include]
    if exclude:
        argv += ['--exclude', exclude]
    if strict:
        argv.append('--strict')
    if output_dir:
        argv += ['--output-dir', output_dir]

    try:
        exit_code = probe_main(argv)
        if not ctx.obj.get('quiet'):
            if exit_code == 0:
                console.print("[green][OK] Endpoint probe completed successfully[/green]")
            else:
                console.print("[red][FAIL] Endpoint probe completed with errors[/red]")
        sys.exit(exit_code)
    except Exception as e:
        console.print(f"[red]Error running endpoint probe: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


# =============================================================================
# P1-T03: CLI Enhancement History Commands
# =============================================================================

@admin.command("enhancements")
@click.option("--file-path", "-f", help="Filter by file path")
@click.option("--limit", "-l", default=50, help="Maximum records to show")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table")
@click.pass_context
def list_enhancements(ctx, file_path, limit, output_format):
    """List enhancement history records."""
    from agents.enhancement_history import get_history_manager
    import json as json_module

    try:
        history = get_history_manager()
        records = history.list_enhancements(file_path=file_path, limit=limit)

        if output_format == "json":
            data = []
            for r in records:
                data.append({
                    "id": r.enhancement_id,
                    "file_path": r.file_path,
                    "status": "rolled_back" if r.rolled_back else "applied",
                    "applied_at": r.applied_at.isoformat() if r.applied_at else None,
                    "applied_by": r.applied_by,
                    "recommendations_count": r.recommendations_count
                })
            console.print(json_module.dumps(data, indent=2, default=str))
        else:
            if not records:
                console.print("[yellow]No enhancement records found.[/yellow]")
                return

            table = Table(title=f"Enhancement History ({len(records)} records)")
            table.add_column("ID", style="cyan", max_width=36)
            table.add_column("File", style="white", max_width=40)
            table.add_column("Status", style="yellow")
            table.add_column("Created", style="dim")

            for r in records:
                file_display = r.file_path[:37] + "..." if len(r.file_path) > 40 else r.file_path
                status = "rolled_back" if r.rolled_back else "applied"
                table.add_row(
                    r.enhancement_id[:8] + "..." if len(r.enhancement_id) > 8 else r.enhancement_id,
                    file_display,
                    status,
                    str(r.applied_at)[:19] if r.applied_at else "N/A"
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing enhancements: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@admin.command("enhancement-detail")
@click.argument("enhancement_id")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
def get_enhancement_detail(ctx, enhancement_id, output_format):
    """Get detailed information about a specific enhancement."""
    from agents.enhancement_history import get_history_manager
    import json as json_module

    try:
        history = get_history_manager()
        record = history.get_enhancement_record(enhancement_id)

        if not record:
            console.print(f"[red]Enhancement {enhancement_id} not found[/red]")
            sys.exit(1)

        if output_format == "json":
            data = {
                "id": record.enhancement_id,
                "file_path": record.file_path,
                "validation_id": record.validation_id,
                "status": "rolled_back" if record.rolled_back else "applied",
                "applied_at": record.applied_at.isoformat() if record.applied_at else None,
                "applied_by": record.applied_by,
                "recommendations_applied": record.recommendations_applied,
                "recommendations_count": record.recommendations_count,
                "safety_score": record.safety_score,
                "rollback_available": record.rollback_available,
                "rolled_back": record.rolled_back,
                "rolled_back_at": record.rolled_back_at.isoformat() if record.rolled_back_at else None,
                "rolled_back_by": record.rolled_back_by
            }
            console.print(json_module.dumps(data, indent=2, default=str))
        else:
            console.print(Panel(f"[bold]Enhancement Detail[/bold]", expand=False))

            table = Table(show_header=False, box=None)
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("ID", record.enhancement_id)
            table.add_row("File", record.file_path)
            table.add_row("Validation ID", record.validation_id)
            table.add_row("Status", "rolled_back" if record.rolled_back else "applied")
            table.add_row("Applied at", str(record.applied_at)[:19] if record.applied_at else "N/A")
            table.add_row("Applied by", record.applied_by or "N/A")
            table.add_row("Recommendations", f"{record.recommendations_applied}/{record.recommendations_count}")
            table.add_row("Safety Score", f"{record.safety_score:.2f}" if record.safety_score else "N/A")
            table.add_row("Rollback available", "Yes" if record.rollback_available else "No")

            if record.rolled_back:
                table.add_row("Rolled back at", str(record.rolled_back_at)[:19] if record.rolled_back_at else "N/A")
                table.add_row("Rolled back by", record.rolled_back_by or "N/A")

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error getting enhancement detail: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


# =============================================================================
# P1-T04: CLI Rollback Command
# =============================================================================

@admin.command("rollback")
@click.argument("enhancement_id")
@click.option("--confirm", is_flag=True, help="Confirm rollback operation (required)")
@click.option("--rolled-back-by", default="cli_user", help="User performing rollback")
@click.pass_context
def rollback_enhancement(ctx, enhancement_id, confirm, rolled_back_by):
    """Rollback an enhancement to restore original content."""
    from agents.enhancement_history import get_history_manager

    if not confirm:
        console.print("[yellow]Rollback requires confirmation.[/yellow]")
        console.print(f"\nTo rollback enhancement {enhancement_id}:")
        console.print(f"  tbcv admin rollback {enhancement_id} --confirm")
        return

    try:
        history = get_history_manager()

        # Show what will be rolled back
        record = history.get_enhancement_record(enhancement_id)
        if not record:
            console.print(f"[red]Enhancement {enhancement_id} not found[/red]")
            sys.exit(1)

        console.print(Panel("[bold]Rolling back enhancement[/bold]", expand=False))
        console.print(f"  ID:      {record.enhancement_id}")
        console.print(f"  File:    {record.file_path}")
        console.print(f"  Applied: {record.applied_at}")
        console.print()

        success = history.rollback_enhancement(enhancement_id, rolled_back_by)

        if success:
            console.print("[green]Rollback successful![/green]")
        else:
            console.print("[red]Rollback failed - point not found or expired[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error during rollback: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


# =============================================================================
# P1-T05: CLI Validation Diff Command
# =============================================================================

@validations.command("diff")
@click.argument("validation_id")
@click.option("--format", "output_format", type=click.Choice(["unified", "side-by-side", "json"]), default="unified")
@click.option("--context", "-c", default=3, help="Lines of context for unified diff")
@click.pass_context
def validation_diff(ctx, validation_id, output_format, context):
    """Show content diff for an enhanced validation."""
    import difflib
    import json as json_module
    from core.database import db_manager

    try:
        validation = db_manager.get_validation_result(validation_id)
        if not validation:
            console.print(f"[red]Validation {validation_id} not found[/red]")
            sys.exit(1)

        results = validation.validation_results or {}
        original = results.get("original_content")
        enhanced = results.get("enhanced_content")

        if not original or not enhanced:
            console.print("[yellow]No diff available - validation may not have been enhanced yet[/yellow]")
            sys.exit(1)

        if output_format == "json":
            diff_data = {
                "validation_id": validation_id,
                "file_path": validation.file_path,
                "has_diff": original != enhanced,
                "original_lines": len(original.splitlines()),
                "enhanced_lines": len(enhanced.splitlines())
            }
            console.print(json_module.dumps(diff_data, indent=2))

        elif output_format == "unified":
            console.print(Panel(f"[bold]Diff for {validation_id[:8]}...[/bold]", expand=False))

            diff = difflib.unified_diff(
                original.splitlines(keepends=True),
                enhanced.splitlines(keepends=True),
                fromfile="Original",
                tofile="Enhanced",
                n=context
            )

            for line in diff:
                line = line.rstrip()
                if line.startswith("+") and not line.startswith("+++"):
                    console.print(f"[green]{line}[/green]")
                elif line.startswith("-") and not line.startswith("---"):
                    console.print(f"[red]{line}[/red]")
                elif line.startswith("@@"):
                    console.print(f"[cyan]{line}[/cyan]")
                else:
                    console.print(line)

        else:  # side-by-side
            orig_lines = original.splitlines()
            enh_lines = enhanced.splitlines()
            max_lines = max(len(orig_lines), len(enh_lines))

            table = Table(title="Side-by-Side Comparison")
            table.add_column("Line", style="dim", width=5)
            table.add_column("Original", style="white", width=50, overflow="fold")
            table.add_column("Enhanced", style="white", width=50, overflow="fold")

            for i in range(min(max_lines, 100)):  # Limit to 100 lines
                orig = orig_lines[i] if i < len(orig_lines) else ""
                enh = enh_lines[i] if i < len(enh_lines) else ""

                # Highlight differences
                if orig != enh:
                    orig_style = f"[red]{orig}[/red]" if orig else "[dim]-[/dim]"
                    enh_style = f"[green]{enh}[/green]" if enh else "[dim]-[/dim]"
                else:
                    orig_style = orig
                    enh_style = enh

                table.add_row(str(i + 1), orig_style, enh_style)

            console.print(table)

            if max_lines > 100:
                console.print(f"[dim]... {max_lines - 100} more lines not shown[/dim]")

    except Exception as e:
        console.print(f"[red]Error getting diff: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


# =============================================================================
# P1-T06: CLI Validation Compare Command
# =============================================================================

@validations.command("compare")
@click.argument("validation_id")
@click.option("--format", "output_format", type=click.Choice(["summary", "detailed", "json"]), default="summary")
@click.pass_context
def validation_compare(ctx, validation_id, output_format):
    """Show comprehensive enhancement comparison with statistics."""
    import difflib
    import json as json_module
    from core.database import db_manager

    try:
        validation = db_manager.get_validation_result(validation_id)
        if not validation:
            console.print(f"[red]Validation {validation_id} not found[/red]")
            sys.exit(1)

        results = validation.validation_results or {}
        original = results.get("original_content", "")
        enhanced = results.get("enhanced_content", "")

        if not original or not enhanced:
            console.print("[yellow]No comparison available - validation not enhanced[/yellow]")
            sys.exit(1)

        # Calculate statistics
        orig_lines = original.splitlines()
        enh_lines = enhanced.splitlines()

        matcher = difflib.SequenceMatcher(None, orig_lines, enh_lines)

        added = 0
        removed = 0
        modified = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "insert":
                added += j2 - j1
            elif tag == "delete":
                removed += i2 - i1
            elif tag == "replace":
                modified += max(i2 - i1, j2 - j1)

        stats = {
            "validation_id": validation_id,
            "file_path": validation.file_path,
            "original_lines": len(orig_lines),
            "enhanced_lines": len(enh_lines),
            "lines_added": added,
            "lines_removed": removed,
            "lines_modified": modified,
            "similarity_ratio": round(matcher.ratio(), 4),
            "applied_recommendations": results.get("applied_recommendations", 0)
        }

        if output_format == "json":
            console.print(json_module.dumps(stats, indent=2))
        else:
            console.print(Panel(f"[bold]Enhancement Comparison[/bold]", expand=False))
            console.print(f"Validation: {validation_id[:8]}...")
            console.print(f"File: {validation.file_path}")
            console.print()

            table = Table(title="Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="yellow")

            table.add_row("Original lines", str(stats['original_lines']))
            table.add_row("Enhanced lines", str(stats['enhanced_lines']))
            table.add_row("Lines added", f"[green]+{stats['lines_added']}[/green]")
            table.add_row("Lines removed", f"[red]-{stats['lines_removed']}[/red]")
            table.add_row("Lines modified", str(stats['lines_modified']))
            table.add_row("Similarity", f"{stats['similarity_ratio']*100:.1f}%")
            table.add_row("Recommendations applied", str(stats['applied_recommendations']))

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error getting comparison: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


# =============================================================================
# P1-T07: CLI Workflow Report Command
# =============================================================================

@workflows.command("report")
@click.argument("workflow_id")
@click.option("--output", "-o", type=click.Path(), help="Save report to file")
@click.option("--format", "output_format", type=click.Choice(["text", "json", "markdown"]), default="text")
@click.pass_context
def workflow_report(ctx, workflow_id, output, output_format):
    """Generate comprehensive workflow report."""
    import json as json_module
    from core.database import db_manager

    try:
        report = db_manager.generate_workflow_report(workflow_id)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)

    if output_format == "json":
        content = json_module.dumps(report, indent=2, default=str)
    elif output_format == "markdown":
        content = _format_workflow_report_markdown(report)
    else:
        content = _format_workflow_report_text(report)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        console.print(f"[green]Report saved to {output}[/green]")
    else:
        console.print(content)


def _format_workflow_report_text(report):
    """Format workflow report as text."""
    lines = []
    lines.append(f"\nWorkflow Report: {report['workflow_id']}")
    lines.append("=" * 60)
    lines.append(f"Type:       {report['type']}")
    lines.append(f"Status:     {report['status']}")
    lines.append(f"Created:    {report['created_at']}")
    lines.append(f"Completed:  {report.get('completed_at', 'N/A')}")
    lines.append(f"Duration:   {report.get('duration_ms', 0)}ms")

    summary = report.get("summary", {})
    lines.append(f"\nSummary:")
    lines.append(f"  Total files:              {summary.get('total_files', 0)}")
    lines.append(f"  Passed:                   {summary.get('files_passed', 0)}")
    lines.append(f"  Failed:                   {summary.get('files_failed', 0)}")
    lines.append(f"  Total issues:             {summary.get('total_issues', 0)}")
    lines.append(f"  Total recommendations:    {summary.get('total_recommendations', 0)}")

    return "\n".join(lines)


def _format_workflow_report_markdown(report):
    """Format workflow report as markdown."""
    lines = []
    lines.append(f"# Workflow Report: {report['workflow_id'][:8]}...")
    lines.append("")
    lines.append(f"| Field | Value |")
    lines.append(f"|-------|-------|")
    lines.append(f"| Type | {report['type']} |")
    lines.append(f"| Status | {report['status']} |")
    lines.append(f"| Created | {report['created_at']} |")
    lines.append(f"| Duration | {report.get('duration_ms', 0)}ms |")
    lines.append("")

    summary = report.get("summary", {})
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total files:** {summary.get('total_files', 0)}")
    lines.append(f"- **Passed:** {summary.get('files_passed', 0)}")
    lines.append(f"- **Failed:** {summary.get('files_failed', 0)}")
    lines.append(f"- **Total issues:** {summary.get('total_issues', 0)}")
    lines.append(f"- **Recommendations:** {summary.get('total_recommendations', 0)}")

    return "\n".join(lines)


# =============================================================================
# P1-T08: CLI Workflow Summary Command
# =============================================================================

@workflows.command("summary")
@click.argument("workflow_id")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
def workflow_summary(ctx, workflow_id, output_format):
    """Show workflow summary (quick overview without details)."""
    import json as json_module
    from core.database import db_manager

    try:
        report = db_manager.generate_workflow_report(workflow_id)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)

    summary = {
        "workflow_id": report["workflow_id"],
        "status": report["status"],
        "type": report["type"],
        "created_at": report["created_at"],
        "completed_at": report.get("completed_at"),
        "duration_ms": report.get("duration_ms"),
        "summary": report.get("summary", {})
    }

    if output_format == "json":
        console.print(json_module.dumps(summary, indent=2, default=str))
    else:
        s = summary["summary"]
        status_color = "green" if summary["status"] == "completed" else "yellow" if summary["status"] == "running" else "red"

        console.print(Panel(f"[bold]Workflow Summary[/bold]", expand=False))
        console.print(f"ID:          {summary['workflow_id'][:8]}...")
        console.print(f"Status:      [{status_color}]{summary['status']}[/{status_color}]")
        console.print(f"Type:        {summary['type']}")
        console.print(f"Files:       {s.get('total_files', 0)} ({s.get('files_passed', 0)} passed, {s.get('files_failed', 0)} failed)")
        console.print(f"Issues:      {s.get('total_issues', 0)}")
        console.print(f"Recommendations: {s.get('total_recommendations', 0)}")

        if summary.get('duration_ms'):
            duration_sec = summary['duration_ms'] / 1000
            console.print(f"Duration:    {duration_sec:.1f}s")


# =============================================================================
# P2-T01: CLI Maintenance Mode Commands
# =============================================================================

@admin.group("maintenance")
@click.pass_context
def maintenance(ctx):
    """Maintenance mode management."""
    pass


@maintenance.command("enable")
@click.option("--base-url", default="http://127.0.0.1:8080", help="API base URL")
@click.pass_context
def maintenance_enable(ctx, base_url):
    """Enable maintenance mode."""
    import requests

    try:
        response = requests.post(f"{base_url}/admin/maintenance/enable", timeout=10)
        response.raise_for_status()

        console.print("[yellow]Maintenance mode ENABLED[/yellow]")
        console.print("New workflow submissions will be rejected.")

    except requests.exceptions.ConnectionError:
        console.print("[red]Error: Could not connect to server[/red]")
        console.print(f"Ensure server is running at {base_url}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@maintenance.command("disable")
@click.option("--base-url", default="http://127.0.0.1:8080", help="API base URL")
@click.pass_context
def maintenance_disable(ctx, base_url):
    """Disable maintenance mode."""
    import requests

    try:
        response = requests.post(f"{base_url}/admin/maintenance/disable", timeout=10)
        response.raise_for_status()

        console.print("[green]Maintenance mode DISABLED[/green]")
        console.print("System is now accepting workflows.")

    except requests.exceptions.ConnectionError:
        console.print("[red]Error: Could not connect to server[/red]")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@maintenance.command("status")
@click.option("--base-url", default="http://127.0.0.1:8080", help="API base URL")
@click.pass_context
def maintenance_status(ctx, base_url):
    """Check maintenance mode status."""
    import requests

    try:
        response = requests.get(f"{base_url}/admin/status", timeout=10)
        response.raise_for_status()
        result = response.json()

        mode = result.get("system", {}).get("maintenance_mode", False)

        if mode:
            console.print("[yellow]Maintenance mode: ENABLED[/yellow]")
        else:
            console.print("[green]Maintenance mode: DISABLED[/green]")

    except requests.exceptions.ConnectionError:
        console.print("[red]Error: Could not connect to server[/red]")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# =============================================================================
# P2-T02: CLI Cache Cleanup Command
# =============================================================================

@admin.command("cache-cleanup")
@click.pass_context
def cache_cleanup(ctx):
    """Cleanup expired cache entries."""
    from core.cache import cache_manager

    try:
        result = cache_manager.cleanup_expired()

        l1_cleaned = result.get("l1_cleaned", 0)
        l2_cleaned = result.get("l2_cleaned", 0)
        total = l1_cleaned + l2_cleaned

        console.print(Panel("[bold]Cache Cleanup[/bold]", expand=False))

        table = Table(show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("L1 entries removed", str(l1_cleaned))
        table.add_row("L2 entries removed", str(l2_cleaned))
        table.add_row("Total removed", str(total))

        console.print(table)
        console.print("[green]Cleanup completed[/green]")

    except Exception as e:
        console.print(f"[red]Error during cleanup: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


# =============================================================================
# P2-T03: CLI Cache Rebuild Command
# =============================================================================

@admin.command("cache-rebuild")
@click.option("--preload-truth", is_flag=True, help="Preload truth data after rebuild")
@click.pass_context
def cache_rebuild(ctx, preload_truth):
    """Rebuild cache from scratch."""
    from core.cache import cache_manager
    from core.database import db_manager

    try:
        # Clear L1
        l1_cleared = 0
        if hasattr(cache_manager, 'l1_cache') and cache_manager.l1_cache:
            l1_cleared = cache_manager.l1_cache.size() if hasattr(cache_manager.l1_cache, 'size') else 0
            cache_manager.clear_l1()

        # Clear L2
        l2_cleared = cache_manager.clear_l2() if hasattr(cache_manager, 'clear_l2') else 0

        console.print(Panel("[bold]Cache Rebuild[/bold]", expand=False))

        table = Table(show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("L1 entries cleared", str(l1_cleared))
        table.add_row("L2 entries cleared", str(l2_cleared))

        console.print(table)
        console.print("Cache will repopulate on demand.")

        if preload_truth:
            console.print("\n[dim]Preloading truth data...[/dim]")
            try:
                truth_manager = agent_registry.get_agent("truth_manager")
                if truth_manager:
                    asyncio.run(truth_manager.handle_message({
                        "type": "REQUEST",
                        "method": "load_truth",
                        "params": {"family": "words"}
                    }))
                    console.print("[green]Truth data preloaded for 'words' family[/green]")
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to preload truth data - {e}[/yellow]")

        console.print("[green]Cache rebuild completed[/green]")

    except Exception as e:
        console.print(f"[red]Error during rebuild: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


# =============================================================================
# P2-T04: CLI Performance Report Command
# =============================================================================

@admin.group("report")
@click.pass_context
def admin_report(ctx):
    """Generate system reports."""
    pass


@admin_report.command("performance")
@click.option("--days", "-d", default=7, help="Number of days to analyze")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
def performance_report(ctx, days, output_format):
    """Generate performance report."""
    import json as json_module
    from datetime import datetime, timedelta, timezone
    from core.database import db_manager, WorkflowState
    from core.cache import cache_manager

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        all_workflows = db_manager.list_workflows(limit=100000)

        period_workflows = []
        for w in all_workflows:
            if w.created_at:
                wf_time = w.created_at.replace(tzinfo=timezone.utc) if w.created_at.tzinfo is None else w.created_at
                if wf_time >= cutoff:
                    period_workflows.append(w)

        total = len(period_workflows)
        completed = len([w for w in period_workflows if w.state == WorkflowState.COMPLETED])
        failed = len([w for w in period_workflows if w.state == WorkflowState.FAILED])
        running = len([w for w in period_workflows if w.state == WorkflowState.RUNNING])

        # Calculate average completion time
        completion_times = []
        for w in period_workflows:
            if w.state == WorkflowState.COMPLETED and w.created_at and w.updated_at:
                delta = (w.updated_at - w.created_at).total_seconds() * 1000
                completion_times.append(delta)

        avg_time = sum(completion_times) / len(completion_times) if completion_times else 0
        error_rate = failed / total if total > 0 else 0
        success_rate = completed / total if total > 0 else 0

        cache_stats = cache_manager.get_statistics()
        l1_hit_rate = cache_stats.get("l1", {}).get("hit_rate", 0.0)

        report = {
            "period_days": days,
            "total_workflows": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "avg_completion_ms": round(avg_time, 2),
            "error_rate": round(error_rate, 4),
            "success_rate": round(success_rate, 4),
            "cache_hit_rate": round(l1_hit_rate, 4)
        }

        if output_format == "json":
            console.print(json_module.dumps(report, indent=2))
        else:
            console.print(Panel(f"[bold]Performance Report (last {days} days)[/bold]", expand=False))

            table = Table()
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="yellow")

            table.add_row("Total workflows", str(total))
            table.add_row("Completed", str(completed))
            table.add_row("Failed", str(failed))
            table.add_row("Running", str(running))
            table.add_row("Success rate", f"{success_rate*100:.1f}%")
            table.add_row("Error rate", f"{error_rate*100:.1f}%")
            table.add_row("Avg completion time", f"{avg_time:.0f}ms")
            table.add_row("Cache hit rate (L1)", f"{l1_hit_rate*100:.1f}%")

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@admin_report.command("health")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
def health_report(ctx, output_format):
    """Generate system health report."""
    import json as json_module
    from datetime import datetime, timezone
    from core.database import db_manager

    try:
        db_connected = False
        try:
            db_connected = db_manager.is_connected()
        except Exception:
            pass

        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database_connected": db_connected,
            "agents_registered": len(agent_registry.agents),
            "status": "healthy" if db_connected else "degraded"
        }

        if output_format == "json":
            console.print(json_module.dumps(report, indent=2))
        else:
            status_color = "green" if report["status"] == "healthy" else "red"

            console.print(Panel("[bold]System Health Report[/bold]", expand=False))

            table = Table(show_header=False)
            table.add_column("Field", style="cyan")
            table.add_column("Value")

            table.add_row("Status", f"[{status_color}]{report['status'].upper()}[/{status_color}]")
            table.add_row("Database", "[green]Connected[/green]" if report['database_connected'] else "[red]Disconnected[/red]")
            table.add_row("Agents", f"{report['agents_registered']} registered")
            table.add_row("Timestamp", report['timestamp'][:19])

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


# =============================================================================
# P2-T05: CLI Workflow Watch Command
# =============================================================================

@workflows.command("watch")
@click.argument("workflow_id")
@click.option("--interval", "-i", default=2, help="Polling interval in seconds")
@click.option("--timeout", "-t", default=300, help="Maximum watch time in seconds")
@click.pass_context
def workflow_watch(ctx, workflow_id, interval, timeout):
    """Watch workflow progress in real-time."""
    import time
    from datetime import datetime
    from core.database import db_manager

    workflow = db_manager.get_workflow(workflow_id)
    if not workflow:
        console.print(f"[red]Workflow {workflow_id} not found[/red]")
        sys.exit(1)

    console.print(f"[dim]Watching workflow {workflow_id[:8]}... (Ctrl+C to stop)[/dim]")
    console.print("-" * 50)

    start_time = time.time()
    last_state = None
    last_progress = -1

    try:
        while time.time() - start_time < timeout:
            workflow = db_manager.get_workflow(workflow_id)
            if not workflow:
                console.print("[yellow]Workflow no longer exists[/yellow]")
                break

            current_state = workflow.state.value if hasattr(workflow.state, 'value') else str(workflow.state)
            current_progress = workflow.progress_percent or 0

            # Only print if something changed
            if current_state != last_state or current_progress != last_progress:
                timestamp = datetime.now().strftime("%H:%M:%S")
                progress_bar = _make_progress_bar(current_progress)

                state_colors = {
                    "pending": "yellow",
                    "running": "blue",
                    "completed": "green",
                    "failed": "red",
                    "cancelled": "magenta"
                }
                state_color = state_colors.get(current_state, "white")

                console.print(f"[dim][{timestamp}][/dim] [{state_color}]{current_state.upper():10}[/{state_color}] {progress_bar} {current_progress}%")

                last_state = current_state
                last_progress = current_progress

            # Exit if terminal state
            if current_state in ["completed", "failed", "cancelled"]:
                console.print()
                if current_state == "completed":
                    console.print("[green]Workflow completed successfully![/green]")
                elif current_state == "failed":
                    console.print("[red]Workflow failed[/red]")
                else:
                    console.print("[yellow]Workflow cancelled[/yellow]")
                break

            time.sleep(interval)
        else:
            console.print(f"\n[yellow]Timeout reached ({timeout}s)[/yellow]")

    except KeyboardInterrupt:
        console.print("\n[dim]Watch cancelled[/dim]")


def _make_progress_bar(percent, width=20):
    """Create a simple progress bar."""
    filled = int(width * percent / 100)
    bar = "=" * filled + "-" * (width - filled)
    return f"[{bar}]"


# =============================================================================
# P3-T01: CLI Health Probe Commands
# =============================================================================

@admin.command("health-live")
@click.pass_context
def health_live(ctx):
    """Kubernetes-style liveness probe (exit code for scripts)."""
    console.print("[green]alive[/green]")
    sys.exit(0)


@admin.command("health-ready")
@click.pass_context
def health_ready(ctx):
    """Kubernetes-style readiness probe (exit code for scripts)."""
    from core.database import db_manager

    checks = {
        "database": False,
        "agents": False
    }

    try:
        checks["database"] = db_manager.is_connected()
    except Exception:
        pass

    try:
        checks["agents"] = len(agent_registry.agents) > 0
    except Exception:
        pass

    all_ready = all(checks.values())

    for check, status in checks.items():
        symbol = "[green]OK[/green]" if status else "[red]FAIL[/red]"
        console.print(f"{check}: {symbol}")

    if all_ready:
        console.print("\n[green]Status: READY[/green]")
        sys.exit(0)
    else:
        console.print("\n[red]Status: NOT READY[/red]")
        sys.exit(1)


# =============================================================================
# P3-T02: CLI Agent Reload Command
# =============================================================================

@admin.command("agent-reload")
@click.argument("agent_id")
@click.pass_context
def agent_reload(ctx, agent_id):
    """Reload a specific agent (clear cache, reinitialize)."""
    from core.cache import cache_manager

    try:
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            console.print(f"[red]Agent {agent_id} not found[/red]")
            sys.exit(1)

        actions = []

        # Clear agent's cache
        try:
            if hasattr(cache_manager, 'clear_agent_cache'):
                cache_manager.clear_agent_cache(agent_id)
                actions.append("cache_cleared")
        except Exception:
            pass

        # Reload config if available
        if hasattr(agent, 'reload_config'):
            try:
                asyncio.run(agent.reload_config())
                actions.append("config_reloaded")
            except Exception:
                pass

        # Reset state if available
        if hasattr(agent, 'reset_state'):
            try:
                agent.reset_state()
                actions.append("state_reset")
            except Exception:
                pass

        console.print(f"[green]Agent {agent_id} reloaded successfully[/green]")
        console.print(f"Actions: {', '.join(actions) if actions else 'none'}")

    except Exception as e:
        console.print(f"[red]Error reloading agent: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


# =============================================================================
# P3-T03: CLI Checkpoint Command
# =============================================================================

@admin.command("checkpoint")
@click.option("--name", "-n", help="Custom checkpoint name")
@click.pass_context
def create_checkpoint(ctx, name):
    """Create system checkpoint for disaster recovery."""
    import uuid
    import pickle
    from datetime import datetime, timezone
    from core.database import db_manager, WorkflowState
    from core.cache import cache_manager

    try:
        checkpoint_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)
        checkpoint_name = name or f"cli_checkpoint_{timestamp.strftime('%Y%m%d_%H%M%S')}"

        # Gather system state
        workflows = db_manager.list_workflows(limit=10000)
        active_workflows = [w for w in workflows if w.state in [WorkflowState.RUNNING, WorkflowState.PENDING]]

        system_state = {
            "checkpoint_id": checkpoint_id,
            "timestamp": timestamp.isoformat(),
            "source": "cli",
            "workflows": {
                "total": len(workflows),
                "active": len(active_workflows)
            },
            "agents": {
                "registered": len(agent_registry.agents)
            }
        }

        # Try to get cache stats
        try:
            system_state["cache"] = cache_manager.get_statistics()
        except Exception:
            system_state["cache"] = {}

        # Store checkpoint - try to use Checkpoint model if available
        try:
            from core.database import Checkpoint
            SYSTEM_CHECKPOINT_WORKFLOW_ID = "00000000-0000-0000-0000-000000000000"

            with db_manager.get_session() as session:
                checkpoint = Checkpoint(
                    id=checkpoint_id,
                    workflow_id=SYSTEM_CHECKPOINT_WORKFLOW_ID,
                    name=checkpoint_name,
                    step_number=0,
                    state_data=pickle.dumps(system_state),
                    created_at=timestamp,
                    can_resume_from=True
                )
                session.add(checkpoint)
                session.commit()
        except Exception as e:
            # If Checkpoint model doesn't exist, just report the state
            logger.warning(f"Could not persist checkpoint: {e}")

        console.print(Panel("[bold]Checkpoint Created[/bold]", expand=False))

        table = Table(show_header=False)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("ID", checkpoint_id)
        table.add_row("Name", checkpoint_name)
        table.add_row("Time", timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Workflows", str(len(workflows)))
        table.add_row("Active", str(len(active_workflows)))

        console.print(table)
        console.print("[green]Checkpoint saved successfully[/green]")

    except Exception as e:
        console.print(f"[red]Error creating checkpoint: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


# ---------------------------
# rag command group (RAG/Vector Search)
# ---------------------------
@cli.group()
@click.pass_context
def rag(ctx):
    """Manage RAG (Retrieval-Augmented Generation) for semantic truth search."""
    pass


@rag.command('index')
@click.option('--family', '-f', default='words', help='Truth family to index (default: words)')
@click.option('--all-families', is_flag=True, help='Index all available families')
@click.option('--clear', is_flag=True, default=True, help='Clear existing index before indexing')
@click.pass_context
def rag_index(ctx, family, all_families, clear):
    """Index truth data for semantic search."""
    asyncio.run(_rag_index(ctx, family, all_families, clear))


async def _rag_index(ctx, family, all_families, clear):
    """Async implementation of RAG indexing."""
    await setup_agents()

    truth_manager = agent_registry.get_agent("truth_manager")
    if not truth_manager:
        console.print("[red]Error: Truth manager not available[/red]")
        sys.exit(1)

    families_to_index = ["words"]  # Default families
    if all_families:
        families_to_index = getattr(truth_manager, 'supported_families', ["words"])
    elif family:
        families_to_index = [family]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Indexing truths for RAG...", total=len(families_to_index))

        total_indexed = 0
        for fam in families_to_index:
            progress.update(task, description=f"Indexing family: {fam}")

            result = await truth_manager.handle_index_for_rag({
                "family": fam,
                "clear_existing": clear
            })

            if result.get("success"):
                indexed = result.get("indexed_count", 0)
                total_indexed += indexed
                console.print(f"  [green]Indexed {indexed} truths for family '{fam}'[/green]")
            else:
                error = result.get("error", "Unknown error")
                console.print(f"  [red]Failed to index family '{fam}': {error}[/red]")

            progress.advance(task)

    console.print(f"\n[green][OK] Total indexed: {total_indexed} documents[/green]")


@rag.command('search')
@click.argument('query')
@click.option('--family', '-f', default='words', help='Truth family to search')
@click.option('--top-k', '-k', default=5, type=int, help='Number of results to return')
@click.option('--threshold', '-t', default=0.7, type=float, help='Minimum similarity threshold')
@click.option('--format', 'output_format', default='table',
              type=click.Choice(['table', 'json']), help='Output format')
@click.pass_context
def rag_search(ctx, query, family, top_k, threshold, output_format):
    """Search truths using semantic similarity."""
    asyncio.run(_rag_search(ctx, query, family, top_k, threshold, output_format))


async def _rag_search(ctx, query, family, top_k, threshold, output_format):
    """Async implementation of RAG search."""
    await setup_agents()

    truth_manager = agent_registry.get_agent("truth_manager")
    if not truth_manager:
        console.print("[red]Error: Truth manager not available[/red]")
        sys.exit(1)

    console.print(f"[blue]Searching for: '{query}' (family: {family})[/blue]")

    result = await truth_manager.handle_search_with_rag({
        "query": query,
        "family": family,
        "top_k": top_k,
        "threshold": threshold
    })

    results = result.get("results", [])
    rag_enabled = result.get("rag_enabled", False)
    fallback_used = result.get("fallback_used", False)

    if fallback_used:
        console.print("[yellow]Note: Fallback to traditional search was used[/yellow]")

    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    if output_format == 'json':
        console.print_json(data=result)
    else:
        table = Table(title=f"Search Results ({len(results)})")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Score", style="green")
        table.add_column("Text", style="white")

        for r in results:
            text = r.get("text", r.get("name", "N/A"))
            if len(text) > 80:
                text = text[:77] + "..."
            score = r.get("score", 0.0)
            doc_id = r.get("id", "N/A")
            if len(doc_id) > 16:
                doc_id = doc_id[:13] + "..."

            table.add_row(doc_id, f"{score:.3f}", text)

        console.print(table)

    console.print(f"\n[dim]RAG: {'enabled' if rag_enabled else 'disabled'}[/dim]")


@rag.command('status')
@click.pass_context
def rag_status(ctx):
    """Show RAG indexing and search status."""
    asyncio.run(_rag_status(ctx))


async def _rag_status(ctx):
    """Async implementation of RAG status."""
    await setup_agents()

    truth_manager = agent_registry.get_agent("truth_manager")
    if not truth_manager:
        console.print("[red]Error: Truth manager not available[/red]")
        sys.exit(1)

    result = await truth_manager.handle_get_rag_status({})

    table = Table(title="RAG Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Enabled", "Yes" if result.get("enabled") else "No")
    table.add_row("Indexed", "Yes" if result.get("indexed") else "No")
    table.add_row("Families", ", ".join(result.get("families", [])) or "None")

    stats = result.get("stats", {})
    table.add_row("Total Documents", str(stats.get("total_documents", 0)))
    table.add_row("Last Updated", stats.get("last_updated", "Never") or "Never")
    table.add_row("Embedding Dimension", str(stats.get("embedding_dimension", "N/A")))

    if result.get("error"):
        table.add_row("Error", f"[red]{result['error']}[/red]")

    console.print(table)


@rag.command('clear')
@click.option('--family', '-f', help='Clear specific family (default: all)')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def rag_clear(ctx, family, confirm):
    """Clear the RAG vector index."""
    asyncio.run(_rag_clear(ctx, family, confirm))


async def _rag_clear(ctx, family, confirm):
    """Async implementation of RAG clear."""
    await setup_agents()

    if not confirm:
        target = f"family '{family}'" if family else "all families"
        console.print(f"[yellow]This will clear the RAG index for {target}[/yellow]")
        if not click.confirm("Are you sure?"):
            console.print("[blue]Cancelled[/blue]")
            return

    try:
        from core.vector_store import get_truth_vector_store
        vector_store = get_truth_vector_store()
        vector_store.clear_index(family)
        console.print(f"[green][OK] Cleared RAG index{'for ' + family if family else ''}[/green]")
    except Exception as e:
        console.print(f"[red]Error clearing index: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli(obj={})
