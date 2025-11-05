#!/usr/bin/env python3
"""Generate health report for the repository."""
import os
import sys
import json
import importlib
import ast
from pathlib import Path
from collections import defaultdict

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    return {
        'version': f"{version.major}.{version.minor}.{version.micro}",
        'compatible': version.major == 3 and version.minor >= 11
    }

def scan_imports(root_dir):
    """Scan all Python files for imports."""
    imports = defaultdict(list)
    missing_modules = set()
    circular_imports = []
    
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in {'__pycache__', '.git', 'node_modules', '.pytest_cache'}]
        
        for fname in files:
            if not fname.endswith('.py'):
                continue
                
            filepath = os.path.join(root, fname)
            rel_path = os.path.relpath(filepath, root_dir)
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    tree = ast.parse(f.read(), filename=rel_path)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports[rel_path].append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports[rel_path].append(node.module)
            except SyntaxError as e:
                pass
            except Exception as e:
                pass
    
    # Check for missing standard library and third-party modules
    for file, file_imports in imports.items():
        for imp in file_imports:
            base_module = imp.split('.')[0]
            # Skip relative imports and known internal modules
            if base_module in {'api', 'agents', 'core', 'cli', 'tools', 'svc', 'config', 'data', 'tests'}:
                continue
            
            try:
                importlib.import_module(base_module)
            except ImportError:
                missing_modules.add(base_module)
            except Exception:
                pass
    
    return {
        'import_graph': dict(imports),
        'missing_modules': sorted(list(missing_modules)),
        'circular_imports': circular_imports
    }

def check_file_structure(root_dir):
    """Check for missing critical files."""
    critical_files = [
        'pyproject.toml',
        'requirements.txt',
        'README.md',
        '__init__.py',
        '__main__.py'
    ]
    
    missing = []
    present = []
    
    for fname in critical_files:
        fpath = os.path.join(root_dir, fname)
        if os.path.exists(fpath):
            present.append(fname)
        else:
            missing.append(fname)
    
    return {
        'present': present,
        'missing': missing
    }

def generate_health_report(root_dir):
    """Generate complete health report."""
    report = {
        'python_version': check_python_version(),
        'file_structure': check_file_structure(root_dir),
        'imports': scan_imports(root_dir)
    }
    
    # Overall health
    issues = []
    if not report['python_version']['compatible']:
        issues.append('Python version incompatible')
    if report['file_structure']['missing']:
        issues.append(f"Missing files: {', '.join(report['file_structure']['missing'])}")
    if report['imports']['missing_modules']:
        issues.append(f"Missing modules: {', '.join(report['imports']['missing_modules'][:5])}")
    
    report['health_status'] = 'PASS' if not issues else 'ISSUES'
    report['issues'] = issues
    
    return report

if __name__ == '__main__':
    root = '/tbcv'
    report = generate_health_report(root)
    
    os.makedirs('/reports', exist_ok=True)
    with open('/reports/health.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Health status: {report['health_status']}")
    if report['issues']:
        for issue in report['issues']:
            print(f"  - {issue}")
