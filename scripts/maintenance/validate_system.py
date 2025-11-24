#!/usr/bin/env python3
"""
Comprehensive TBCV System Validation
Tests all critical components before deployment.
"""

import sys
import json
from pathlib import Path

def test_imports():
    """Test all critical imports."""
    print("="*70)
    print("1. TESTING IMPORTS")
    print("="*70)
    
    imports = {
        "core.config": ["get_settings"],
        "core.database": ["db_manager", "WorkflowState", "RecommendationStatus"],
        "core.logging": ["setup_logging", "get_logger"],
        "core.cache": ["cache_result"],
        "agents.base": ["BaseAgent", "AgentContract", "AgentCapability", "agent_registry"],
        "agents.truth_manager": ["TruthManagerAgent"],
        "agents.fuzzy_detector": ["FuzzyDetectorAgent"],
        "agents.content_validator": ["ContentValidatorAgent"],
        "agents.content_enhancer": ["ContentEnhancerAgent"],
        "agents.llm_validator": ["LLMValidatorAgent"],
        "agents.code_analyzer": ["CodeAnalyzerAgent"],
        "agents.orchestrator": ["OrchestratorAgent"],
        "agents.recommendation_agent": ["RecommendationAgent"],
        "agents.enhancement_agent": ["EnhancementAgent"],
    }
    
    failed = []
    for module, items in imports.items():
        try:
            mod = __import__(module, fromlist=items)
            for item in items:
                if not hasattr(mod, item):
                    failed.append(f"{module}.{item} not found")
            print(f"✓ {module}")
        except Exception as e:
            failed.append(f"{module}: {e}")
            print(f"✗ {module}: {e}")
    
    if failed:
        print(f"\n❌ {len(failed)} import(s) failed:")
        for f in failed:
            print(f"  - {f}")
        return False
    
    print(f"\n✅ All {len(imports)} modules imported successfully\n")
    return True

def test_agent_registration():
    """Test agent registration and contracts."""
    print("="*70)
    print("2. TESTING AGENT REGISTRATION")
    print("="*70)
    
    from agents.base import agent_registry
    from agents.recommendation_agent import RecommendationAgent
    from agents.truth_manager import TruthManagerAgent
    from agents.content_validator import ContentValidatorAgent
    
    agents = [
        ("recommendation", RecommendationAgent),
        ("truth", TruthManagerAgent),
        ("validator", ContentValidatorAgent),
    ]
    
    failed = []
    for name, AgentClass in agents:
        try:
            agent = AgentClass(f"test_{name}")
            contract = agent.get_contract()
            if not contract:
                failed.append(f"{name}: No contract returned")
            else:
                agent_registry.register_agent(agent)
                print(f"✓ {AgentClass.__name__} (contract: {contract.name})")
        except Exception as e:
            failed.append(f"{name}: {e}")
            print(f"✗ {AgentClass.__name__}: {e}")
    
    if failed:
        print(f"\n❌ {len(failed)} agent(s) failed:")
        for f in failed:
            print(f"  - {f}")
        return False
    
    print(f"\n✅ All {len(agents)} agents registered successfully\n")
    return True

def test_truth_files():
    """Test truth file loading."""
    print("="*70)
    print("3. TESTING TRUTH FILES")
    print("="*70)
    
    truth_files = [
        "truth/words.json",
        "truth/aspose_words_plugins_truth.json",
        "truth/words_combinations.json",
        "truth/aspose_words_plugins_combinations.json",
    ]
    
    failed = []
    for file_path in truth_files:
        path = Path(file_path)
        if not path.exists():
            failed.append(f"{file_path}: File not found")
            print(f"✗ {file_path}: Not found")
            continue
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Validate structure
            if "plugins" in data or "combinations" in data or "suites" in data:
                count = len(data.get("plugins", [])) + len(data.get("combinations", [])) + len(data.get("suites", []))
                print(f"✓ {file_path} ({count} entries)")
            else:
                failed.append(f"{file_path}: Invalid structure")
                print(f"✗ {file_path}: Invalid structure")
        except json.JSONDecodeError as e:
            failed.append(f"{file_path}: Invalid JSON - {e}")
            print(f"✗ {file_path}: Invalid JSON")
        except Exception as e:
            failed.append(f"{file_path}: {e}")
            print(f"✗ {file_path}: {e}")
    
    if failed:
        print(f"\n❌ {len(failed)} truth file(s) failed:")
        for f in failed:
            print(f"  - {f}")
        return False
    
    print(f"\n✅ All {len(truth_files)} truth files validated\n")
    return True

