#!/usr/bin/env python3
"""
Test File Diagnostic Tool
=========================

This script diagnoses why your test file isn't working.
Run this before running the test suite.

Usage:
    python diagnose_tests.py
    python diagnose_tests.py --file tests/test_everything.py
"""

import argparse
import ast
import sys
from pathlib import Path
from typing import List, Tuple


def check_file_exists(file_path: Path) -> bool:
    """Check if file exists."""
    print(f"\n1. Checking if file exists: {file_path}")
    if file_path.exists():
        print(f"   [OK] File exists")
        print(f"   Size: {file_path.stat().st_size} bytes")
        return True
    else:
        print(f"   [FAIL] File NOT found")
        return False


def check_syntax(file_path: Path) -> bool:
    """Check if file has valid Python syntax."""
    print(f"\n2. Checking Python syntax...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        print(f"   [OK] Syntax is valid")
        return True
    except SyntaxError as e:
        print(f"   [FAIL] Syntax Error at line {e.lineno}: {e.msg}")
        return False
    except Exception as e:
        print(f"   [FAIL] Error reading file: {e}")
        return False


def check_imports(file_path: Path) -> Tuple[bool, List[str]]:
    """Check if all imports work."""
    print(f"\n3. Checking imports...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        imports = []
        failed_imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        print(f"   Found {len(set(imports))} unique imports")
        
        # Try importing each one
        for imp in set(imports):
            try:
                __import__(imp.split('.')[0])
                print(f"   [OK] {imp}")
            except ImportError as e:
                print(f"   [FAIL] {imp} - {e}")
                failed_imports.append(imp)
        
        if failed_imports:
            print(f"\n   {len(failed_imports)} imports failed!")
            print("   Install with: pip install -r requirements.txt")
            return False, failed_imports
        else:
            print(f"   [OK] All imports successful")
            return True, []
            
    except Exception as e:
        print(f"   [FAIL] Error checking imports: {e}")
        return False, []


def check_test_functions(file_path: Path) -> Tuple[bool, List[str]]:
    """Check for test functions."""
    print(f"\n4. Checking for test functions...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        test_functions = []
        test_classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_'):
                    test_functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                if node.name.startswith('Test'):
                    test_classes.append(node.name)
                    # Count test methods in class
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
                            test_functions.append(f"{node.name}.{item.name}")
        
        print(f"   Found {len(test_classes)} test classes")
        print(f"   Found {len(test_functions)} test functions/methods")
        
        if test_functions:
            print(f"\n   Test functions found:")
            for func in test_functions[:10]:  # Show first 10
                print(f"      - {func}")
            if len(test_functions) > 10:
                print(f"      ... and {len(test_functions) - 10} more")
            return True, test_functions
        else:
            print(f"   [FAIL] NO test functions found!")
            print(f"   Test functions must:")
            print(f"      - Start with 'test_' (e.g., def test_something():)")
            print(f"      - Be inside classes that start with 'Test' (e.g., class TestSomething:)")
            return False, []
            
    except Exception as e:
        print(f"   [FAIL] Error parsing file: {e}")
        return False, []


def check_pytest_collection(file_path: Path) -> bool:
    """Try to collect tests with pytest."""
    print(f"\n5. Trying pytest collection...")
    
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', str(file_path), '--collect-only', '-q'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        output = result.stdout + result.stderr
        
        # Look for "collected X items"
        import re
        match = re.search(r'collected (\d+) item', output)
        
        if match:
            count = int(match.group(1))
            print(f"   [OK] Pytest collected {count} tests")
            return count > 0
        else:
            print(f"   [FAIL] Pytest could not collect tests")
            print(f"\n   Pytest output:")
            print(output)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"   [FAIL] Pytest collection timed out")
        return False
    except Exception as e:
        print(f"   [FAIL] Error running pytest: {e}")
        return False


def find_test_files() -> List[Path]:
    """Find all test files."""
    test_dir = Path('tests')
    if not test_dir.exists():
        return []
    
    test_files = []
    for pattern in ['test_*.py', '*_test.py']:
        test_files.extend(test_dir.glob(pattern))
        test_files.extend(test_dir.glob(f'*/{pattern}'))
    
    return sorted(set(test_files))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Diagnose test file issues')
    parser.add_argument(
        '--file',
        type=Path,
        help='Test file to diagnose (default: auto-detect)'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("TEST FILE DIAGNOSTIC TOOL")
    print("=" * 80)
    
    # Find test file
    if args.file:
        test_file = args.file
    else:
        # Try to find test file
        possible_names = [
            Path('tests/test_everything.py'),
            Path('tests/test_comprehensive_integration.py'),
            Path('tests/test_comprehensive.py'),
        ]
        
        test_file = None
        for path in possible_names:
            if path.exists():
                test_file = path
                break
        
        if not test_file:
            print("\nNo test file specified and couldn't auto-detect.")
            print("\nAvailable test files:")
            test_files = find_test_files()
            if test_files:
                for tf in test_files:
                    print(f"  - {tf}")
                print(f"\nRe-run with: python diagnose_tests.py --file tests/YOUR_TEST_FILE.py")
            else:
                print("  No test files found in tests/ directory")
            return 1
    
    print(f"\nDiagnosing: {test_file}")
    print("=" * 80)
    
    # Run diagnostics
    all_passed = True
    
    # 1. File exists
    if not check_file_exists(test_file):
        print("\n" + "=" * 80)
        print("DIAGNOSIS FAILED: File doesn't exist")
        return 1
    
    # 2. Syntax
    if not check_syntax(test_file):
        all_passed = False
        print("\n" + "=" * 80)
        print("DIAGNOSIS FAILED: Syntax errors")
        return 1
    
    # 3. Imports
    imports_ok, failed_imports = check_imports(test_file)
    if not imports_ok:
        all_passed = False
        print("\n" + "=" * 80)
        print("DIAGNOSIS FAILED: Import errors")
        print(f"\nFailed imports: {', '.join(failed_imports)}")
        print("Install with: pip install -r requirements.txt")
        return 1
    
    # 4. Test functions
    has_tests, test_funcs = check_test_functions(test_file)
    if not has_tests:
        all_passed = False
        print("\n" + "=" * 80)
        print("DIAGNOSIS FAILED: No test functions found")
        print("\nMake sure your functions:")
        print("  1. Start with 'test_' (e.g., def test_something():)")
        print("  2. Are in classes starting with 'Test' (e.g., class TestSomething:)")
        return 1
    
    # 5. Pytest collection
    if not check_pytest_collection(test_file):
        all_passed = False
        print("\n" + "=" * 80)
        print("DIAGNOSIS FAILED: Pytest cannot collect tests")
        print("\nThis usually means there's a runtime import error.")
        print("Try running: python -m pytest", str(test_file), "--collect-only")
        return 1
    
    # Summary
    print("\n" + "=" * 80)
    if all_passed:
        print("[OK] DIAGNOSIS PASSED - File should work with pytest!")
        print("\nRun tests with:")
        print(f"  python -m pytest {test_file} -v")
        print("  python all_tests.py")
        return 0
    else:
        print("[FAIL] DIAGNOSIS FAILED - See errors above")
        return 1


if __name__ == '__main__':
    sys.exit(main())
