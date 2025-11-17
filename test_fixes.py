#!/usr/bin/env python
"""
Validation script to verify all fixes are working correctly.
"""
import sys
import py_compile
from pathlib import Path

def test_syntax():
    """Test that all fixed files have valid Python syntax."""
    print("Testing syntax of fixed files...")
    
    files_to_test = [
        "api/websocket_endpoints.py",
        "agents/base.py",
        "agents/truth_manager.py",
        "tests/test_truth_validation.py"
    ]
    
    all_valid = True
    for filepath in files_to_test:
        try:
            py_compile.compile(filepath, doraise=True)
            print(f"  ✓ {filepath} - syntax valid")
        except py_compile.PyCompileError as e:
            print(f"  ✗ {filepath} - syntax error: {e}")
            all_valid = False
    
    return all_valid

def test_imports():
    """Test that fixed imports work correctly."""
    print("\nTesting import fixes...")
    
    try:
        # Test that from __future__ import is now first in websocket_endpoints.py
        with open("api/websocket_endpoints.py", "r") as f:
            lines = f.readlines()
            # Find first non-comment, non-empty line
            first_code_line = None
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                    first_code_line = stripped
                    break
            
            if first_code_line and first_code_line.startswith("from __future__ import"):
                print("  ✓ websocket_endpoints.py - from __future__ import is first")
            else:
                print(f"  ✗ websocket_endpoints.py - from __future__ import is not first (found: {first_code_line})")
                return False
    except Exception as e:
        print(f"  ✗ Failed to check websocket_endpoints.py: {e}")
        return False
    
    return True

def test_datetime_fixes():
    """Test that datetime.utcnow() has been replaced."""
    print("\nTesting datetime.utcnow() replacements...")
    
    files_to_check = [
        "api/websocket_endpoints.py",
        "agents/base.py",
        "agents/truth_manager.py"
    ]
    
    all_fixed = True
    for filepath in files_to_check:
        try:
            with open(filepath, "r") as f:
                content = f.read()
                if "datetime.utcnow()" in content:
                    print(f"  ✗ {filepath} - still contains datetime.utcnow()")
                    all_fixed = False
                else:
                    print(f"  ✓ {filepath} - datetime.utcnow() replaced")
        except Exception as e:
            print(f"  ✗ Failed to check {filepath}: {e}")
            all_fixed = False
    
    return all_fixed

def test_fixture_await_fix():
    """Test that await has been removed from fixture usage."""
    print("\nTesting pytest fixture await fix...")
    
    try:
        with open("tests/test_truth_validation.py", "r") as f:
            content = f.read()
            
        # Check that "await setup_orchestrator_environment" doesn't appear
        if "await setup_orchestrator_environment" in content:
            print("  ✗ test_truth_validation.py - still contains 'await setup_orchestrator_environment'")
            return False
        else:
            print("  ✓ test_truth_validation.py - fixture await removed")
            return True
    except Exception as e:
        print(f"  ✗ Failed to check test_truth_validation.py: {e}")
        return False

def main():
    """Run all validation tests."""
    print("=" * 70)
    print("VALIDATION SCRIPT FOR TBCV FIXES")
    print("=" * 70)
    
    results = []
    
    # Run all tests
    results.append(("Syntax validation", test_syntax()))
    results.append(("Import order fix", test_imports()))
    results.append(("Datetime deprecation fix", test_datetime_fixes()))
    results.append(("Pytest fixture fix", test_fixture_await_fix()))
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    all_passed = all(result for _, result in results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print("=" * 70)
    
    if all_passed:
        print("✓ ALL FIXES VALIDATED SUCCESSFULLY")
        return 0
    else:
        print("✗ SOME FIXES FAILED VALIDATION")
        return 1

if __name__ == "__main__":
    sys.exit(main())
