# file: tests/core/test_config_loader.py
"""
Tests for the Generic Configuration Loader.

Covers:
- ConfigLoader initialization and file loading
- Rule parsing and retrieval
- Profile configuration and switching
- Family-specific overrides
- Cache invalidation and reload
- Edge cases and error handling
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path

from core.config_loader import (
    ConfigLoader,
    Rule,
    ProfileConfig,
    ValidatorConfig,
    get_config_loader,
    reset_config_loader
)


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_config(temp_config_dir):
    """Create a sample validator config file."""
    config_content = """
seo:
  enabled: true
  profile: "default"

  rules:
    h1_required:
      enabled: true
      level: error
      message: "Document must have exactly one H1 heading"
      params: {}
    h1_unique:
      enabled: true
      level: error
      message: "Multiple H1 headings found"
    hierarchy_skip:
      enabled: true
      level: error
      message: "Heading hierarchy skip detected"
    empty_heading:
      enabled: true
      level: warning
      message: "Empty heading detected"
    heading_too_short:
      enabled: true
      level: warning
      message: "Heading below minimum length"
      params:
        min_length: 10
    disabled_rule:
      enabled: false
      level: info
      message: "This rule is disabled"

  profiles:
    strict:
      rules: [h1_required, h1_unique, hierarchy_skip, empty_heading, heading_too_short]
      overrides:
        heading_too_short:
          level: error
    default:
      rules: [h1_required, h1_unique, hierarchy_skip]
    relaxed:
      rules: [h1_required]

  family_overrides:
    words:
      profile: "strict"
      rules:
        hierarchy_skip:
          level: warning
    pdf:
      profile: "relaxed"
"""
    config_path = Path(temp_config_dir) / "seo.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    return temp_config_dir


@pytest.fixture
def loader(sample_config):
    """Create a ConfigLoader with sample config."""
    return ConfigLoader(config_dir=sample_config)


class TestConfigLoaderInit:
    """Test ConfigLoader initialization."""

    def test_init_default_path(self):
        """Test initialization with default config path."""
        loader = ConfigLoader()
        assert loader.config_dir == Path("./config")

    def test_init_custom_path(self, temp_config_dir):
        """Test initialization with custom config path."""
        loader = ConfigLoader(config_dir=temp_config_dir)
        assert loader.config_dir == Path(temp_config_dir)

    def test_init_empty_cache(self, temp_config_dir):
        """Test that cache is empty on init."""
        loader = ConfigLoader(config_dir=temp_config_dir)
        assert len(loader._cache) == 0


class TestConfigLoading:
    """Test configuration loading."""

    def test_load_existing_config(self, loader):
        """Test loading an existing configuration file."""
        config = loader.load("seo")
        assert config is not None
        assert config.name == "seo"
        assert config.enabled is True
        assert config.profile == "default"

    def test_load_nonexistent_config(self, loader):
        """Test loading a config file that doesn't exist."""
        config = loader.load("nonexistent")
        assert config is not None
        assert config.name == "nonexistent"
        assert config.enabled is True  # Default
        assert len(config.rules) == 0

    def test_load_caches_result(self, loader):
        """Test that loaded config is cached."""
        config1 = loader.load("seo")
        config2 = loader.load("seo")
        assert config1 is config2  # Same instance from cache

    def test_load_force_reload(self, loader):
        """Test force reload bypasses cache."""
        config1 = loader.load("seo")
        config2 = loader.load("seo", force_reload=True)
        # Both should have same content but may be different objects
        assert config2.name == "seo"
        assert config2.enabled == config1.enabled


class TestRuleParsing:
    """Test rule parsing and retrieval."""

    def test_rules_parsed_correctly(self, loader):
        """Test that rules are parsed with all fields."""
        config = loader.load("seo")
        assert "h1_required" in config.rules
        rule = config.rules["h1_required"]
        assert rule.id == "h1_required"
        assert rule.enabled is True
        assert rule.level == "error"
        assert rule.message == "Document must have exactly one H1 heading"

    def test_rule_params(self, loader):
        """Test that rule params are parsed correctly."""
        config = loader.load("seo")
        rule = config.rules["heading_too_short"]
        assert rule.params.get("min_length") == 10

    def test_disabled_rule(self, loader):
        """Test disabled rule parsing."""
        config = loader.load("seo")
        rule = config.rules["disabled_rule"]
        assert rule.enabled is False

    def test_get_rules_default_profile(self, loader):
        """Test get_rules with default profile."""
        rules = loader.get_rules("seo", profile="default")
        rule_ids = [r.id for r in rules]
        assert "h1_required" in rule_ids
        assert "h1_unique" in rule_ids
        assert "hierarchy_skip" in rule_ids
        # Not in default profile
        assert "empty_heading" not in rule_ids

    def test_get_rules_strict_profile(self, loader):
        """Test get_rules with strict profile."""
        rules = loader.get_rules("seo", profile="strict")
        rule_ids = [r.id for r in rules]
        assert "h1_required" in rule_ids
        assert "empty_heading" in rule_ids
        assert "heading_too_short" in rule_ids

    def test_get_rules_relaxed_profile(self, loader):
        """Test get_rules with relaxed profile."""
        rules = loader.get_rules("seo", profile="relaxed")
        rule_ids = [r.id for r in rules]
        assert "h1_required" in rule_ids
        assert len(rules) == 1

    def test_profile_overrides_rule_level(self, loader):
        """Test that profile overrides can change rule level."""
        rules = loader.get_rules("seo", profile="strict")
        heading_rule = next(r for r in rules if r.id == "heading_too_short")
        assert heading_rule.level == "error"  # Overridden from warning


