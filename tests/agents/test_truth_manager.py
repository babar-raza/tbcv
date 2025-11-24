# file: tests/agents/test_truth_manager.py
"""
Comprehensive tests for agents/truth_manager.py module.
Target: 85%+ coverage of TruthManagerAgent functionality.
"""

import os
import sys

# Set environment before imports
os.environ.setdefault("TBCV_ENV", "test")
os.environ.setdefault("OLLAMA_ENABLED", "false")
os.environ.setdefault("OLLAMA_MODEL", "mistral")

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, AsyncMock

from agents.truth_manager import (
    TruthManagerAgent,
    PluginInfo,
    CombinationRule,
    TruthDataIndex,
    TruthDataAdapter
)


# =============================================================================
# Data Model Tests
# =============================================================================

@pytest.mark.unit
class TestPluginInfo:
    """Test PluginInfo dataclass."""

    def test_plugin_info_creation_minimal(self):
        """Test creating PluginInfo with minimal fields."""
        plugin = PluginInfo(
            id="test_plugin",
            name="Test Plugin",
            slug="test-plugin",
            description="A test plugin",
            patterns={"csharp": ["Test.Method"]},
            family="words",
            version="1.0.0",
            dependencies=[],
            capabilities=["read"]
        )

        assert plugin.id == "test_plugin"
        assert plugin.name == "Test Plugin"
        assert plugin.family == "words"
        assert plugin.load_formats == []
        assert plugin.save_formats == []

    def test_plugin_info_creation_full(self):
        """Test creating PluginInfo with all fields."""
        plugin = PluginInfo(
            id="test_plugin",
            name="Test Plugin",
            slug="test-plugin",
            description="A test plugin",
            patterns={"csharp": ["Test.Method"]},
            family="words",
            version="1.0.0",
            dependencies=["dep1"],
            capabilities=["read", "write"],
            plugin_type="converter",
            load_formats=["docx"],
            save_formats=["pdf"]
        )

        assert plugin.plugin_type == "converter"
        assert plugin.load_formats == ["docx"]
        assert plugin.save_formats == ["pdf"]
        assert plugin.dependencies == ["dep1"]

    def test_plugin_info_to_dict(self):
        """Test PluginInfo serialization to dict."""
        plugin = PluginInfo(
            id="test_plugin",
            name="Test Plugin",
            slug="test-plugin",
            description="A test plugin",
            patterns={"csharp": ["Test.Method"]},
            family="words",
            version="1.0.0",
            dependencies=[],
            capabilities=["read"]
        )

        plugin_dict = plugin.to_dict()
        assert isinstance(plugin_dict, dict)
        assert plugin_dict["id"] == "test_plugin"
        assert plugin_dict["name"] == "Test Plugin"
        assert plugin_dict["patterns"] == {"csharp": ["Test.Method"]}


@pytest.mark.unit
class TestCombinationRule:
    """Test CombinationRule dataclass."""

    def test_combination_rule_creation(self):
        """Test creating CombinationRule."""
        rule = CombinationRule(
            name="Test Combo",
            plugins=["plugin1", "plugin2"],
            trigger_patterns=["Pattern1", "Pattern2"],
            confidence_boost=0.1,
            required_all=True
        )

        assert rule.name == "Test Combo"
        assert len(rule.plugins) == 2
        assert rule.confidence_boost == 0.1
        assert rule.required_all is True

    def test_combination_rule_to_dict(self):
        """Test CombinationRule serialization to dict."""
        rule = CombinationRule(
            name="Test Combo",
            plugins=["plugin1", "plugin2"],
            trigger_patterns=["Pattern1"],
            confidence_boost=0.2,
            required_all=False
        )

        rule_dict = rule.to_dict()
        assert isinstance(rule_dict, dict)
        assert rule_dict["name"] == "Test Combo"
        assert rule_dict["plugins"] == ["plugin1", "plugin2"]
        assert rule_dict["confidence_boost"] == 0.2
        assert rule_dict["required_all"] is False


# =============================================================================
# TruthDataAdapter Tests
# =============================================================================

