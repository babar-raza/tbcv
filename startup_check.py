#!/usr/bin/env python3
"""
TBCV Startup Validation Script
Validates configuration and dependencies before starting the system
"""
import sys
from pathlib import Path
import json

def validate_dependencies():
    """Check if all required packages are installed"""
    print("Checking dependencies...")
    required = ['fastapi', 'sqlalchemy', 'pydantic', 'yaml']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"  ❌ Missing packages: {', '.join(missing)}")
        print("  Run: pip install -r requirements.txt")
        return False
    
    print("  ✅ All dependencies installed")
    return True

def validate_configuration():
    """Validate configuration files"""
    print("Checking configuration...")
    
    config_file = Path("config/main.yaml")
    if not config_file.exists():
        print(f"  ❌ Configuration file not found: {config_file}")
        return False
    
    print("  ✅ Configuration file exists")
    return True

def validate_truth_files():
    """Validate truth and rule files"""
    print("Checking truth and rule files...")
    
    truth_dir = Path("truth")
    rules_dir = Path("rules")
    
    if not truth_dir.exists():
        print(f"  ❌ Truth directory not found: {truth_dir}")
        return False
    
    if not rules_dir.exists():
        print(f"  ❌ Rules directory not found: {rules_dir}")
        return False
    
    # Check for at least one family
    truth_files = list(truth_dir.glob("*.json"))
    if not truth_files or (len(truth_files) == 1 and truth_files[0].name == "schema.json"):
        print("  ⚠️  No truth files found (except schema.json)")
        print("  At least one family should be defined (e.g., words.json)")
    else:
        families = [f.stem for f in truth_files if f.name != "schema.json"]
        print(f"  ✅ Found families: {', '.join(families)}")
    
    # Validate JSON syntax
    for truth_file in truth_files:
        if truth_file.name == "schema.json":
            continue
        try:
            with open(truth_file) as f:
                json.load(f)
        except json.JSONDecodeError as e:
            print(f"  ❌ Invalid JSON in {truth_file.name}: {e}")
            return False
    
    print("  ✅ Truth files validated")
    return True

def validate_database():
    """Check database connectivity"""
    print("Checking database...")
    
    try:
        from core.database import db_manager
        db_manager.initialize_database()
        print("  ✅ Database initialized")
        return True
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def main():
    """Run all validations"""
    print("=" * 60)
    print("TBCV Startup Validation")
    print("=" * 60)
    print()
    
    checks = [
        ("Dependencies", validate_dependencies),
        ("Configuration", validate_configuration),
        ("Truth Files", validate_truth_files),
        ("Database", validate_database),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
            print()
        except Exception as e:
            print(f"  ❌ {name} check failed with error: {e}")
            results.append((name, False))
            print()
    
    # Summary
    print("=" * 60)
    print("Validation Summary")
    print("=" * 60)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n✅ All checks passed! System is ready to start.")
        return 0
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
