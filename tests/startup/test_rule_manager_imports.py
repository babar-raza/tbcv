# file: tests\startup\test_rule_manager_imports.py
"""
Test that rule_manager imports work correctly.
"""

import pytest

def test_import_rule_manager_top_level():
    """Test that top-level rule_manager import works."""
    import rule_manager
    assert hasattr(rule_manager, 'RuleManager')
    assert hasattr(rule_manager, 'rule_manager')
    print(f"rule_manager OK: {rule_manager.__file__}")


def test_import_rule_manager_from_top_level():
    """Test importing RuleManager from top-level."""
    from rule_manager import RuleManager
    rm = RuleManager()
    assert hasattr(rm, 'get_family_rules')
    print("RuleManager from top-level OK")

def test_import_rule_manager_from_core():
    """Test importing from core."""
    from core.rule_manager import rule_manager, RuleManager
    rm = RuleManager()
    rules = rm.get_family_rules("words")
    assert rules.family == "words"
    print("rule_manager from core OK")

def test_smoke_api_import():
    """Test that the API can import without errors."""
    try:
        # This will fail if there are import issues during module loading
        from api.server import app
        print("API import smoke test OK")
    except ImportError as e:
        print(f"API import failed: {e}")
        raise

if __name__ == "__main__":
    test_import_rule_manager_top_level()
    test_import_rule_manager_from_top_level()
    test_import_rule_manager_from_core()
    test_smoke_api_import()
    print("All import tests passed!")
