#!/usr/bin/env python
"""
Endpoint Checker Tool
Verifies API endpoints offline (static analysis) and online (running server).

Usage:
  python tools/endpoint_check.py --offline
  python tools/endpoint_check.py --online
"""

import sys
import json
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_offline():
    """Check endpoints offline by importing the API module."""
    print("Offline Endpoint Check")
    print("=" * 60)
    
    results = {
        "mode": "offline",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    try:
        # Import FastAPI app
        from api.server import app
        
        results["checks"]["import_success"] = {
            "status": "pass",
            "message": "Successfully imported API server module"
        }
        
        # Enumerate routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append({
                    "path": route.path,
                    "methods": list(route.methods),
                    "name": route.name
                })
        
        results["checks"]["routes_enumerated"] = {
            "status": "pass",
            "message": f"Found {len(routes)} routes",
            "routes": routes
        }
        
        # Check critical endpoints
        critical_endpoints = [
            ("/health", "GET"),
            ("/validations", "GET"),
            ("/validations/{validation_id}", "GET")
        ]
        
        found_endpoints = []
        missing_endpoints = []
        
        for path, method in critical_endpoints:
            found = any(r['path'] == path and method in r['methods'] for r in routes)
            if found:
                found_endpoints.append(f"{method} {path}")
            else:
                missing_endpoints.append(f"{method} {path}")
        
        results["checks"]["critical_endpoints"] = {
            "status": "pass" if not missing_endpoints else "fail",
            "found": found_endpoints,
            "missing": missing_endpoints
        }
        
        results["overall_status"] = "pass" if not missing_endpoints else "fail"
        
    except Exception as e:
        results["checks"]["import_failed"] = {
            "status": "fail",
            "error": str(e)
        }
        results["overall_status"] = "fail"
    
    # Save results
    output_path = Path('reports/endpoint_check/offline.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8', newline='\r\n') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    print(f"Overall status: {results['overall_status']}")
    
    return results['overall_status'] == 'pass'

def check_online():
    """Check endpoints online by making HTTP requests."""
    print("Online Endpoint Check")
    print("=" * 60)
    
    results = {
        "mode": "online",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    try:
        import requests
    except ImportError:
        print("Error: requests library not available")
        print("Install with: pip install requests")
        results["checks"]["requests_missing"] = {
            "status": "fail",
            "message": "requests library not installed"
        }
        results["overall_status"] = "fail"
        
        output_path = Path('reports/endpoint_check/online.json')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8', newline='\r\n') as f:
            json.dump(results, f, indent=2)
        return False
    
    base_url = "http://127.0.0.1:8080"
    
    # Wait for server to be ready
    print(f"Checking if server is running at {base_url}...")
    ready = False
    for i in range(10):
        try:
            response = requests.get(f"{base_url}/health/live", timeout=2)
            if response.status_code == 200:
                ready = True
                break
        except:
            pass
        time.sleep(1)
    
    if not ready:
        print("Error: Server is not responding")
        print("Ensure the API server is running:")
        print("  python main.py --mode api --host 127.0.0.1 --port 8080")
        
        results["checks"]["server_not_running"] = {
            "status": "fail",
            "message": "Server is not responding at http://127.0.0.1:8080"
        }
        results["overall_status"] = "fail"
        
        output_path = Path('reports/endpoint_check/online.json')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8', newline='\r\n') as f:
            json.dump(results, f, indent=2)
        return False
    
    print("Server is running, checking endpoints...\n")
    
    # Check /health
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        results["checks"]["health_endpoint"] = {
            "status": "pass" if response.status_code in [200, 503] else "fail",
            "status_code": response.status_code,
            "response": response.json()
        }
        print(f"✓ GET /health → {response.status_code}")
    except Exception as e:
        results["checks"]["health_endpoint"] = {
            "status": "fail",
            "error": str(e)
        }
        print(f"✗ GET /health → Error: {e}")
    
    # Check /validations
    try:
        response = requests.get(f"{base_url}/validations", timeout=5)
        data = response.json()
        results["checks"]["validations_list"] = {
            "status": "pass" if response.status_code == 200 else "fail",
            "status_code": response.status_code,
            "validations_count": len(data.get('validations', [])) if isinstance(data, dict) else len(data)
        }
        print(f"✓ GET /validations → {response.status_code} ({results['checks']['validations_list']['validations_count']} validations)")
        
        # If we have validations, check a detail page
        if isinstance(data, dict) and data.get('validations'):
            validation_id = data['validations'][0].get('id')
            if validation_id:
                try:
                    response = requests.get(f"{base_url}/validations/{validation_id}", timeout=5)
                    detail_data = response.json()
                    results["checks"]["validation_detail"] = {
                        "status": "pass" if response.status_code == 200 else "fail",
                        "status_code": response.status_code,
                        "has_recommendations": 'recommendations' in detail_data
                    }
                    print(f"✓ GET /validations/{validation_id} → {response.status_code}")
                except Exception as e:
                    results["checks"]["validation_detail"] = {
                        "status": "fail",
                        "error": str(e)
                    }
                    print(f"✗ GET /validations/{validation_id} → Error: {e}")
        
    except Exception as e:
        results["checks"]["validations_list"] = {
            "status": "fail",
            "error": str(e)
        }
        print(f"✗ GET /validations → Error: {e}")
    
    # Determine overall status
    all_passed = all(
        check.get("status") == "pass" 
        for check in results["checks"].values()
    )
    results["overall_status"] = "pass" if all_passed else "fail"
    
    # Save results
    output_path = Path('reports/endpoint_check/online.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8', newline='\r\n') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    print(f"Overall status: {results['overall_status']}")
    
    return results['overall_status'] == 'pass'

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Check API endpoints')
    parser.add_argument('--offline', action='store_true', help='Check endpoints offline (static analysis)')
    parser.add_argument('--online', action='store_true', help='Check endpoints online (requires running server)')
    
    args = parser.parse_args()
    
    if not args.offline and not args.online:
        print("Error: Specify either --offline or --online")
        parser.print_help()
        sys.exit(1)
    
    success = True
    
    if args.offline:
        if not check_offline():
            success = False
    
    if args.online:
        if not check_online():
            success = False
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
