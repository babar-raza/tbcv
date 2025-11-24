# tests/core/test_rule_manager.py
"""
Unit tests for core/rule_manager.py - RuleManager.
Target coverage: 100% (Currently 25%)
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open

from core.rule_manager import RuleManager, FamilyRules, rule_manager


@pytest.mark.unit
class TestFamilyRules:
    """Test FamilyRules dataclass."""

    def test_family_rules_creation(self):
        """Test FamilyRules dataclass creation."""
        rules = FamilyRules(
            family="words",
            plugin_aliases={"alias1": ["plugin1"]},
            api_patterns={"pattern1": ["regex1"]},
            dependencies={"plugin1": ["plugin2"]},
            non_editable_yaml_fields={"field1", "field2"},
            validation_requirements={"req1": "value1"},
            code_quality_rules={"rule1": "value1"},
            format_patterns={"format1": ["pattern1"]}
        )

        assert rules.family == "words"
        assert rules.plugin_aliases == {"alias1": ["plugin1"]}
        assert rules.api_patterns == {"pattern1": ["regex1"]}
        assert rules.dependencies == {"plugin1": ["plugin2"]}
        assert "field1" in rules.non_editable_yaml_fields
        assert rules.validation_requirements == {"req1": "value1"}
        assert rules.code_quality_rules == {"rule1": "value1"}
        assert rules.format_patterns == {"format1": ["pattern1"]}


@pytest.mark.unit
class TestRuleManager:
    """Test RuleManager class."""

    def test_initialization(self):
        """Test RuleManager initialization."""
        manager = RuleManager()

        assert isinstance(manager.rules_cache, dict)
        assert len(manager.rules_cache) == 0
        assert manager.rules_directory == Path("rules")
        assert "title" in manager.global_non_editable_fields
        assert "layout" in manager.global_non_editable_fields

    def test_get_family_rules_loads_from_file(self, temp_dir):
        """Test getting family rules loads from file."""
        # Create a test rules file
        rules_data = {
            "plugin_aliases": {"pdf": ["pdf_converter"]},
            "api_patterns": {"save": ["Save", "SaveAs"]},
            "dependencies": {},
            "non_editable_yaml_fields": ["custom_field"],
            "validation_requirements": {"min_length": 10},
            "code_quality_rules": {},
            "format_patterns": {}
        }

        manager = RuleManager()
        manager.rules_directory = temp_dir

        rules_file = temp_dir / "words.json"
        rules_file.write_text(json.dumps(rules_data))

        # Get rules (should load from file)
        rules = manager.get_family_rules("words")

        assert rules.family == "words"
        assert rules.plugin_aliases == {"pdf": ["pdf_converter"]}
        assert "save" in rules.api_patterns
        assert "custom_field" in rules.non_editable_yaml_fields
        assert "title" in rules.non_editable_yaml_fields  # Global field

    def test_get_family_rules_caching(self, temp_dir):
        """Test that family rules are cached."""
        rules_data = {"plugin_aliases": {}}

        manager = RuleManager()
        manager.rules_directory = temp_dir

        rules_file = temp_dir / "test.json"
        rules_file.write_text(json.dumps(rules_data))

        # First call - loads from file
        rules1 = manager.get_family_rules("test")
        # Second call - uses cache
        rules2 = manager.get_family_rules("test")

        assert rules1 is rules2  # Same object from cache
        assert "test" in manager.rules_cache

    def test_get_family_rules_missing_file(self, temp_dir):
        """Test getting rules for family with no rules file."""
        manager = RuleManager()
        manager.rules_directory = temp_dir

        with patch('core.rule_manager.logger') as mock_logger:
            rules = manager.get_family_rules("nonexistent")

            assert rules.family == "nonexistent"
            # Should return default rules
            assert "document_creation" in rules.api_patterns
            assert "save_operations" in rules.api_patterns
            mock_logger.warning.assert_called()

    def test_load_family_rules_invalid_json(self, temp_dir):
        """Test loading rules with invalid JSON."""
        manager = RuleManager()
        manager.rules_directory = temp_dir

        rules_file = temp_dir / "invalid.json"
        rules_file.write_text("{ invalid json }")

        with patch('core.rule_manager.logger') as mock_logger:
            manager._load_family_rules("invalid")

            # Should use default rules on error
            assert "invalid" in manager.rules_cache
            rules = manager.rules_cache["invalid"]
            assert rules.family == "invalid"
            mock_logger.error.assert_called()

    def test_parse_rules_data(self):
        """Test parsing rules data from JSON."""
        manager = RuleManager()

        data = {
            "plugin_aliases": {"alias": ["plugin"]},
            "api_patterns": {"pattern": ["regex"]},
            "dependencies": {"p1": ["p2"]},
            "non_editable_yaml_fields": ["custom"],
            "validation_requirements": {"req": "val"},
            "code_quality_rules": {"rule": "val"},
            "format_patterns": {"fmt": ["pattern"]}
        }

        rules = manager._parse_rules_data("test", data)

        assert rules.family == "test"
        assert rules.plugin_aliases == {"alias": ["plugin"]}
        assert rules.api_patterns == {"pattern": ["regex"]}
        assert "custom" in rules.non_editable_yaml_fields
        assert "title" in rules.non_editable_yaml_fields  # Global

    def test_parse_rules_data_missing_fields(self):
        """Test parsing rules data with missing optional fields."""
        manager = RuleManager()

        # Minimal data (all fields optional except those with defaults)
        data = {}

        rules = manager._parse_rules_data("minimal", data)

        assert rules.family == "minimal"
        assert rules.plugin_aliases == {}
        assert rules.api_patterns == {}
        assert rules.dependencies == {}
        # Should still have global non-editable fields
        assert "title" in rules.non_editable_yaml_fields

    def test_get_default_rules(self):
        """Test getting default rules."""
        manager = RuleManager()

        rules = manager._get_default_rules("default")

        assert rules.family == "default"
        assert "document_creation" in rules.api_patterns
        assert "save_operations" in rules.api_patterns
        assert "load_operations" in rules.api_patterns
        assert "forbidden_patterns" in rules.code_quality_rules
        assert "required_patterns" in rules.code_quality_rules
        assert len(rules.non_editable_yaml_fields) > 0

    def test_get_api_patterns(self, temp_dir):
        """Test getting API patterns for a family."""
        rules_data = {
            "api_patterns": {
                "save": ["Save", "SaveAs"],
                "load": ["Load", "Open"]
            }
        }

        manager = RuleManager()
        manager.rules_directory = temp_dir

        rules_file = temp_dir / "test.json"
        rules_file.write_text(json.dumps(rules_data))

        patterns = manager.get_api_patterns("test")

        assert "save" in patterns
        assert "load" in patterns
        assert "Save" in patterns["save"]

    def test_get_plugin_aliases(self, temp_dir):
        """Test getting plugin aliases for a family."""
        rules_data = {
            "plugin_aliases": {
                "pdf": ["pdf_converter", "pdf_export"],
                "word": ["word_processor"]
            }
        }

        manager = RuleManager()
        manager.rules_directory = temp_dir

        rules_file = temp_dir / "test.json"
        rules_file.write_text(json.dumps(rules_data))

        aliases = manager.get_plugin_aliases("test")

        assert "pdf" in aliases
        assert "pdf_converter" in aliases["pdf"]
        assert "word_processor" in aliases["word"]

    def test_get_dependencies(self, temp_dir):
        """Test getting dependencies for a plugin."""
        rules_data = {
            "dependencies": {
                "plugin1": ["plugin2", "plugin3"],
                "plugin2": []
            }
        }

        manager = RuleManager()
        manager.rules_directory = temp_dir

        rules_file = temp_dir / "test.json"
        rules_file.write_text(json.dumps(rules_data))

        # Get dependencies for plugin1
        deps = manager.get_dependencies("test", "plugin1")
        assert deps == ["plugin2", "plugin3"]

        # Get dependencies for plugin2 (empty)
        deps = manager.get_dependencies("test", "plugin2")
        assert deps == []

        # Get dependencies for nonexistent plugin
        deps = manager.get_dependencies("test", "nonexistent")
        assert deps == []

    def test_get_non_editable_fields(self, temp_dir):
        """Test getting non-editable fields."""
        rules_data = {
            "non_editable_yaml_fields": ["custom1", "custom2"]
        }

        manager = RuleManager()
        manager.rules_directory = temp_dir

        rules_file = temp_dir / "test.json"
        rules_file.write_text(json.dumps(rules_data))

        fields = manager.get_non_editable_fields("test")

        assert "custom1" in fields
        assert "custom2" in fields
        # Should also include global fields
        assert "title" in fields
        assert "layout" in fields

    def test_get_validation_requirements(self, temp_dir):
        """Test getting validation requirements."""
        rules_data = {
            "validation_requirements": {
                "min_length": 100,
                "max_length": 5000,
                "required_sections": ["introduction", "conclusion"]
            }
        }

        manager = RuleManager()
        manager.rules_directory = temp_dir

        rules_file = temp_dir / "test.json"
        rules_file.write_text(json.dumps(rules_data))

        requirements = manager.get_validation_requirements("test")

        assert requirements["min_length"] == 100
        assert requirements["max_length"] == 5000
        assert "introduction" in requirements["required_sections"]

    def test_get_code_quality_rules(self, temp_dir):
        """Test getting code quality rules."""
        rules_data = {
            "code_quality_rules": {
                "forbidden_patterns": {
                    "hardcoded": ["C:\\\\", "D:\\\\"]
                },
                "required_patterns": {
                    "error_handling": ["try", "catch"]
                }
            }
        }

        manager = RuleManager()
        manager.rules_directory = temp_dir

        rules_file = temp_dir / "test.json"
        rules_file.write_text(json.dumps(rules_data))

        quality_rules = manager.get_code_quality_rules("test")

        assert "forbidden_patterns" in quality_rules
        assert "required_patterns" in quality_rules
        assert "hardcoded" in quality_rules["forbidden_patterns"]

    def test_reload_rules_specific_family(self, temp_dir):
        """Test reloading rules for a specific family."""
        manager = RuleManager()
        manager.rules_directory = temp_dir

        # Create initial rules file
        rules_file = temp_dir / "test.json"
        rules_file.write_text(json.dumps({"plugin_aliases": {"v1": ["plugin1"]}}))

        # Load rules
        rules1 = manager.get_family_rules("test")
        assert "v1" in rules1.plugin_aliases

        # Update rules file
        rules_file.write_text(json.dumps({"plugin_aliases": {"v2": ["plugin2"]}}))

        # Reload
        manager.reload_rules("test")

        # Get updated rules
        rules2 = manager.get_family_rules("test")
        assert "v2" in rules2.plugin_aliases
        assert "v1" not in rules2.plugin_aliases

    def test_reload_all_rules(self):
        """Test reloading all rules (clearing cache)."""
        manager = RuleManager()

        # Populate cache
        manager.rules_cache["family1"] = manager._get_default_rules("family1")
        manager.rules_cache["family2"] = manager._get_default_rules("family2")

        assert len(manager.rules_cache) == 2

        # Reload all (clear cache)
        with patch('core.rule_manager.logger') as mock_logger:
            manager.reload_rules()

            assert len(manager.rules_cache) == 0
            mock_logger.info.assert_called_with("Cleared all rule caches")

    def test_global_non_editable_fields(self):
        """Test that global non-editable fields are present."""
        manager = RuleManager()

        expected_fields = {'layout', 'categories', 'date', 'draft', 'lastmod', 'title', 'weight', 'author'}

        assert manager.global_non_editable_fields == expected_fields

    def test_default_api_patterns_structure(self):
        """Test structure of default API patterns."""
        manager = RuleManager()
        rules = manager._get_default_rules("test")

        # Should have common operation patterns
        assert "document_creation" in rules.api_patterns
        assert "save_operations" in rules.api_patterns
        assert "load_operations" in rules.api_patterns

        # Each pattern should have regex patterns
        for patterns in rules.api_patterns.values():
            assert isinstance(patterns, list)
            assert len(patterns) > 0

    def test_default_code_quality_rules_structure(self):
        """Test structure of default code quality rules."""
        manager = RuleManager()
        rules = manager._get_default_rules("test")

        assert "forbidden_patterns" in rules.code_quality_rules
        assert "required_patterns" in rules.code_quality_rules

        # Check forbidden patterns
        assert "hardcoded_paths" in rules.code_quality_rules["forbidden_patterns"]
        assert "magic_numbers" in rules.code_quality_rules["forbidden_patterns"]

        # Check required patterns
        assert "error_handling" in rules.code_quality_rules["required_patterns"]
        assert "resource_disposal" in rules.code_quality_rules["required_patterns"]


@pytest.mark.unit
class TestGlobalRuleManager:
    """Test global rule_manager instance."""

    def test_global_instance_exists(self):
        """Test that global rule_manager exists."""
        from core.rule_manager import rule_manager

        assert rule_manager is not None
        assert isinstance(rule_manager, RuleManager)


@pytest.mark.integration
class TestRuleManagerIntegration:
    """Integration tests for RuleManager."""

    def test_multiple_families(self, temp_dir):
        """Test managing rules for multiple families."""
        manager = RuleManager()
        manager.rules_directory = temp_dir

        # Create rules for multiple families
        families = ["words", "cells", "slides", "pdf"]
        for family in families:
            rules_file = temp_dir / f"{family}.json"
            rules_file.write_text(json.dumps({
                "plugin_aliases": {family: [f"{family}_plugin"]}
            }))

        # Load all families
        for family in families:
            rules = manager.get_family_rules(family)
            assert rules.family == family
            assert family in rules.plugin_aliases

        # All should be cached
        assert len(manager.rules_cache) == len(families)

    def test_full_workflow(self, temp_dir):
        """Test complete workflow of loading and using rules."""
        manager = RuleManager()
        manager.rules_directory = temp_dir

        # Create comprehensive rules file
        rules_data = {
            "plugin_aliases": {"pdf": ["pdf_converter"]},
            "api_patterns": {"save": ["Save"]},
            "dependencies": {"plugin1": ["plugin2"]},
            "non_editable_yaml_fields": ["custom"],
            "validation_requirements": {"min": 10},
            "code_quality_rules": {"rule": "value"},
            "format_patterns": {"format": ["pattern"]}
        }

        rules_file = temp_dir / "complete.json"
        rules_file.write_text(json.dumps(rules_data))

        # Test all access methods
        assert "pdf" in manager.get_plugin_aliases("complete")
        assert "save" in manager.get_api_patterns("complete")
        assert manager.get_dependencies("complete", "plugin1") == ["plugin2"]
        assert "custom" in manager.get_non_editable_fields("complete")
        assert manager.get_validation_requirements("complete")["min"] == 10
        assert manager.get_code_quality_rules("complete")["rule"] == "value"

        # Rules should be cached
        assert "complete" in manager.rules_cache