class TestProfiles:
    """Test profile configuration."""

    def test_get_profile_exists(self, loader):
        """Test getting an existing profile."""
        profile = loader.get_profile("seo", "strict")
        assert profile is not None
        assert profile.name == "strict"
        assert "h1_required" in profile.rules
        assert "heading_too_short" in profile.overrides

    def test_get_profile_not_exists(self, loader):
        """Test getting a non-existent profile."""
        profile = loader.get_profile("seo", "nonexistent")
        assert profile is None

    def test_profile_rules_list(self, loader):
        """Test profile rules list."""
        profile = loader.get_profile("seo", "default")
        assert profile is not None
        assert len(profile.rules) == 3


class TestFamilyOverrides:
    """Test family-specific override handling."""

    def test_get_family_override_exists(self, loader):
        """Test getting an existing family override."""
        override = loader.get_family_override("seo", "words")
        assert override is not None
        assert override.get("profile") == "strict"

    def test_get_family_override_not_exists(self, loader):
        """Test getting a non-existent family override."""
        override = loader.get_family_override("seo", "nonexistent")
        assert override is None

    def test_family_changes_profile(self, loader):
        """Test that family override can change effective profile."""
        # Without family: default profile
        rules_default = loader.get_rules("seo", profile="default")
        # With words family: strict profile (from family override)
        rules_words = loader.get_rules("seo", profile="default", family="words")

        default_ids = {r.id for r in rules_default}
        words_ids = {r.id for r in rules_words}

        # Words should have more rules because it uses strict profile
        assert len(words_ids) > len(default_ids)
        assert "empty_heading" in words_ids
        assert "empty_heading" not in default_ids

    def test_family_rule_override(self, loader):
        """Test that family can override individual rule settings."""
        rules = loader.get_rules("seo", profile="default", family="words")
        hierarchy_rule = next((r for r in rules if r.id == "hierarchy_skip"), None)
        assert hierarchy_rule is not None
        # Family override changes level from error to warning
        assert hierarchy_rule.level == "warning"


class TestReload:
    """Test cache invalidation and reload."""

    def test_reload_specific_validator(self, loader):
        """Test reloading a specific validator config."""
        config1 = loader.load("seo")
        assert "seo" in loader._cache

        loader.reload("seo")

        assert "seo" not in loader._cache
        config2 = loader.load("seo")
        assert config2.name == "seo"

    def test_reload_all(self, loader):
        """Test reloading all configs."""
        loader.load("seo")
        assert len(loader._cache) > 0

        loader.reload()

        assert len(loader._cache) == 0


class TestValidatorConfig:
    """Test ValidatorConfig dataclass."""

    def test_to_dict(self, loader):
        """Test ValidatorConfig.to_dict()."""
        config = loader.load("seo")
        config_dict = config.to_dict()

        assert config_dict["name"] == "seo"
        assert config_dict["enabled"] is True
        assert "rules" in config_dict
        assert "profiles" in config_dict
        assert "family_overrides" in config_dict

    def test_get_nested_value(self, loader):
        """Test ValidatorConfig.get() with nested key."""
        config = loader.load("seo")
        # Access raw config via get()
        value = config.get("rules.h1_required.level")
        assert value == "error"

    def test_get_missing_value(self, loader):
        """Test ValidatorConfig.get() with missing key."""
        config = loader.load("seo")
        value = config.get("nonexistent.key", default="default_value")
        assert value == "default_value"


class TestRule:
    """Test Rule dataclass."""

    def test_rule_to_dict(self):
        """Test Rule.to_dict()."""
        rule = Rule(
            id="test_rule",
            enabled=True,
            level="error",
            message="Test message",
            params={"key": "value"}
        )
        rule_dict = rule.to_dict()

        assert rule_dict["id"] == "test_rule"
        assert rule_dict["enabled"] is True
        assert rule_dict["level"] == "error"
        assert rule_dict["message"] == "Test message"
        assert rule_dict["params"]["key"] == "value"

    def test_rule_defaults(self):
        """Test Rule default values."""
        rule = Rule(id="minimal")
        assert rule.enabled is True
        assert rule.level == "warning"
        assert rule.message == ""
        assert rule.params == {}


