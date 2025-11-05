#!/usr/bin/env python3
"""
Comprehensive Test Runner for TBCV System (Windows Compatible - v2)
==========================================

Improved version with better diagnostics and error detection.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")


def check_dependencies() -> Dict[str, bool]:
    """Check if all required dependencies are available."""
    print_header("Checking Dependencies")
    
    dependencies = {
        'pytest': False,
        'pytest-asyncio': False,
        'pytest-cov': False,
        'fastapi': False,
        'sqlalchemy': False,
        'uvicorn': False,
        'httpx': False
    }
    
    for dep in dependencies.keys():
        try:
            module_name = dep.replace('-', '_')
            if dep == 'pytest-asyncio':
                module_name = 'pytest_asyncio'
            elif dep == 'pytest-cov':
                module_name = 'pytest_cov'
            __import__(module_name)
            dependencies[dep] = True
            print_success(f"{dep} is available")
        except ImportError:
            dependencies[dep] = False
            print_error(f"{dep} is NOT available")
    
    return dependencies


def check_ollama_service() -> bool:
    """Check if Ollama service is running."""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/version', timeout=2)
        if response.status_code == 200:
            print_success("Ollama service is running")
            return True
    except:
        pass
    
    print_warning("Ollama service is not running (will use mocks)")
    return False


def find_test_file() -> str:
    """Find the test file (handles renamed files)."""
    possible_names = [
        'test_everything.py',
        'test_comprehensive_integration.py',
        'test_comprehensive.py',
        'test_integration.py'
    ]
    
    tests_dir = Path(__file__).parent / 'tests'
    
    for name in possible_names:
        test_file = tests_dir / name
        if test_file.exists():
            return str(test_file)
    
    # If not found, return the first option as default
    return str(tests_dir / possible_names[0])


def run_pytest_command(args: List[str], test_file: str = None) -> Dict[str, Any]:
    """Run pytest with given arguments using python -m pytest (Windows compatible)."""
    # Use python -m pytest instead of pytest directly for Windows compatibility
    cmd = [sys.executable, '-m', 'pytest']
    
    if test_file:
        cmd.append(test_file)
    else:
        cmd.append(find_test_file())
    
    cmd.extend(args)
    
    # Convert Path objects to strings
    cmd = [str(c) for c in cmd]
    
    print_info(f"Running: {' '.join(cmd)}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(Path(__file__).parent),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        duration = time.time() - start_time
        
        return {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'duration': duration,
            'cmd': ' '.join(cmd)
        }
    except FileNotFoundError as e:
        print_error(f"Failed to run pytest: {e}")
        print_info("Make sure pytest is installed: pip install pytest")
        return {
            'returncode': 1,
            'stdout': '',
            'stderr': str(e),
            'duration': 0,
            'cmd': ' '.join(cmd)
        }
    except Exception as e:
        print_error(f"Error running pytest: {e}")
        return {
            'returncode': 1,
            'stdout': '',
            'stderr': str(e),
            'duration': 0,
            'cmd': ' '.join(cmd)
        }


def parse_pytest_output(output: str) -> Dict[str, Any]:
    """Parse pytest output to extract statistics."""
    stats = {
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'errors': 0,
        'warnings': 0,
        'duration': 0.0,
        'collected': 0
    }
    
    # Look for collection info
    for line in output.split('\n'):
        if 'collected' in line.lower():
            import re
            match = re.search(r'collected (\d+) item', line)
            if match:
                stats['collected'] = int(match.group(1))
    
    # Parse summary line
    for line in output.split('\n'):
        if 'passed' in line.lower() or 'failed' in line.lower():
            import re
            # Look for patterns like "10 passed in 5.2s"
            match = re.search(r'(\d+)\s+passed', line)
            if match:
                stats['passed'] = int(match.group(1))
            
            match = re.search(r'(\d+)\s+failed', line)
            if match:
                stats['failed'] = int(match.group(1))
            
            match = re.search(r'(\d+)\s+skipped', line)
            if match:
                stats['skipped'] = int(match.group(1))
            
            match = re.search(r'(\d+)\s+error', line)
            if match:
                stats['errors'] = int(match.group(1))
            
            match = re.search(r'in\s+([\d.]+)s', line)
            if match:
                stats['duration'] = float(match.group(1))
    
    return stats


def run_all_tests(verbose: bool = False, coverage: bool = False) -> Dict[str, Any]:
    """Run all comprehensive tests."""
    print_header("Running All Comprehensive Tests")
    
    # First, do a dry run to collect tests
    print_info("Collecting tests...")
    collect_result = run_pytest_command(['--collect-only', '-q'])
    collect_stats = parse_pytest_output(collect_result['stdout'])
    
    if collect_stats['collected'] == 0:
        print_error("No tests discovered!")
        print_warning("\nPossible reasons:")
        print_info("  1. Import errors in test file")
        print_info("  2. No functions starting with 'test_'")
        print_info("  3. Test file is empty or has syntax errors")
        print_info("  4. Wrong test file path")
        print("\nCollection output:")
        print(collect_result['stdout'])
        if collect_result['stderr']:
            print("\nCollection errors:")
            print(collect_result['stderr'])
        
        return {
            'result': collect_result,
            'stats': collect_stats,
            'no_tests_found': True
        }
    
    print_success(f"Found {collect_stats['collected']} tests")
    
    # Now run the actual tests
    args = [
        '-v' if verbose else '',
        '--tb=short',
        '--maxfail=10'
    ]
    
    if coverage:
        reports_dir = Path(__file__).parent / 'tests' / 'reports'
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        args.extend([
            '--cov=.',
            f'--cov-report=html:{reports_dir / "coverage"}',
            f'--cov-report=json:{reports_dir / "coverage.json"}',
            '--cov-report=term'
        ])
    
    # Remove empty strings
    args = [a for a in args if a]
    
    result = run_pytest_command(args)
    stats = parse_pytest_output(result['stdout'])
    
    if result['returncode'] != 0 and verbose:
        print("\nTest Output:")
        print(result['stdout'])
        if result['stderr']:
            print("\nErrors:")
            print(result['stderr'])
    
    return {
        'result': result,
        'stats': stats,
        'no_tests_found': False
    }


def run_test_category(category: str, verbose: bool = False) -> Dict[str, Any]:
    """Run tests for a specific category."""
    print_header(f"Running {category.upper()} Tests")
    
    args = [
        '-v' if verbose else '-q',
        '--tb=short',
        '-k', category
    ]
    
    result = run_pytest_command(args)
    stats = parse_pytest_output(result['stdout'])
    
    if result['returncode'] == 0:
        print_success(f"{category} tests passed")
    else:
        print_error(f"{category} tests failed")
        if verbose:
            print("\nOutput:")
            print(result['stdout'])
            if result['stderr']:
                print("\nErrors:")
                print(result['stderr'])
    
    print_info(f"Passed: {stats['passed']}, Failed: {stats['failed']}, Skipped: {stats['skipped']}")
    print_info(f"Duration: {stats['duration']:.2f}s")
    
    return {
        'category': category,
        'result': result,
        'stats': stats
    }


def run_performance_tests(verbose: bool = False) -> Dict[str, Any]:
    """Run performance benchmark tests."""
    print_header("Running Performance Tests")
    
    args = [
        '-v' if verbose else '-q',
        '--tb=short',
        '-k', 'performance',
        '--durations=10'
    ]
    
    result = run_pytest_command(args)
    stats = parse_pytest_output(result['stdout'])
    
    return {
        'category': 'performance',
        'result': result,
        'stats': stats
    }


def generate_report(results: Dict[str, Any], output_file: Path):
    """Generate JSON report of test results."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'python_version': sys.version,
        'platform': sys.platform,
        'results': results,
        'summary': {
            'total_passed': sum(r.get('stats', {}).get('passed', 0) for r in results.values() if isinstance(r, dict)),
            'total_failed': sum(r.get('stats', {}).get('failed', 0) for r in results.values() if isinstance(r, dict)),
            'total_skipped': sum(r.get('stats', {}).get('skipped', 0) for r in results.values() if isinstance(r, dict)),
            'total_duration': sum(r.get('stats', {}).get('duration', 0) for r in results.values() if isinstance(r, dict))
        }
    }
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print_success(f"Report generated: {output_file}")


