#!/usr/bin/env python3
"""Smoke test runner for CLI and entry points."""
import os
import sys
import json
import subprocess
import time
from pathlib import Path

def test_main_py():
    """Test main.py execution."""
    result = {
        'entry_point': 'main.py',
        'status': 'unknown',
        'exit_code': None,
        'stdout': '',
        'stderr': '',
        'duration': 0
    }
    
    start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, 'main.py', '--help'],
            cwd='/tbcv',
            capture_output=True,
            text=True,
            timeout=10
        )
        result['exit_code'] = proc.returncode
        result['stdout'] = proc.stdout[:500]
        result['stderr'] = proc.stderr[:500]
        result['status'] = 'pass' if proc.returncode == 0 else 'fail'
    except subprocess.TimeoutExpired:
        result['status'] = 'timeout'
    except Exception as e:
        result['status'] = 'error'
        result['stderr'] = str(e)[:500]
    
    result['duration'] = time.time() - start
    return result

def test_main_module():
    """Test running as module."""
    result = {
        'entry_point': 'python -m tbcv',
        'status': 'unknown',
        'exit_code': None,
        'stdout': '',
        'stderr': '',
        'duration': 0
    }
    
    start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, '-m', 'tbcv', '--help'],
            cwd='/tbcv',
            capture_output=True,
            text=True,
            timeout=10
        )
        result['exit_code'] = proc.returncode
        result['stdout'] = proc.stdout[:500]
        result['stderr'] = proc.stderr[:500]
        result['status'] = 'pass' if proc.returncode == 0 else 'fail'
    except subprocess.TimeoutExpired:
        result['status'] = 'timeout'
    except Exception as e:
        result['status'] = 'error'
        result['stderr'] = str(e)[:500]
    
    result['duration'] = time.time() - start
    return result

def test_import_main_modules():
    """Test importing main modules."""
    modules_to_test = [
        'core.rule_manager',
        'agents.orchestrator',
        'cli.commands',
        'config.settings'
    ]
    
    results = []
    for module in modules_to_test:
        result = {
            'entry_point': f'import {module}',
            'status': 'unknown',
            'error': ''
        }
        
        try:
            # Mock missing dependencies
            import unittest.mock as mock
            with mock.patch.dict('sys.modules', {
                'fastapi': mock.MagicMock(),
                'uvicorn': mock.MagicMock(),
                'sqlalchemy': mock.MagicMock(),
                'ollama': mock.MagicMock(),
                'langchain': mock.MagicMock(),
                'chromadb': mock.MagicMock()
            }):
                __import__(module)
                result['status'] = 'pass'
        except ImportError as e:
            result['status'] = 'import_error'
            result['error'] = str(e)[:200]
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)[:200]
        
        results.append(result)
    
    return results

def main():
    """Run all smoke tests."""
    os.chdir('/tbcv')
    if '/tbcv' not in sys.path:
        sys.path.insert(0, '/tbcv')
    
    smoke_results = {
        'cli_tests': [],
        'import_tests': []
    }
    
    # Test CLI entry points
    print("Testing CLI entry points...")
    smoke_results['cli_tests'].append(test_main_py())
    smoke_results['cli_tests'].append(test_main_module())
    
    # Test imports
    print("Testing module imports...")
    smoke_results['import_tests'] = test_import_main_modules()
    
    # Generate report
    total_tests = len(smoke_results['cli_tests']) + len(smoke_results['import_tests'])
    passed = sum(1 for t in smoke_results['cli_tests'] + smoke_results['import_tests'] if t['status'] == 'pass')
    
    smoke_results['summary'] = {
        'total_tests': total_tests,
        'passed': passed,
        'failed': total_tests - passed
    }
    
    os.makedirs('/reports', exist_ok=True)
    with open('/reports/smoke.json', 'w') as f:
        json.dump(smoke_results, f, indent=2)
    
    print(f"\nSmoke Test Summary:")
    print(f"  Total: {total_tests}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total_tests - passed}")
    
    return smoke_results

if __name__ == '__main__':
    main()
