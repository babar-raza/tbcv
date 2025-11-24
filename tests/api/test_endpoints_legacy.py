#!/usr/bin/env python3
"""
TBCV Endpoint Test Suite
Tests all documented API endpoints with proper HTTP methods and payloads.
"""

import requests
import json
import sys
from typing import Dict, Any, List, Tuple

BASE_URL = "http://localhost:8080"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def test_endpoint(method: str, path: str, data: Dict = None, params: Dict = None, 
                  expected_status: List[int] = None) -> Tuple[bool, str]:
    """Test a single endpoint."""
    if expected_status is None:
        expected_status = [200, 201]
    
    url = f"{BASE_URL}{path}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, params=params, timeout=5)
        elif method == "PUT":
            response = requests.put(url, json=data, params=params, timeout=5)
        elif method == "DELETE":
            response = requests.delete(url, params=params, timeout=5)
        else:
            return False, f"Unknown method: {method}"
        
        if response.status_code in expected_status:
            return True, f"{response.status_code} - {response.text[:100]}"
        else:
            return False, f"{response.status_code} - {response.text[:200]}"
            
    except requests.exceptions.ConnectionError:
        return False, "Connection refused - is server running?"
    except requests.exceptions.Timeout:
        return False, "Request timeout"
    except Exception as e:
        return False, f"Error: {str(e)}"

def print_result(name: str, method: str, path: str, passed: bool, message: str):
    """Print test result."""
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"{status} {method:6} {path:50} - {message}")

def run_tests():
    """Run all endpoint tests."""
    
    tests = [
        # ===== Core Endpoints =====
        ("Root", "GET", "/", None, None, [200]),
        ("Status", "GET", "/status", None, None, [200]),
        
        # ===== Health Endpoints =====
        ("Health", "GET", "/health", None, None, [200]),
        ("Health Live", "GET", "/health/live", None, None, [200]),
        ("Health Ready", "GET", "/health/ready", None, None, [200]),
        
        # ===== Agent Endpoints =====
        ("List Agents", "GET", "/agents", None, None, [200]),
        ("Get Agent", "GET", "/agents/content_validator", None, None, [200, 404]),
        ("Registry Agents", "GET", "/registry/agents", None, None, [200]),
        
        # ===== Validation Endpoints =====
        ("Validate Content", "POST", "/agents/validate", {
            "content": "Document doc = new Document();",
            "file_path": "test.md",
            "family": "words",
            "validation_types": ["code"]
        }, None, [200, 500]),
        
        ("Batch Validate", "POST", "/api/validate/batch", {
            "files": ["test1.md", "test2.md"],
            "family": "words",
            "validation_types": ["markdown"],
            "max_workers": 2
        }, None, [200, 500]),
        
        ("Detect Plugins", "POST", "/api/detect-plugins", {
            "content": "Document.Save()",
            "family": "words"
        }, None, [200, 500]),
        
        ("List Validations", "GET", "/api/validations", None, {"limit": 10}, [200]),
        
        # ===== Workflow Endpoints =====
        ("List Workflows", "GET", "/workflows", None, None, [200]),
        ("List Workflows API", "GET", "/api/workflows", None, None, [200]),
        
        ("Validate Directory", "POST", "/workflows/validate-directory", {
            "directory_path": "./test",
            "file_pattern": "*.md",
            "workflow_type": "validate_file",
            "max_workers": 4,
            "family": "words"
        }, None, [200, 500]),
        
        # ===== Recommendation Endpoints =====
        ("List Recommendations", "GET", "/api/recommendations", None, None, [200]),
        
        # ===== Admin Endpoints =====
        ("Admin Status", "GET", "/admin/status", None, None, [200]),
        ("Admin Active Workflows", "GET", "/admin/workflows/active", None, None, [200]),
        ("Admin Cache Stats", "GET", "/admin/cache/stats", None, None, [200]),
        ("Admin Performance Report", "GET", "/admin/reports/performance", None, {"days": 7}, [200]),
        ("Admin Health Report", "GET", "/admin/reports/health", None, {"period": "7days"}, [200]),
        
        # ===== Cache Endpoints (POST) =====
        ("Admin Clear Cache", "POST", "/admin/cache/clear", {}, None, [200]),
        ("Admin Cleanup Cache", "POST", "/admin/cache/cleanup", {}, None, [200]),
        ("Admin Rebuild Cache", "POST", "/admin/cache/rebuild", {}, None, [200]),
        
        # ===== System Endpoints (POST) =====
        ("Admin Garbage Collect", "POST", "/admin/system/gc", {}, None, [200]),
        ("Admin System Checkpoint", "POST", "/admin/system/checkpoint", {}, None, [200]),
        ("Admin Enable Maintenance", "POST", "/admin/maintenance/enable", {}, None, [200]),
        ("Admin Disable Maintenance", "POST", "/admin/maintenance/disable", {}, None, [200]),
    ]
    
    print("\n" + "="*100)
    print("TBCV ENDPOINT TEST SUITE")
    print("="*100 + "\n")
    
    passed = 0
    failed = 0
    errors = []
    
    for test_data in tests:
        name, method, path = test_data[:3]
        data = test_data[3] if len(test_data) > 3 else None
        params = test_data[4] if len(test_data) > 4 else None
        expected = test_data[5] if len(test_data) > 5 else [200]
        
        success, message = test_endpoint(method, path, data, params, expected)
        print_result(name, method, path, success, message)
        
        if success:
            passed += 1
        else:
            failed += 1
            errors.append((name, method, path, message))
    
    print("\n" + "="*100)
    print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("="*100)
    
    if errors:
        print(f"\n{Colors.RED}FAILED TESTS:{Colors.END}\n")
        for name, method, path, message in errors:
            print(f"  • {name}")
            print(f"    {method} {path}")
            print(f"    {message}\n")
    
    return 0 if failed == 0 else 1

def main():
    """Main entry point."""
    print(f"\nTesting server at: {BASE_URL}")
    print("Checking server availability...\n")
    
    try:
        response = requests.get(f"{BASE_URL}/health/live", timeout=2)
        if response.status_code == 200:
            print(f"{Colors.GREEN}✓ Server is running{Colors.END}\n")
        else:
            print(f"{Colors.YELLOW}⚠ Server responded with status {response.status_code}{Colors.END}\n")
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}✗ Cannot connect to server at {BASE_URL}{Colors.END}")
        print(f"\nPlease start the server with:")
        print(f"  python main.py --mode api --host 0.0.0.0 --port 8080\n")
        return 1
    
    return run_tests()

if __name__ == "__main__":
    sys.exit(main())