class TestProfileConfig:
    """Test ProfileConfig dataclass."""

    def test_profile_to_dict(self):
        """Test ProfileConfig.to_dict()."""
        profile = ProfileConfig(
            name="test_profile",
            rules=["rule1", "rule2"],
            overrides={"rule1": {"level": "error"}}
        )
        profile_dict = profile.to_dict()

        assert profile_dict["name"] == "test_profile"
        assert "rule1" in profile_dict["rules"]
        assert "rule1" in profile_dict["overrides"]


class TestListValidators:
    """Test list_validators functionality."""

    def test_list_validators(self, sample_config):
        """Test listing available validators."""
        loader = ConfigLoader(config_dir=sample_config)
        validators = loader.list_validators()
        assert "seo" in validators

    def test_list_validators_empty_dir(self, temp_config_dir):
        """Test listing validators in empty directory."""
        loader = ConfigLoader(config_dir=temp_config_dir)
        validators = loader.list_validators()
        assert validators == []


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_malformed_yaml(self, temp_config_dir):
        """Test handling of malformed YAML."""
        config_path = Path(temp_config_dir) / "bad.yaml"
        with open(config_path, "w") as f:
            f.write("invalid: yaml: content: ][")

        loader = ConfigLoader(config_dir=temp_config_dir)
        config = loader.load("bad")
        # Should return empty config, not crash
        assert config.name == "bad"
        assert len(config.rules) == 0

    def test_empty_yaml(self, temp_config_dir):
        """Test handling of empty YAML file."""
        config_path = Path(temp_config_dir) / "empty.yaml"
        with open(config_path, "w") as f:
            f.write("")

        loader = ConfigLoader(config_dir=temp_config_dir)
        config = loader.load("empty")
        assert config.name == "empty"
        assert config.enabled is True

    def test_nonexistent_directory(self):
        """Test handling of non-existent config directory."""
        loader = ConfigLoader(config_dir="./nonexistent_path")
        validators = loader.list_validators()
        assert validators == []

    def test_missing_rule_in_profile(self, temp_config_dir):
        """Test profile referencing non-existent rule."""
        config_content = """
test:
  rules:
    existing_rule:
      enabled: true
      level: warning
      message: "Test"
  profiles:
    test_profile:
      rules: [existing_rule, nonexistent_rule]
"""
        config_path = Path(temp_config_dir) / "test.yaml"
        with open(config_path, "w") as f:
            f.write(config_content)

        loader = ConfigLoader(config_dir=temp_config_dir)
        rules = loader.get_rules("test", profile="test_profile")
        # Should only return the existing rule
        rule_ids = [r.id for r in rules]
        assert "existing_rule" in rule_ids
        assert "nonexistent_rule" not in rule_ids


class TestSingletonLoader:
    """Test the singleton config loader."""

    def test_get_config_loader(self):
        """Test get_config_loader returns singleton."""
        reset_config_loader()
        loader1 = get_config_loader()
        loader2 = get_config_loader()
        assert loader1 is loader2

    def test_reset_config_loader(self):
        """Test reset_config_loader clears singleton."""
        loader1 = get_config_loader()
        reset_config_loader()
        loader2 = get_config_loader()
        assert loader1 is not loader2


# Integration tests - verify real-world scenarios
class TestIntegration:
    """Integration tests for config loading scenarios."""

    def test_full_validation_config_flow(self, loader):
        """Test complete flow: load -> get rules -> apply to validation."""
        # Simulate what a validator would do
        config = loader.load("seo")
        assert config.enabled

        # Get rules for strict profile
        rules = loader.get_rules("seo", profile="strict")
        assert len(rules) > 0

        # Check that rules can be used for validation
        for rule in rules:
            assert rule.id is not None
            assert rule.level in ["error", "warning", "info"]
            assert isinstance(rule.message, str)

    def test_family_specific_validation(self, loader):
        """Test family-specific validation configuration."""
        # Words family should use strict profile
        override = loader.get_family_override("seo", "words")
        assert override is not None
        assert override.get("profile") == "strict"

        # PDF family should use relaxed profile
        override = loader.get_family_override("seo", "pdf")
        assert override is not None
        assert override.get("profile") == "relaxed"

        # Get rules for words family
        rules = loader.get_rules("seo", profile="default", family="words")
        rule_ids = [r.id for r in rules]
        # Should have strict profile rules even though we requested default
        assert "empty_heading" in rule_ids
