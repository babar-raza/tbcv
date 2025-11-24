# file: tbcv/core/startup_checks.py
"""
Startup self-checks for TBCV system.

Verifies:
- Ollama connectivity and model availability
- Database connectivity and schema status
- Required directories are writable
- Agent smoke tests
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone

from core.logging import get_logger

logger = get_logger(__name__)


class StartupCheckResult:
    """Result of a single startup check."""
    
    def __init__(self, name: str, passed: bool, message: str, critical: bool = True):
        self.name = name
        self.passed = passed
        self.message = message
        self.critical = critical
        self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "critical": self.critical,
            "timestamp": self.timestamp.isoformat(),
        }


class StartupChecker:
    """Performs comprehensive startup checks for TBCV system."""
    
    def __init__(self):
        self.results: List[StartupCheckResult] = []
        self.critical_failures = 0
    
    def check_ollama_connectivity(self) -> StartupCheckResult:
        """Verify Ollama is reachable."""
        try:
            from core.ollama import OllamaClient
            
            client = OllamaClient()
            # Try to ping Ollama
            if client.is_available():
                return StartupCheckResult(
                    "Ollama Connectivity",
                    True,
                    "Ollama is reachable",
                    critical=False
                )
            else:
                return StartupCheckResult(
                    "Ollama Connectivity",
                    False,
                    "Ollama is not responding. LLM-based validation features will be disabled.",
                    critical=False
                )
        except Exception as e:
            return StartupCheckResult(
                "Ollama Connectivity",
                False,
                f"Failed to connect to Ollama: {e}. LLM-based validation features will be disabled.",
                critical=False
            )
    
    def check_ollama_models(self, required_models: List[str] = None) -> StartupCheckResult:
        """Verify required models are available in Ollama."""
        if required_models is None:
            required_models = ["llama2", "mistral"]  # Default models
        
        try:
            from core.ollama import OllamaClient
            
            client = OllamaClient()
            available_models = client.list_models()
            
            missing_models = []
            for model in required_models:
                if not any(model.lower() in m.lower() for m in available_models):
                    missing_models.append(model)
            
            if not missing_models:
                return StartupCheckResult(
                    "Ollama Models",
                    True,
                    f"All required models available: {', '.join(required_models)}",
                    critical=False
                )
            else:
                return StartupCheckResult(
                    "Ollama Models",
                    False,
                    f"Missing required models: {', '.join(missing_models)}. Install with: ollama pull <model>",
                    critical=False
                )
        except Exception as e:
            return StartupCheckResult(
                "Ollama Models",
                False,
                f"Failed to check models: {e}",
                critical=False
            )
    
    def check_database_connectivity(self) -> StartupCheckResult:
        """Verify database is accessible."""
        try:
            from core.database import db_manager
            
            if db_manager.is_connected():
                return StartupCheckResult(
                    "Database Connectivity",
                    True,
                    "Database is connected",
                    critical=True
                )
            else:
                return StartupCheckResult(
                    "Database Connectivity",
                    False,
                    "Database is not connected. Check database configuration.",
                    critical=True
                )
        except Exception as e:
            return StartupCheckResult(
                "Database Connectivity",
                False,
                f"Failed to connect to database: {e}",
                critical=True
            )
    
    def check_database_schema(self) -> StartupCheckResult:
        """Verify database schema is present and up-to-date."""
        try:
            from core.database import db_manager
            
            # Try to initialize database (idempotent)
            db_manager.init_database()
            
            if db_manager.has_required_schema():
                return StartupCheckResult(
                    "Database Schema",
                    True,
                    "Database schema is valid and up-to-date",
                    critical=True
                )
            else:
                return StartupCheckResult(
                    "Database Schema",
                    False,
                    "Database schema is missing or incomplete. Run migrations.",
                    critical=True
                )
        except Exception as e:
            return StartupCheckResult(
                "Database Schema",
                False,
                f"Failed to verify schema: {e}",
                critical=True
            )
    
    def check_writable_paths(self, paths: List[str] = None) -> StartupCheckResult:
        """Verify required paths are writable."""
        if paths is None:
            paths = ["reports", "output", "jobs", "logs"]
        
        missing_paths = []
        readonly_paths = []
        
        for path_str in paths:
            path = Path(path_str)
            
            # Create directory if it doesn't exist
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                missing_paths.append(f"{path_str} ({e})")
                continue
            
            # Test if writable
            test_file = path / f".write_test_{os.getpid()}"
            try:
                test_file.write_text("test")
                test_file.unlink()
            except Exception as e:
                readonly_paths.append(f"{path_str} ({e})")
        
        if not missing_paths and not readonly_paths:
            return StartupCheckResult(
                "Writable Paths",
                True,
                f"All required paths are writable: {', '.join(paths)}",
                critical=True
            )
        else:
            error_msg = []
            if missing_paths:
                error_msg.append(f"Cannot create: {', '.join(missing_paths)}")
            if readonly_paths:
                error_msg.append(f"Read-only: {', '.join(readonly_paths)}")
            
            return StartupCheckResult(
                "Writable Paths",
                False,
                "; ".join(error_msg),
                critical=True
            )
    
    def check_agents_smoke_test(self) -> StartupCheckResult:
        """Quick smoke test for validation and recommendation agents."""
        try:
            from agents.content_validator import ContentValidatorAgent
            from agents.recommendation_agent import RecommendationAgent
            
            # Test fixture content
            test_content = """---
