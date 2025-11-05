"""
TBCV - Truth-Based Content Validation System
A comprehensive system for validating and enhancing technical content with plugin detection.
"""

# Location: scripts/reviewer/__init__.py
# TBCV - Truth-Based Content Validation System
# A comprehensive system for validating and enhancing technical content with plugin detection
#
# This package provides:
# - Multi-agent architecture with MCP protocol
# - Plugin detection using fuzzy matching algorithms  
# - Content validation for YAML, Markdown, and code
# - Content enhancement with automatic plugin linking
# - Workflow orchestration and batch processing
# - Two-level caching system (L1 in-memory, L2 persistent)
# - RESTful API and CLI interfaces
# - Real-time monitoring and WebSocket support

__version__ = "1.0.0"
__author__ = "TBCV Development Team"
__description__ = "Truth-Based Content Validation System"

# Import core components for easy access
from .core.config import get_settings
from .core.logging import setup_logging
from .agents.base import BaseAgent, agent_registry
from .agents.fuzzy_detector import FuzzyDetectorAgent
from .agents.content_validator import ContentValidatorAgent
from .agents.content_enhancer import ContentEnhancerAgent
from .agents.orchestrator import OrchestratorAgent
from .agents.truth_manager import TruthManagerAgent

# Export main components
__all__ = [
    "get_settings",
    "setup_logging", 
    "BaseAgent",
    "agent_registry",
    "FuzzyDetectorAgent",
    "ContentValidatorAgent",
    "ContentEnhancerAgent", 
    "OrchestratorAgent",
    "TruthManagerAgent",
]
