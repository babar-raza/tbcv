"""
Contract tests for TBCV API stability.

These tests verify that critical public interfaces remain stable across refactorings.
They helped catch API drift that caused 147+ test failures.

Test files:
- test_database_contract.py: DatabaseManager interface
- test_cache_contract.py: CacheManager interface
- test_agent_contract.py: BaseAgent interface
"""
