#!/usr/bin/env python3
"""
Quick Test Script for TBCV
Tests basic functionality after setup
"""
import sys
from pathlib import Path

def test_imports():
    """Test that all core modules can be imported"""
    print("Testing imports...")
    try:
        from agents.truth_manager import TruthManagerAgent
        from agents.fuzzy_detector import FuzzyDetectorAgent
        from agents.content_validator import ContentValidatorAgent
        from agents.content_enhancer import ContentEnhancerAgent
        from agents.code_analyzer import CodeAnalyzerAgent
        from agents.orchestrator import OrchestratorAgent
        from core.database import db_manager
        from core.path_validator import is_safe_path
        print("  ✅ All core modules imported successfully")
        return True
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False

def test_database():
    """Test database initialization"""
    print("Testing database...")
    try:
        from core.database import db_manager
        db_manager.initialize_database()
        print("  ✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def test_path_validator():
    """Test path validation"""
    print("Testing path validator...")
    try:
        from core.path_validator import is_safe_path, sanitize_path
        
        # Test safe paths
        assert is_safe_path("./data/test.txt") == True
        assert is_safe_path("data/content/file.md") == True
        
        # Test unsafe paths
        assert is_safe_path("../../../etc/passwd") == False
        assert is_safe_path("/etc/passwd") == False
        assert is_safe_path("C:\\Windows\\System32\\config") == False
        
        print("  ✅ Path validator working correctly")
        return True
    except Exception as e:
        print(f"  ❌ Path validator error: {e}")
        return False

def test_truth_loading():
    """Test truth file loading"""
    print("Testing truth file loading...")
    try:
        import asyncio
        from agents.content_validator import ContentValidatorAgent
        
        validator = ContentValidatorAgent("test")
        
        # Test async method
        async def test_load():
            truth = await validator._load_truth_context("words")
            assert isinstance(truth, dict)
            return True
        
        result = asyncio.run(test_load())
        if result:
            print("  ✅ Truth loading working correctly")
            return True
    except Exception as e:
        print(f"  ❌ Truth loading error: {e}")
        return False

def test_mcp_server():
    """Test MCP server initialization"""
    print("Testing MCP server...")
    try:
        from svc.mcp_server import MCPServer
        server = MCPServer()
        
        # Test that methods exist
        assert hasattr(server, '_validate_folder')
        assert hasattr(server, '_approve')
        assert hasattr(server, '_reject')
        assert hasattr(server, '_enhance')
        
        print("  ✅ MCP server initialized successfully")
        return True
    except Exception as e:
        print(f"  ❌ MCP server error: {e}")
        return False

def main():
    print("=" * 60)
    print("TBCV Quick Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        ("Module Imports", test_imports),
        ("Database", test_database),
        ("Path Validator", test_path_validator),
        ("Truth Loading", test_truth_loading),
        ("MCP Server", test_mcp_server),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
            print()
        except Exception as e:
            print(f"  ❌ {name} failed with exception: {e}")
            results.append((name, False))
            print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = 0
    failed = 0
    for name, result in results:
        if result:
            print(f"✅ PASS: {name}")
            passed += 1
        else:
            print(f"❌ FAIL: {name}")
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n✅ All tests passed! System is working correctly.")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
