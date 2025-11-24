#!/usr/bin/env python3
"""Quick endpoint verification - tests critical endpoints only."""

import requests
import json

BASE = "http://localhost:8080"

def test(method, path, data=None, name=""):
    """Test single endpoint."""
    try:
        url = f"{BASE}{path}"
        if method == "GET":
            r = requests.get(url, timeout=3)
        else:
            r = requests.post(url, json=data, timeout=3)
        
        status = "✓" if r.status_code < 400 else "✗"
        print(f"{status} {method:4} {path:40} -> {r.status_code} {name}")
        if r.status_code >= 400:
            print(f"     {r.text[:100]}")
        return r.status_code < 400
    except Exception as e:
        print(f"✗ {method:4} {path:40} -> ERROR: {e}")
        return False

print("\n=== TBCV Quick Endpoint Test ===\n")

# Test server
try:
    r = requests.get(f"{BASE}/health/live", timeout=2)
    print(f"✓ Server is running at {BASE}\n")
except:
    print(f"✗ Cannot connect to {BASE}")
    print("   Start server: python main.py --mode api\n")
    exit(1)

# Core endpoints
print("Core:")
test("GET", "/", name="Root")
test("GET", "/health/live", name="Health")
test("GET", "/status", name="Status")

print("\nAgents:")
test("GET", "/agents", name="List agents")

print("\nValidation:")
test("POST", "/api/validate", {
    "content": "Document doc = new Document();",
    "file_path": "test.md",
    "family": "words"
}, name="Validate content")

test("POST", "/agents/validate", {
    "content": "test",
    "file_path": "test.md",
    "family": "words"
}, name="Validate via agents")

print("\nWorkflows:")
test("GET", "/workflows", name="List workflows")

test("POST", "/workflows/validate-directory", {
    "directory_path": "./test",
    "file_pattern": "*.md",
    "workflow_type": "validate_file",
    "max_workers": 2,
    "family": "words"
}, name="Start workflow")

print("\nAdmin:")
test("GET", "/admin/status", name="Admin status")
test("GET", "/admin/cache/stats", name="Cache stats")

print("\n=== Test Complete ===\n")
