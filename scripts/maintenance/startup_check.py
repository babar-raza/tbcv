#!/usr/bin/env python3
"""
TBCV System Startup Validation
Runs comprehensive checks before system startup to ensure all components are ready.
"""

import sys
import json
from pathlib import Path
from typing import Tuple, Dict, Any, List

def check_python_version() -> Tuple[bool, str]:
    """Check Python version is 3.9+."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor} (requires 3.9+)"

def check_directories() -> Tuple[bool, List[str]]:
    """Check required directories exist."""
    required_dirs = [
        "agents", "api", "cli", "core", "config", "templates",
        "truth", "rules", "prompts", "data", "data/logs", "data/cache"
    ]
    missing = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            missing.append(f"Created: {dir_path}")
    
    return True, missing if missing else ["All directories exist"]

def check_truth_files() -> Tuple[bool, List[str]]:
    """Check truth files exist and are valid JSON."""
    required_files = [
        "truth/words.json",
        "truth/aspose_words_plugins_truth.json",
        "truth/words_combinations.json",
        "truth/aspose_words_plugins_combinations.json"
    ]
    issues = []
    
    for file_path in required_files:
        path = Path(file_path)
        if not path.exists():
            issues.append(f"MISSING: {file_path}")
            continue
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    issues.append(f"INVALID: {file_path} - not a JSON object")
        except json.JSONDecodeError as e:
            issues.append(f"INVALID JSON: {file_path} - {e}")
        except Exception as e:
            issues.append(f"ERROR: {file_path} - {e}")
    
    if issues:
        return False, issues
    return True, [f"Validated {len(required_files)} truth files"]

def check_config_files() -> Tuple[bool, List[str]]:
    """Check configuration files exist and are valid."""
    config_files = {
        "config/main.yaml": "yaml",
        "config/agent.yaml": "yaml",
        "config/perf.json": "json",
        "config/tone.json": "json"
    }
    issues = []
    
    for file_path, file_type in config_files.items():
        path = Path(file_path)
        if not path.exists():
            issues.append(f"MISSING: {file_path}")
            continue
        
        try:
            if file_type == "json":
                with open(path, 'r', encoding='utf-8') as f:
                    json.load(f)
            elif file_type == "yaml":
                import yaml
                with open(path, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
        except Exception as e:
            issues.append(f"INVALID: {file_path} - {e}")
    
    if issues:
        return False, issues
    return True, [f"Validated {len(config_files)} config files"]

def check_core_imports() -> Tuple[bool, str]:
    """Check core modules can be imported."""
    try:
        import core.config
        import core.database
        import core.logging
        import agents.base
        return True, "Core imports successful"
    except ImportError as e:
        return False, f"Import error: {e}"

def check_database() -> Tuple[bool, str]:
    """Check database can be initialized."""
    try:
        from core.database import db_manager, SQLALCHEMY_AVAILABLE
        
        if not SQLALCHEMY_AVAILABLE:
            return True, "Database will use in-memory fallback (install SQLAlchemy for persistence)"
        
        db_manager.init_database()
        if db_manager.is_connected():
            return True, "Database initialized and connected"
        return False, "Database not connected"
    except Exception as e:
        return False, f"Database error: {e}"

def run_all_checks() -> Dict[str, Any]:
    """Run all startup checks."""
    results = {}
    all_passed = True
    
    # Python version
    passed, msg = check_python_version()
    results["python_version"] = {"passed": passed, "message": msg}
    all_passed = all_passed and passed
    
    # Directories
    passed, msgs = check_directories()
    results["directories"] = {"passed": passed, "messages": msgs}
    all_passed = all_passed and passed
    
    # Truth files
    passed, msgs = check_truth_files()
    results["truth_files"] = {"passed": passed, "messages": msgs}
    all_passed = all_passed and passed
    
    # Config files
    passed, msgs = check_config_files()
    results["config_files"] = {"passed": passed, "messages": msgs}
    all_passed = all_passed and passed
    
    # Core imports
    passed, msg = check_core_imports()
    results["core_imports"] = {"passed": passed, "message": msg}
    all_passed = all_passed and passed
    
    # Database
    passed, msg = check_database()
    results["database"] = {"passed": passed, "message": msg}
    all_passed = all_passed and passed
    
    results["overall"] = all_passed
    return results

def print_results(results: Dict[str, Any]) -> None:
    """Print results in a readable format."""
    print("\n" + "="*70)
    print("TBCV STARTUP VALIDATION")
    print("="*70 + "\n")
    
    for check_name, result in results.items():
        if check_name == "overall":
            continue
        
        status = "✓" if result.get("passed", False) else "✗"
        print(f"{status} {check_name.replace('_', ' ').title()}")
        
        if "message" in result:
            print(f"  {result['message']}")
        if "messages" in result:
            for msg in result["messages"]:
                print(f"  {msg}")
        print()
    
    print("="*70)
    if results["overall"]:
        print("✓ ALL CHECKS PASSED - System ready to start")
    else:
        print("✗ SOME CHECKS FAILED - Please fix issues before starting")
    print("="*70 + "\n")

def main():
    """Main entry point."""
    results = run_all_checks()
    print_results(results)
    
    if not results["overall"]:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
