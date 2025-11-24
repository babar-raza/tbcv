#!/usr/bin/env python3
"""
Comprehensive test runner for TBCV.

Usage:
    python run_all_tests.py                           # Run all tests (unit + integration, skip local_heavy)
    python run_all_tests.py --all                     # Run ALL tests including local_heavy
    python run_all_tests.py --local-only              # Run only local_heavy tests
    python run_all_tests.py --unit                    # Run only unit tests
    python run_all_tests.py --integration              # Run only integration tests
    python run_all_tests.py --quick                   # Run smoke tests only
    python run_all_tests.py --file tests/test_x.py    # Run specific test file

Test categories:
    - Unit tests: Fast tests with mocks, no external dependencies
    - Integration tests: Tests with real agents but mocked LLM
    - Local/heavy tests: Full-stack tests with real Ollama and services

Prerequisites for local_heavy tests:
    - Ollama server running: ollama serve
    - Model available (check config/main.yaml)
    - Database accessible
    - All configuration files present
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


class TestRunner:
    def __init__(self):
        self.base_cmd = [sys.executable, "-m", "pytest"]
        self.failed_suites = []
    
    def run_command(self, cmd, description):
        """Run a pytest command and track results."""
        print(f"\n{'='*80}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'='*80}\n")
        
        result = subprocess.run(cmd)
        
        if result.returncode != 0:
            self.failed_suites.append(description)
            return False
        return True
    
    def run_unit_tests(self):
        """Run unit tests (fast, with mocks)."""
        cmd = self.base_cmd + [
            "tests/",
            "-v",
            "-m", "not local_heavy",
            "-k", "not (two_stage or heuristic_only or llm_only or full_stack)",
            "--tb=short"
        ]
        return self.run_command(cmd, "Unit Tests")
    
    def run_integration_tests(self):
        """Run integration tests (mocked LLM but real agents)."""
        cmd = self.base_cmd + [
            "tests/test_truth_validation.py",
            "-v",
            "-k", "two_stage or heuristic_only or llm_only",
            "--tb=short"
        ]
        return self.run_command(cmd, "Integration Tests (with mocks)")
    
    def run_smoke_tests(self):
        """Run quick smoke tests."""
        cmd = self.base_cmd + [
            "tests/",
            "-v",
            "-m", "smoke",
            "--tb=short"
        ]
        return self.run_command(cmd, "Smoke Tests")
    
    def run_local_heavy_tests(self):
        """Run full-stack local tests with real dependencies."""
        print(f"\n{'='*80}")
        print("Running: Full-Stack Local Tests (requires Ollama)")
        print(f"{'='*80}\n")
        
        # Check if Ollama is running
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code != 200:
                print("⚠ WARNING: Ollama not responding properly")
                print("  Run: ollama serve")
                return False
        except Exception as e:
            print(f"⚠ WARNING: Cannot connect to Ollama: {e}")
            print("  Run: ollama serve")
            return False
        
        # Use the full-stack test runner
        result = subprocess.run([
            sys.executable,
            "run_full_stack_test.py",
            "--no-server"  # Assume server will be started separately
        ])
        
        if result.returncode != 0:
            self.failed_suites.append("Full-Stack Local Tests")
            return False
        return True
    
    def run_specific_file(self, filepath):
        """Run tests from a specific file."""
        cmd = self.base_cmd + [
            filepath,
            "-v",
            "--tb=short"
        ]
        return self.run_command(cmd, f"Tests in {filepath}")
    
    def print_summary(self):
        """Print test run summary."""
        print(f"\n{'='*80}")
        print("TEST RUN SUMMARY")
        print(f"{'='*80}")
        
        if not self.failed_suites:
            print("✓ ALL TEST SUITES PASSED")
        else:
            print(f"✗ {len(self.failed_suites)} TEST SUITE(S) FAILED:")
            for suite in self.failed_suites:
                print(f"  - {suite}")
        
        print(f"{'='*80}\n")
        
        return len(self.failed_suites) == 0


def main():
    parser = argparse.ArgumentParser(
        description="Run TBCV tests",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--all", action="store_true",
                       help="Run ALL tests including local_heavy")
    parser.add_argument("--local-only", action="store_true",
                       help="Run only local_heavy tests")
    parser.add_argument("--unit", action="store_true",
                       help="Run only unit tests")
    parser.add_argument("--integration", action="store_true",
                       help="Run only integration tests")
    parser.add_argument("--quick", action="store_true",
                       help="Run only smoke tests")
    parser.add_argument("--file", type=str,
                       help="Run specific test file")
    parser.add_argument("--skip-local", action="store_true",
                       help="Skip local_heavy tests (default)")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    success = True
    
    # Determine what to run
    if args.file:
        # Run specific file
        success = runner.run_specific_file(args.file)
    
    elif args.local_only:
        # Only local/heavy tests
        success = runner.run_local_heavy_tests()
    
    elif args.unit:
        # Only unit tests
        success = runner.run_unit_tests()
    
    elif args.integration:
        # Only integration tests
        success = runner.run_integration_tests()
    
    elif args.quick:
        # Only smoke tests
        success = runner.run_smoke_tests()
    
    elif args.all:
        # Run everything
        print("Running complete test suite (unit + integration + local_heavy)")
        
        runner.run_smoke_tests()
        runner.run_unit_tests()
        runner.run_integration_tests()
        runner.run_local_heavy_tests()
        
        success = runner.print_summary()
    
    else:
        # Default: unit + integration, skip local_heavy
        print("Running standard test suite (unit + integration, skipping local_heavy)")
        print("Use --all to include local_heavy tests")
        print()
        
        runner.run_smoke_tests()
        runner.run_unit_tests()
        runner.run_integration_tests()
        
        success = runner.print_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
