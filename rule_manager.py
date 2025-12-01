# file: rule_manager.py
"""
Top-level re-export of core.rule_manager for convenience imports.

This module allows:
    import rule_manager
    from rule_manager import RuleManager

Instead of requiring:
    from core.rule_manager import RuleManager
"""

from core.rule_manager import RuleManager, rule_manager

__all__ = ['RuleManager', 'rule_manager']