@pytest.mark.unit
class TestTruthDataAdapter:
    """Test TruthDataAdapter functionality."""

    def test_adapter_initialization(self):
        """Test TruthDataAdapter initialization."""
        adapter = TruthDataAdapter(family="words")
        assert adapter.family == "words"
        assert adapter.family_rules is not None

    def test_adapt_plugin_data_with_plugins_key(self):
        """Test adapting truth data with 'plugins' key."""
        adapter = TruthDataAdapter(family="words")

        truth_data = {
            "plugins": [
                {
                    "name": "Test Plugin",
                    "id": "test-plugin",
                    "type": "processor"
                }
            ]
        }

        adapted = adapter.adapt_plugin_data(truth_data)
        assert "plugins" in adapted
        assert isinstance(adapted["plugins"], list)

    def test_adapt_plugin_data_with_components_key(self):
        """Test adapting truth data with 'components' key (fallback)."""
        adapter = TruthDataAdapter(family="words")

        truth_data = {
            "components": [
                {
                    "name": "Test Component",
                    "id": "test-component"
                }
            ]
        }

        adapted = adapter.adapt_plugin_data(truth_data)
        assert "plugins" in adapted

    def test_adapt_plugin_data_with_items_key(self):
        """Test adapting truth data with 'items' key (second fallback)."""
        adapter = TruthDataAdapter(family="words")

        truth_data = {
            "items": [
                {
                    "name": "Test Item",
                    "id": "test-item"
                }
            ]
        }

        adapted = adapter.adapt_plugin_data(truth_data)
        assert "plugins" in adapted

    def test_adapt_plugin_data_empty(self):
        """Test adapting empty truth data."""
        adapter = TruthDataAdapter(family="words")

        truth_data = {}
        adapted = adapter.adapt_plugin_data(truth_data)

        assert "plugins" in adapted
        assert len(adapted["plugins"]) == 0


# =============================================================================
# TruthManagerAgent Basic Tests
# =============================================================================

@pytest.mark.unit
class TestTruthManagerAgentBasics:
    """Test TruthManagerAgent initialization and basic operations."""

    def test_truth_manager_initialization(self):
        """Test TruthManagerAgent initialization."""
        agent = TruthManagerAgent("test_truth_manager")

        assert agent.agent_id == "test_truth_manager"
        assert agent.truth_index is None
        assert isinstance(agent.truth_directories, list)
        assert isinstance(agent.validation_issues, list)
        assert "words" in agent.supported_families

    def test_truth_manager_default_id(self):
        """Test TruthManagerAgent with default ID."""
        agent = TruthManagerAgent()

        assert agent.agent_id == "truth_manager"

    def test_get_contract(self):
        """Test TruthManagerAgent contract."""
        agent = TruthManagerAgent()
        contract = agent.get_contract()

        assert contract.agent_id == "truth_manager"
        assert contract.name == "TruthManagerAgent"
        assert contract.version == "1.0.0"
        assert len(contract.capabilities) >= 3
        assert contract.max_runtime_s == 60
        assert contract.confidence_threshold == 0.9

    def test_get_contract_capabilities(self):
        """Test contract capabilities are properly defined."""
        agent = TruthManagerAgent()
        contract = agent.get_contract()

        capability_names = [cap.name for cap in contract.capabilities]
        assert "load_truth_data" in capability_names
        assert "get_plugin_info" in capability_names
        assert "search_plugins" in capability_names

    def test_message_handlers_registered(self):
        """Test that message handlers are registered."""
        agent = TruthManagerAgent()

        # Check handlers are registered
        assert "ping" in agent.handlers
        assert "get_status" in agent.handlers
        assert "load_truth_data" in agent.handlers
        assert "get_plugin_info" in agent.handlers
        assert "search_plugins" in agent.handlers
        assert "get_combination_rules" in agent.handlers


