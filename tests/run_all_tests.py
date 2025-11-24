#!/usr/bin/env python3
"""
Comprehensive test runner for TBCV system
Runs all tests and provides summary
"""
import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run all test suites"""
    test_dir = Path(__file__).parent
    
    test_files = [
        "test_truth_validation.py",
        "test_fuzzy_logic.py",
        "test_recommendations.py",
        "test_websocket.py",
        "test_cli_web_parity.py"
    ]
    
    print("=" * 70)
    print("TBCV Comprehensive Test Suite")
    print("=" * 70)
    
    results = {}
    
    for test_file in test_files:
        test_path = test_dir / test_file
        if not test_path.exists():
            print(f"\n❌ {test_file} - NOT FOUND")
            results[test_file] = "NOT_FOUND"
            continue
        
        print(f"\n📝 Running {test_file}...")
        print("-" * 70)
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_path), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=test_dir.parent
            )
            
            if result.returncode == 0:
                print(f"✅ {test_file} - PASSED")
                results[test_file] = "PASSED"
            else:
                print(f"❌ {test_file} - FAILED")
                print(result.stdout)
                print(result.stderr)
                results[test_file] = "FAILED"
        except Exception as e:
            print(f"⚠️  {test_file} - ERROR: {e}")
            results[test_file] = "ERROR"
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for r in results.values() if r == "PASSED")
    failed = sum(1 for r in results.values() if r == "FAILED")
    errors = sum(1 for r in results.values() if r in ["ERROR", "NOT_FOUND"])
    
    for test_file, status in results.items():
        icon = "✅" if status == "PASSED" else "❌" if status == "FAILED" else "⚠️ "
        print(f"{icon} {test_file}: {status}")
    
    print("\n" + "-" * 70)
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
    print("=" * 70)
    
    return failed + errors == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