def test_configuration():
    """Test configuration loading."""
    print("="*70)
    print("4. TESTING CONFIGURATION")
    print("="*70)
    
    config_files = [
        ("config/main.yaml", "yaml"),
        ("config/agent.yaml", "yaml"),
        ("config/perf.json", "json"),
        ("config/tone.json", "json"),
    ]
    
    failed = []
    for file_path, file_type in config_files:
        path = Path(file_path)
        if not path.exists():
            failed.append(f"{file_path}: Not found")
            print(f"✗ {file_path}: Not found")
            continue
        
        try:
            if file_type == "json":
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"✓ {file_path} ({len(data)} keys)")
            elif file_type == "yaml":
                import yaml
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    print(f"✓ {file_path} ({len(data)} sections)")
        except Exception as e:
            failed.append(f"{file_path}: {e}")
            print(f"✗ {file_path}: {e}")
    
    if failed:
        print(f"\n❌ {len(failed)} config file(s) failed:")
        for f in failed:
            print(f"  - {f}")
        return False
    
    print(f"\n✅ All {len(config_files)} config files loaded\n")
    return True

def test_database():
    """Test database operations."""
    print("="*70)
    print("5. TESTING DATABASE")
    print("="*70)
    
    try:
        from core.database import db_manager, SQLALCHEMY_AVAILABLE
        
        if not SQLALCHEMY_AVAILABLE:
            print("⚠ SQLAlchemy not available - using in-memory fallback")
            print("  Install with: pip install sqlalchemy==2.0.23")
            return True
        
        # Test initialization
        db_manager.init_database()
        print("✓ Database initialized")
        
        # Test connection
        if db_manager.is_connected():
            print("✓ Database connected")
        else:
            print("✗ Database not connected")
            return False
        
        # Test schema
        if db_manager.has_required_schema():
            print("✓ Database schema valid")
        else:
            print("✗ Database schema incomplete")
            return False
        
        print("\n✅ Database operations successful\n")
        return True
        
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False

def test_api_imports():
    """Test API server imports."""
    print("="*70)
    print("6. TESTING API SERVER")
    print("="*70)
    
    try:
        from api.server import app
        print("✓ API server imported")
        
        # Count endpoints
        routes = [r for r in app.routes if hasattr(r, 'path')]
        print(f"✓ {len(routes)} routes registered")
        
        # Check critical endpoints
        critical = [
            "/health/live",
            "/health/ready",
            "/workflows/validate-directory",
            "/api/validate",
            "/admin/status",
        ]
        
        paths = [r.path for r in routes if hasattr(r, 'path')]
        missing = [ep for ep in critical if ep not in paths]
        
        if missing:
            print(f"✗ Missing endpoints: {missing}")
            return False
        
        print(f"✓ All {len(critical)} critical endpoints present")
        print("\n✅ API server ready\n")
        return True
        
    except Exception as e:
        print(f"✗ API server error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("TBCV COMPREHENSIVE SYSTEM VALIDATION")
    print("="*70 + "\n")
    
    results = {
        "Imports": test_imports(),
        "Agent Registration": test_agent_registration(),
        "Truth Files": test_truth_files(),
        "Configuration": test_configuration(),
        "Database": test_database(),
        "API Server": test_api_imports(),
    }
    
    print("="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test}")
    
    print("="*70)
    
    if all(results.values()):
        print("\n🎉 ALL VALIDATIONS PASSED - System is production ready!\n")
        return 0
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"\n❌ {len(failed)} validation(s) failed:")
        for test in failed:
            print(f"  - {test}")
        print("\nPlease fix the issues above before deployment.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