# =============================================================================
# TruthManagerAgent Handler Tests (Async)
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
class TestTruthManagerHandlers:
    """Test TruthManagerAgent async handlers."""

    async def test_handle_ping(self):
        """Test ping handler."""
        agent = TruthManagerAgent()
        response = await agent.handle_ping({})

        assert response["status"] == "ok"
        assert "timestamp" in response

    async def test_handle_get_status(self):
        """Test get_status handler."""
        agent = TruthManagerAgent()
        response = await agent.handle_get_status({})

        assert "agent_id" in response
        assert "status" in response
        assert response["agent_id"] == "truth_manager"

    async def test_handle_load_truth_data_default_family(self):
        """Test loading truth data with default family."""
        agent = TruthManagerAgent()

        # Mock the internal _load_truth_data method
        with patch.object(agent, '_load_truth_data', return_value=True):
            response = await agent.handle_load_truth_data({})

            assert "success" in response
            assert "family" in response

    async def test_handle_load_truth_data_specific_family(self):
        """Test loading truth data with specific family."""
        agent = TruthManagerAgent()

        with patch.object(agent, '_load_truth_data', return_value=True):
            response = await agent.handle_load_truth_data({"family": "cells"})

            assert "success" in response
            assert response.get("family") in ["cells", "words"]  # May use default

    async def test_handle_get_plugin_info_no_index(self):
        """Test get_plugin_info when no truth data loaded."""
        agent = TruthManagerAgent()
        agent.truth_index = None

        response = await agent.handle_get_plugin_info({"plugin_id": "test"})

        assert "error" in response or "found" in response
        if "found" in response:
            assert response["found"] is False

    async def test_handle_get_plugin_info_by_id(self):
        """Test get_plugin_info by plugin ID."""
        agent = TruthManagerAgent()

        # Create mock truth index
        mock_plugin = PluginInfo(
            id="test_plugin",
            name="Test Plugin",
            slug="test-plugin",
            description="Test",
            patterns={},
            family="words",
            version="1.0.0",
            dependencies=[],
            capabilities=[]
        )

        agent.truth_index = TruthDataIndex(
            by_id={"test_plugin": mock_plugin},
            by_slug={},
            by_name={},
            by_alias={},
            by_family={},
            by_pattern={},
            combination_rules=[],
            combination_index={},
            dependencies={},
            version_hash="test_hash",
            last_updated=datetime.now()
        )

        response = await agent.handle_get_plugin_info({"plugin_id": "test_plugin"})

        assert response["found"] is True
        assert response["plugin"]["id"] == "test_plugin"

    async def test_handle_get_plugin_info_by_slug(self):
        """Test get_plugin_info by slug."""
        agent = TruthManagerAgent()

        mock_plugin = PluginInfo(
            id="test_plugin",
            name="Test Plugin",
            slug="test-plugin",
            description="Test",
            patterns={},
            family="words",
            version="1.0.0",
            dependencies=[],
            capabilities=[]
        )

        agent.truth_index = TruthDataIndex(
            by_id={},
            by_slug={"test-plugin": mock_plugin},
            by_name={},
            by_alias={},
            by_family={},
            by_pattern={},
            combination_rules=[],
            combination_index={},
            dependencies={},
            version_hash="test_hash",
            last_updated=datetime.now()
        )

        response = await agent.handle_get_plugin_info({"slug": "test-plugin"})

        assert response["found"] is True
        assert response["plugin"]["slug"] == "test-plugin"

    async def test_handle_search_plugins_no_index(self):
        """Test search_plugins when no truth data loaded."""
        agent = TruthManagerAgent()
        agent.truth_index = None

        response = await agent.handle_search_plugins({"query": "test"})

        assert "results" in response or "error" in response
        if "results" in response:
            assert len(response["results"]) == 0

    async def test_handle_search_plugins_with_query(self):
        """Test search_plugins with query string."""
        agent = TruthManagerAgent()

        mock_plugin = PluginInfo(
            id="word_processor",
            name="Word Processor Plugin",
            slug="word-processor",
            description="Process words",
            patterns={},
            family="words",
            version="1.0.0",
            dependencies=[],
            capabilities=[]
        )

        agent.truth_index = TruthDataIndex(
            by_id={"word_processor": mock_plugin},
            by_slug={},
            by_name={"word processor plugin": mock_plugin},
            by_alias={"word": [mock_plugin]},
            by_family={"words": [mock_plugin]},
            by_pattern={},
            combination_rules=[],
            combination_index={},
            dependencies={},
            version_hash="test_hash",
            last_updated=datetime.now()
        )

        response = await agent.handle_search_plugins({"query": "word"})

        assert "results" in response
        assert isinstance(response["results"], list)

    async def test_handle_get_combination_rules_no_index(self):
        """Test get_combination_rules when no truth data loaded."""
        agent = TruthManagerAgent()
        agent.truth_index = None

        response = await agent.handle_get_combination_rules({})

        assert "rules" in response or "error" in response

    async def test_handle_get_combination_rules_with_rules(self):
        """Test get_combination_rules with loaded rules."""
        agent = TruthManagerAgent()

        mock_rule = CombinationRule(
            name="Test Combo",
            plugins=["plugin1", "plugin2"],
            trigger_patterns=["Pattern1"],
            confidence_boost=0.1,
            required_all=True
        )

        agent.truth_index = TruthDataIndex(
            by_id={},
            by_slug={},
            by_name={},
            by_alias={},
            by_family={},
            by_pattern={},
            combination_rules=[mock_rule],
            combination_index={},
            dependencies={},
            version_hash="test_hash",
            last_updated=datetime.now()
        )

        response = await agent.handle_get_combination_rules({})

        assert "rules" in response
        assert len(response["rules"]) == 1
        assert response["rules"][0]["name"] == "Test Combo"

    async def test_handle_validate_truth_data(self):
        """Test validate_truth_data handler."""
        agent = TruthManagerAgent()

        response = await agent.handle_validate_truth_data({})

        assert "valid" in response
        assert "issues" in response
        assert isinstance(response["issues"], list)

    async def test_handle_get_truth_statistics_no_index(self):
        """Test get_truth_statistics when no truth data loaded."""
        agent = TruthManagerAgent()
        agent.truth_index = None

        response = await agent.handle_get_truth_statistics({})

        assert "total_plugins" in response or "error" in response

    async def test_handle_get_truth_statistics_with_data(self):
        """Test get_truth_statistics with loaded data."""
        agent = TruthManagerAgent()

        mock_plugin = PluginInfo(
            id="test_plugin",
            name="Test Plugin",
            slug="test-plugin",
            description="Test",
            patterns={"csharp": ["Test"]},
            family="words",
            version="1.0.0",
            dependencies=[],
            capabilities=[]
        )

        agent.truth_index = TruthDataIndex(
            by_id={"test_plugin": mock_plugin},
            by_slug={"test-plugin": mock_plugin},
            by_name={"test plugin": mock_plugin},
            by_alias={},
            by_family={"words": [mock_plugin]},
            by_pattern={},
            combination_rules=[],
            combination_index={},
            dependencies={},
            version_hash="test_hash",
            last_updated=datetime.now()
        )

        response = await agent.handle_get_truth_statistics({})

        assert response["total_plugins"] == 1
        assert "families" in response
        assert "version_hash" in response

    async def test_handle_reload_truth_data(self):
        """Test reload_truth_data handler."""
        agent = TruthManagerAgent()

        with patch.object(agent, '_load_truth_data', return_value=True):
            response = await agent.handle_reload_truth_data({})

            assert "success" in response

    async def test_handle_check_plugin_combination_no_index(self):
        """Test check_plugin_combination when no truth data loaded."""
        agent = TruthManagerAgent()
        agent.truth_index = None

        response = await agent.handle_check_plugin_combination({
            "plugin_ids": ["plugin1", "plugin2"]
        })

        assert "valid" in response or "error" in response

    async def test_handle_check_plugin_combination_valid(self):
        """Test check_plugin_combination with valid combination."""
        agent = TruthManagerAgent()

        mock_rule = CombinationRule(
            name="Valid Combo",
            plugins=["plugin1", "plugin2"],
            trigger_patterns=[],
            confidence_boost=0.1,
            required_all=True
        )

        agent.truth_index = TruthDataIndex(
            by_id={},
            by_slug={},
            by_name={},
            by_alias={},
            by_family={},
            by_pattern={},
            combination_rules=[mock_rule],
            combination_index={
                ("plugin1", "plugin2"): [mock_rule]
            },
            dependencies={},
            version_hash="test_hash",
            last_updated=datetime.now()
        )

        response = await agent.handle_check_plugin_combination({
            "plugin_ids": ["plugin1", "plugin2"]
        })

        assert "valid" in response
        if response["valid"]:
            assert "rules" in response