def print_summary(results: Dict[str, Any]):
    """Print summary of all test results."""
    print_header("Test Summary")
    
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    total_duration = 0.0
    no_tests_found = False
    
    for category, result in results.items():
        if isinstance(result, dict):
            if result.get('no_tests_found'):
                no_tests_found = True
                
            if 'stats' in result:
                stats = result['stats']
                print(f"\n{Colors.BOLD}{category.upper()}{Colors.ENDC}")
                print(f"  Passed:   {stats.get('passed', 0)}")
                print(f"  Failed:   {stats.get('failed', 0)}")
                print(f"  Skipped:  {stats.get('skipped', 0)}")
                print(f"  Duration: {stats.get('duration', 0):.2f}s")
                
                total_passed += stats.get('passed', 0)
                total_failed += stats.get('failed', 0)
                total_skipped += stats.get('skipped', 0)
                total_duration += stats.get('duration', 0)
    
    print(f"\n{Colors.BOLD}OVERALL{Colors.ENDC}")
    print(f"  Total Passed:  {total_passed}")
    print(f"  Total Failed:  {total_failed}")
    print(f"  Total Skipped: {total_skipped}")
    print(f"  Total Time:    {total_duration:.2f}s")
    
    # Check if any tests actually ran
    total_tests = total_passed + total_failed + total_skipped
    
    if no_tests_found or total_tests == 0:
        print_error("\n✗ NO TESTS WERE DISCOVERED OR RUN!")
        print_warning("\nTo diagnose:")
        print_info("  1. Check if test file exists and has correct name")
        print_info("  2. Run: python -m pytest tests/test_everything.py --collect-only")
        print_info("  3. Check for import errors in test file")
        print_info("  4. Ensure test functions start with 'test_'")
        return 2  # Exit code 2 for no tests found
    elif total_failed == 0:
        print_success("\n✓ All tests passed!")
        return 0
    else:
        print_error(f"\n✗ {total_failed} test(s) failed")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run comprehensive TBCV integration tests'
    )
    parser.add_argument(
        '--category',
        choices=['api', 'agents', 'database', 'integration', 'performance', 'all'],
        default='all',
        help='Test category to run'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Generate coverage report'
    )
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Skip slow tests'
    )
    parser.add_argument(
        '--report',
        type=Path,
        default=Path('tests/reports/comprehensive_test_report.json'),
        help='Output report file'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_header("TBCV Comprehensive Test Suite")
    print(f"Category: {args.category}")
    print(f"Verbose:  {args.verbose}")
    print(f"Coverage: {args.coverage}")
    print(f"Report:   {args.report}")
    
    # Check dependencies
    deps = check_dependencies()
    missing_deps = [dep for dep, available in deps.items() if not available]
    
    if missing_deps:
        print_error(f"Missing dependencies: {', '.join(missing_deps)}")
        print_info("Install with: pip install -r requirements.txt")
        return 1
    
    # Check Ollama
    ollama_available = check_ollama_service()
    if not ollama_available:
        os.environ['OLLAMA_ENABLED'] = 'false'
    
    # Check test file exists
    test_file = find_test_file()
    if not Path(test_file).exists():
        print_error(f"Test file not found: {test_file}")
        print_info("Expected one of: test_everything.py, test_comprehensive_integration.py")
        return 1
    else:
        print_success(f"Found test file: {Path(test_file).name}")
    
    # Run tests based on category
    results = {}
    
    try:
        if args.category == 'all':
            results['all'] = run_all_tests(args.verbose, args.coverage)
        elif args.category == 'performance':
            results['performance'] = run_performance_tests(args.verbose)
        else:
            results[args.category] = run_test_category(args.category, args.verbose)
        
        # Generate report
        generate_report(results, args.report)
        
        # Print summary
        exit_code = print_summary(results)
        
        return exit_code
        
    except KeyboardInterrupt:
        print_warning("\n\nTests interrupted by user")
        return 130
    except Exception as e:
        print_error(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
