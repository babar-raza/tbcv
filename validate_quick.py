#!/usr/bin/env python
"""
Quick validation script for testing the new modular validator architecture.

Usage:
    python validate_quick.py <file.md>
    python validate_quick.py <file.md> --validators seo,yaml,markdown
    python validate_quick.py <file.md> --all
    python validate_quick.py <file.md> --verbose

This script uses the new ValidatorRouter to run validations without starting
the full server. Perfect for quick testing and development.
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

from agents.validators.seo_validator import SeoValidatorAgent
from agents.validators.yaml_validator import YamlValidatorAgent
from agents.validators.markdown_validator import MarkdownValidatorAgent
from agents.validators.code_validator import CodeValidatorAgent
from agents.validators.link_validator import LinkValidatorAgent
from agents.validators.structure_validator import StructureValidatorAgent
from agents.validators.truth_validator import TruthValidatorAgent
from agents.validators.router import ValidatorRouter
from agents.base import agent_registry


async def run_validation(file_path: str, validator_types: list, verbose: bool = False):
    """Run validation on a file using specified validators."""

    # Read file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"[ERROR] Failed to read file: {e}")
        return 1

    # Register all available validators
    agent_registry.register_agent(SeoValidatorAgent("seo_validator"))
    agent_registry.register_agent(YamlValidatorAgent("yaml_validator"))
    agent_registry.register_agent(MarkdownValidatorAgent("markdown_validator"))
    agent_registry.register_agent(CodeValidatorAgent("code_validator"))
    agent_registry.register_agent(LinkValidatorAgent("link_validator"))
    agent_registry.register_agent(StructureValidatorAgent("structure_validator"))
    agent_registry.register_agent(TruthValidatorAgent("truth_validator"))

    # Create router
    router = ValidatorRouter(agent_registry)

    # Run validations
    print(f"\n{'='*60}")
    print(f"Validating: {file_path}")
    print(f"Validators: {', '.join(validator_types)}")
    print(f"{'='*60}\n")

    result = await router.execute(
        validation_types=validator_types,
        content=content,
        context={"file_path": file_path, "family": "words"},
        ui_override=False
    )

    # Display results
    routing_info = result.get('routing_info', {})
    validation_results = result.get('validation_results', {})

    total_issues = 0
    total_validators = len(validator_types)
    successful_validations = 0

    for val_type in validator_types:
        route_status = routing_info.get(val_type, 'unknown')
        val_result = validation_results.get(f"{val_type}_validation", {})

        if route_status == 'error':
            print(f"[FAILED] {val_type}: {val_result.get('error', 'Unknown error')}")
            continue

        if route_status == 'unknown_type':
            print(f"[SKIP] {val_type}: Unknown validator type")
            continue

        successful_validations += 1
        confidence = val_result.get('confidence', 0.0)
        issues = val_result.get('issues', [])
        used_legacy = val_result.get('used_legacy', False)
        total_issues += len(issues)

        # Determine status emoji
        if len(issues) == 0:
            status = "[PASS]"
        elif all(issue.get('level') in ['info', 'warning'] for issue in issues):
            status = "[WARN]"
        else:
            status = "[FAIL]"

        validator_type_label = "legacy" if used_legacy else "new"
        print(f"{status} {val_type} ({validator_type_label}): {len(issues)} issues, confidence={confidence:.2f}")

        # Show issues if verbose or if there are errors
        if verbose or any(issue.get('level') == 'error' for issue in issues):
            for issue in issues:
                level = issue.get('level', 'info').upper()
                category = issue.get('category', 'unknown')
                message = issue.get('message', '')
                line = issue.get('line_number')
                line_str = f" (line {line})" if line else ""

                print(f"  [{level}] {message}{line_str}")

                if verbose and issue.get('suggestion'):
                    print(f"    Suggestion: {issue.get('suggestion')}")

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total validators run: {successful_validations}/{total_validators}")
    print(f"Total issues found: {total_issues}")

    if total_issues == 0:
        print(f"\n[SUCCESS] All validations passed!")
        return 0
    else:
        errors = sum(1 for val_result in validation_results.values()
                    for issue in val_result.get('issues', [])
                    if issue.get('level') == 'error')
        warnings = sum(1 for val_result in validation_results.values()
                      for issue in val_result.get('issues', [])
                      if issue.get('level') == 'warning')

        print(f"\nErrors: {errors}, Warnings: {warnings}")

        if errors > 0:
            print(f"\n[FAILED] Validation failed with {errors} error(s)")
            return 1
        else:
            print(f"\n[WARN] Validation completed with warnings")
            return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Quick validator testing tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_quick.py test.md
  python validate_quick.py test.md --validators seo,yaml
  python validate_quick.py test.md --all --verbose
        """
    )

    parser.add_argument('file', help='File to validate')
    parser.add_argument(
        '--validators', '-v',
        help='Comma-separated list of validators (default: seo,yaml,markdown)',
        default='seo,yaml,markdown'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Run all available validators'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output including suggestions'
    )

    args = parser.parse_args()

    # Check file exists
    if not Path(args.file).exists():
        print(f"[ERROR] File not found: {args.file}")
        return 1

    # Determine which validators to run
    if args.all:
        validator_types = ['seo', 'yaml', 'markdown', 'code', 'links', 'structure', 'Truth']
    else:
        validator_types = [v.strip() for v in args.validators.split(',')]

    # Run async validation
    exit_code = asyncio.run(run_validation(args.file, validator_types, args.verbose))
    return exit_code


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
