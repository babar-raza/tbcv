#!/usr/bin/env python
"""
Quick demonstration of language detection functionality.
Run this to see language detection in action.
"""

from core.language_utils import is_english_content, validate_english_content_batch
from rich.console import Console
from rich.table import Table

console = Console()

def demo_single_file_checks():
    """Demonstrate single file language checks."""
    console.print("\n[bold cyan]Single File Language Detection Demo[/bold cyan]\n")

    test_cases = [
        # (file_path, description)
        ("/docs/en/words/index.md", "Standard English path"),
        ("/docs/fr/words/index.md", "French path"),
        ("/docs/es/cells/features.md", "Spanish path"),
        ("/blog.aspose.net/post/index.md", "Blog English (index.md)"),
        ("/blog.aspose.net/post/index.fr.md", "Blog French"),
        ("/api/en/reference.md", "API English"),
        ("/api/de/reference.md", "API German"),
    ]

    table = Table(title="Language Detection Results", show_header=True)
    table.add_column("File Path", style="cyan", width=50)
    table.add_column("Description", style="white", width=25)
    table.add_column("Status", style="bold", width=15)
    table.add_column("Reason", style="yellow", width=40)

    for file_path, description in test_cases:
        is_english, reason = is_english_content(file_path)
        status = "[green]ACCEPTED[/green]" if is_english else "[red]REJECTED[/red]"
        table.add_row(file_path, description, status, reason)

    console.print(table)


def demo_batch_validation():
    """Demonstrate batch validation."""
    console.print("\n[bold cyan]Batch Validation Demo[/bold cyan]\n")

    file_paths = [
        "/docs/en/words/index.md",
        "/docs/fr/words/index.md",
        "/docs/es/cells/features.md",
        "/docs/en/slides/tutorial.md",
        "/blog.aspose.net/post/index.md",
        "/blog.aspose.net/post/index.de.md",
        "/api/en/reference.md",
        "/api/it/reference.md",
    ]

    console.print(f"[yellow]Input:[/yellow] {len(file_paths)} files")
    console.print()

    valid_paths, rejected = validate_english_content_batch(file_paths)

    console.print(f"[green]Accepted:[/green] {len(valid_paths)} English files")
    for path in valid_paths:
        console.print(f"  - {path}")

    console.print()
    console.print(f"[red]Rejected:[/red] {len(rejected)} non-English files")
    for path, reason in rejected:
        console.print(f"  - {path}")
        console.print(f"    Reason: {reason}")


def demo_realistic_paths():
    """Demonstrate with realistic Aspose documentation paths."""
    console.print("\n[bold cyan]Realistic Aspose Documentation Paths[/bold cyan]\n")

    test_cases = [
        # English paths
        ("/home/docs/en/words/net/developer-guide/programming-with-documents/working-with-images/index.md", True),
        ("/var/www/products/en/cells/java/conversion/xlsx-to-pdf.md", True),
        ("C:\\Aspose\\docs\\en\\slides\\cpp\\getting-started\\index.md", True),

        # Non-English paths
        ("/home/docs/fr/words/net/developer-guide/index.md", False),
        ("/var/www/products/zh/cells/java/index.md", False),
        ("C:\\Aspose\\docs\\ja\\slides\\cpp\\index.md", False),
    ]

    table = Table(title="Realistic Path Detection", show_header=True)
    table.add_column("File Path", style="cyan", width=80)
    table.add_column("Expected", style="white", width=15)
    table.add_column("Result", style="bold", width=15)

    for path, expected_is_english in test_cases:
        is_english, reason = is_english_content(path)
        result = "[green]PASS[/green]" if is_english == expected_is_english else "[red]FAIL[/red]"
        expected = "English" if expected_is_english else "Non-English"
        table.add_row(path, expected, result)

    console.print(table)


if __name__ == "__main__":
    console.print("[bold magenta]" + "=" * 100 + "[/bold magenta]")
    console.print("[bold magenta]TBCV Language Detection System - Live Demo[/bold magenta]")
    console.print("[bold magenta]" + "=" * 100 + "[/bold magenta]")

    demo_single_file_checks()
    demo_batch_validation()
    demo_realistic_paths()

    console.print("\n[bold green]Demo Complete![/bold green]")
    console.print("\n[yellow]Key Takeaways:[/yellow]")
    console.print("  - Only English content (with /en/ in path) is accepted")
    console.print("  - Blog posts use index.md for English, index.{lang}.md for others")
    console.print("  - All non-English content is automatically rejected")
    console.print("  - Works with Windows and Unix path separators")
    console.print()
