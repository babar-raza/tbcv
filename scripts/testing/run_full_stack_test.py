#!/usr/bin/env python3
"""
Full-stack test runner with server management.

Usage:
    python run_full_stack_test.py                    # Run all full-stack tests
    python run_full_stack_test.py path/to/file.md    # Test specific file
    python run_full_stack_test.py path/to/folder/    # Test folder
    python run_full_stack_test.py --server-only      # Start server and wait
    python run_full_stack_test.py --no-server        # Run tests without starting server

Environment variables:
    TEST_FILE=/path/to/file.md                      # Override test file
    TEST_DIR=/path/to/dir                           # Override test directory
    SKIP_SERVER_START=1                             # Don't start server (assume running)
    KEEP_SERVER_RUNNING=1                           # Don't stop server after tests
"""

import sys
import os
import time
import signal
import subprocess
import argparse
from pathlib import Path


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")


def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")


def check_ollama():
    """Check if Ollama is running."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print_success(f"Ollama running with {len(models)} model(s)")
            return True
        return False
    except Exception as e:
        print_error(f"Ollama not accessible: {e}")
        return False


def check_dependencies():
    """Check all required dependencies."""
    print_header("Checking dependencies")
    
    all_good = True
    
    # Check Ollama
    if not check_ollama():
        print_warning("Run: ollama serve")
        all_good = False
    
    # Check database
    db_path = Path("data/tbcv.db")
    if db_path.exists():
        print_success(f"Database found: {db_path}")
    else:
        print_warning(f"Database not found at {db_path} (will be created)")
    
    # Check config
    config_path = Path("config/main.yaml")
    if config_path.exists():
        print_success(f"Config found: {config_path}")
    else:
        print_error(f"Config not found: {config_path}")
        all_good = False
    
    # Check truth files
    truth_path = Path("truth")
    if truth_path.exists():
        truth_files = list(truth_path.glob("*.json"))
        print_success(f"Truth files: {len(truth_files)} found")
    else:
        print_warning(f"Truth directory not found: {truth_path}")
    
    return all_good


def start_server():
    """Start the API server."""
    print_header("Starting API server")
    
    try:
        # Start server in background
        process = subprocess.Popen(
            [sys.executable, "main.py", "--mode", "api"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to be ready
        print("Waiting for server to start", end="", flush=True)
        max_wait = 30
        for i in range(max_wait):
            time.sleep(1)
            print(".", end="", flush=True)
            try:
                import requests
                response = requests.get("http://localhost:8080/health", timeout=2)
                if response.status_code == 200:
                    print()
                    print_success("Server started at http://localhost:8080")
                    return process
            except Exception:
                continue
        
        print()
        print_error("Server failed to start within timeout")
        process.kill()
        return None
        
    except Exception as e:
        print_error(f"Failed to start server: {e}")
        return None


def stop_server(process):
    """Stop the API server."""
    if process:
        print_header("Stopping server")
        try:
            process.terminate()
            process.wait(timeout=5)
            print_success("Server stopped")
        except subprocess.TimeoutExpired:
            process.kill()
            print_warning("Server forcefully killed")
        except Exception as e:
            print_error(f"Error stopping server: {e}")


def run_tests(test_path=None):
    """Run the full-stack tests."""
    print_header("Running full-stack tests")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_full_stack_local.py",
        "-v", "-s",
        "--local-heavy",
        "--tb=short"
    ]
    
    # Set environment variables for test paths
    env = os.environ.copy()
    if test_path:
        test_path_obj = Path(test_path)
        if test_path_obj.is_file():
            env["TEST_FILE"] = str(test_path_obj.absolute())
            cmd.extend(["-k", "single_file"])
        elif test_path_obj.is_dir():
            env["TEST_DIR"] = str(test_path_obj.absolute())
            cmd.extend(["-k", "directory"])
    
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, env=env)
    
    if result.returncode == 0:
        print_success("All tests passed")
        return True
    else:
        print_error("Some tests failed")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run full-stack TBCV tests")
    parser.add_argument("path", nargs="?", help="Path to file or directory to test")
    parser.add_argument("--server-only", action="store_true", 
                       help="Start server and wait (don't run tests)")
    parser.add_argument("--no-server", action="store_true",
                       help="Run tests without starting server")
    parser.add_argument("--skip-checks", action="store_true",
                       help="Skip dependency checks")
    
    args = parser.parse_args()
    
    print_header("TBCV Full-Stack Test Runner")
    
    # Check dependencies
    if not args.skip_checks:
        if not check_dependencies():
            print_error("Dependency checks failed")
            print_warning("Use --skip-checks to run anyway")
            return 1
    
    # Determine if we should manage the server
    skip_server = args.no_server or os.getenv("SKIP_SERVER_START") == "1"
    keep_running = args.server_only or os.getenv("KEEP_SERVER_RUNNING") == "1"
    
    server_process = None
    
    try:
        # Start server if needed
        if not skip_server:
            server_process = start_server()
            if not server_process:
                print_error("Cannot proceed without server")
                return 1
        else:
            print_warning("Assuming server is already running at http://localhost:8080")
        
        # Run tests or wait
        if args.server_only:
            print_success("Server running. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nReceived interrupt signal")
        else:
            success = run_tests(args.path)
            
            if success:
                print_header("SUCCESS - Full-stack tests completed")
                print(f"Dashboard: http://localhost:8080/")
                print(f"Validations: http://localhost:8080/validations")
                
                if keep_running:
                    print_success("Server still running. Press Ctrl+C to stop.")
                    try:
                        while True:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        print("\nReceived interrupt signal")
                
                return 0
            else:
                print_header("FAILURE - Some tests failed")
                return 1
    
    finally:
        # Cleanup
        if server_process and not keep_running:
            stop_server(server_process)


if __name__ == "__main__":
    sys.exit(main())