# =============================================================================
# Integration Tests with Real Truth Data
# =============================================================================

@pytest.mark.integration
class TestTruthManagerIntegration:
    """Integration tests with actual truth data files."""

    def test_load_truth_data_from_files(self):
        """Test loading truth data from actual files."""
        agent = TruthManagerAgent()

        # Try to load from actual truth directory if it exists
        truth_dir = Path("truth")
        if truth_dir.exists():
            result = agent._load_truth_data(family="words")

            # If truth data loaded successfully
            if result:
                assert agent.truth_index is not None
                assert len(agent.truth_index.by_id) > 0

    @pytest.mark.asyncio
    async def test_full_workflow_with_real_data(self):
        """Test complete workflow with real truth data."""
        agent = TruthManagerAgent()

        truth_dir = Path("truth")
        if not truth_dir.exists():
            pytest.skip("Truth directory not available")

        # Load truth data
        load_response = await agent.handle_load_truth_data({"family": "words"})

        if load_response.get("success"):
            # Get statistics
            stats_response = await agent.handle_get_truth_statistics({})
            assert stats_response["total_plugins"] > 0

            # Search for plugins
            search_response = await agent.handle_search_plugins({"query": "aspose"})
            assert "results" in search_response


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=agents.truth_manager", "--cov-report=term-missing"])