title: Test Document
---

# Test Document

This is a test document with a code block:

```python
print("Hello, World!")
```
"""
            
            # Quick validation test
            validator = ContentValidatorAgent("test_validator")
            # Don't actually run full validation, just instantiate
            
            # Quick recommendation test
            rec_agent = RecommendationAgent("test_rec_agent")
            # Don't actually generate recommendations, just instantiate
            
            return StartupCheckResult(
                "Agent Smoke Test",
                True,
                "Validation and recommendation agents instantiated successfully",
                critical=False
            )
        except Exception as e:
            return StartupCheckResult(
                "Agent Smoke Test",
                False,
                f"Agent smoke test failed: {e}",
                critical=False
            )
    
    def run_all_checks(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Run all startup checks.
        
        Returns:
            (success, summary) tuple where success is True if all critical checks passed
        """
        logger.info("Running startup checks...")
        
        # Run all checks
        self.results.append(self.check_database_connectivity())
        self.results.append(self.check_database_schema())
        self.results.append(self.check_ollama_connectivity())
        self.results.append(self.check_ollama_models())
        self.results.append(self.check_writable_paths())
        self.results.append(self.check_agents_smoke_test())
        
        # Count failures
        self.critical_failures = sum(1 for r in self.results if not r.passed and r.critical)
        total_failures = sum(1 for r in self.results if not r.passed)
        
        # Build summary
        summary = {
            "total_checks": len(self.results),
            "passed": sum(1 for r in self.results if r.passed),
            "failed": total_failures,
            "critical_failures": self.critical_failures,
            "checks": [r.to_dict() for r in self.results],
        }
        
        # Print results
        print("\n" + "="*70)
        print("STARTUP CHECKS SUMMARY")
        print("="*70)
        
        for result in self.results:
            status_icon = "[OK]" if result.passed else "[FAIL]"
            criticality = "[CRITICAL]" if result.critical else "[WARNING]"
            status_text = f"{status_icon} {result.name}"
            
            if not result.passed and result.critical:
                print(f"{status_text} {criticality}")
                print(f"  -> {result.message}")
            elif not result.passed:
                print(f"{status_text} {criticality}")
                print(f"  -> {result.message}")
            else:
                print(f"{status_text}")
        
        print("="*70)
        print(f"Total: {len(self.results)} checks | Passed: {summary['passed']} | Failed: {total_failures}")
        
        if self.critical_failures > 0:
            print(f"\n[CRITICAL] {self.critical_failures} CRITICAL FAILURE(S) - Cannot start server")
            print("="*70 + "\n")
            return False, summary
        elif total_failures > 0:
            print(f"\n[WARNING] {total_failures} WARNING(S) - Server may not work correctly")
            print("="*70 + "\n")
            return True, summary
        else:
            print("\n[OK] ALL CHECKS PASSED - System ready to start")
            print("="*70 + "\n")
            return True, summary


def run_startup_checks() -> Tuple[bool, Dict[str, Any]]:
    """
    Run all startup checks and return results.
    
    Returns:
        (success, summary) where success indicates if system can start
    """
    checker = StartupChecker()
    return checker.run_all_checks()