# file: core/config_loader.py
"""
Generic Configuration Loader for TBCV Validators.

Provides a unified way to load, parse, and access validator configurations
with support for rules, profiles, and family-specific overrides.
"""

from __future__ import annotations
import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path
from functools import lru_cache

from core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Rule:
    """Represents a single validation rule."""
    id: str
    enabled: bool = True
    level: str = "warning"  # error, warning, info
    message: str = ""
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "enabled": self.enabled,
            "level": self.level,
            "message": self.message,
            "params": self.params
        }


@dataclass
class ProfileConfig:
    """Represents a validation profile configuration."""
    name: str
    rules: List[str] = field(default_factory=list)
    overrides: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "rules": self.rules,
            "overrides": self.overrides
        }


@dataclass
class ValidatorConfig:
    """Complete configuration for a validator."""
    name: str
    enabled: bool = True
    profile: str = "default"
    rules: Dict[str, Rule] = field(default_factory=dict)
    profiles: Dict[str, ProfileConfig] = field(default_factory=dict)
    family_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    raw_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "profile": self.profile,
            "rules": {k: v.to_dict() for k, v in self.rules.items()},
            "profiles": {k: v.to_dict() for k, v in self.profiles.items()},
            "family_overrides": self.family_overrides,
            "raw_config": self.raw_config
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from raw_config by key path (supports dot notation)."""
        keys = key.split(".")
        value = self.raw_config
        try:
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    return default
                if value is None:
                    return default
            return value
        except (KeyError, TypeError):
            return default


class ConfigLoader:
    """
    Generic configuration loader with rules, profiles, and family overrides.

    Usage:
        loader = ConfigLoader()
        config = loader.load("seo")
        rules = loader.get_rules("seo", profile="strict")
        override = loader.get_family_override("seo", "words")
    """

    def __init__(self, config_dir: str = "./config"):
        """
        Initialize the configuration loader.

        Args:
            config_dir: Path to the configuration directory.
        """
        self.config_dir = Path(config_dir)
        self._cache: Dict[str, ValidatorConfig] = {}
        self._file_mtimes: Dict[str, float] = {}

    def load(self, validator_name: str, force_reload: bool = False) -> ValidatorConfig:
        """
        Load configuration for a validator.

        Args:
            validator_name: Name of the validator (e.g., 'seo', 'yaml', 'markdown')
            force_reload: Force reload from disk even if cached

        Returns:
            ValidatorConfig instance with parsed rules, profiles, and overrides
        """
        config_path = self.config_dir / f"{validator_name}.yaml"

        # Check cache
        if not force_reload and validator_name in self._cache:
            # Check if file has been modified
            if config_path.exists():
                current_mtime = config_path.stat().st_mtime
                cached_mtime = self._file_mtimes.get(validator_name, 0)
                if current_mtime <= cached_mtime:
                    return self._cache[validator_name]

        # Load from file
        raw_config = self._load_yaml(config_path)

        # Parse into ValidatorConfig
        config = self._parse_config(validator_name, raw_config)

        # Cache
        self._cache[validator_name] = config
        if config_path.exists():
            self._file_mtimes[validator_name] = config_path.stat().st_mtime

        return config

    def get_rules(
        self,
        validator_name: str,
        profile: str = "default",
        family: Optional[str] = None
    ) -> List[Rule]:
        """
        Get active rules for a validator based on profile and optional family override.

        Args:
            validator_name: Name of the validator
            profile: Profile name (default, strict, relaxed)
            family: Optional family for family-specific overrides

        Returns:
            List of active Rule objects
        """
        config = self.load(validator_name)

        # Check for family override on profile
        effective_profile = profile
        if family and family in config.family_overrides:
            family_cfg = config.family_overrides[family]
            if "profile" in family_cfg:
                effective_profile = family_cfg["profile"]

        # Get profile configuration
        profile_config = config.profiles.get(effective_profile)

        # Determine which rules are active
        active_rule_ids = set()
        if profile_config and profile_config.rules:
            active_rule_ids = set(profile_config.rules)
        else:
            # Default: all enabled rules
            active_rule_ids = set(r_id for r_id, rule in config.rules.items() if rule.enabled)

        # Build rules with profile overrides
        result: List[Rule] = []
        for rule_id in active_rule_ids:
            if rule_id not in config.rules:
                logger.warning(f"Rule '{rule_id}' in profile '{effective_profile}' not found in config")
                continue

            base_rule = config.rules[rule_id]
            if not base_rule.enabled:
                continue

            # Apply profile overrides
            rule = Rule(
                id=base_rule.id,
                enabled=base_rule.enabled,
                level=base_rule.level,
                message=base_rule.message,
                params=dict(base_rule.params)
            )

            if profile_config and rule_id in profile_config.overrides:
                overrides = profile_config.overrides[rule_id]
                if "level" in overrides:
                    rule.level = overrides["level"]
                if "enabled" in overrides:
                    rule.enabled = overrides["enabled"]
                if "params" in overrides:
                    rule.params.update(overrides["params"])

            # Apply family overrides
            if family and family in config.family_overrides:
                family_cfg = config.family_overrides[family]
                family_rules = family_cfg.get("rules", {})
                if rule_id in family_rules:
                    family_rule_cfg = family_rules[rule_id]
                    if "level" in family_rule_cfg:
                        rule.level = family_rule_cfg["level"]
                    if "enabled" in family_rule_cfg:
                        rule.enabled = family_rule_cfg["enabled"]
                    if "params" in family_rule_cfg:
                        rule.params.update(family_rule_cfg["params"])

            if rule.enabled:
                result.append(rule)

        return result

    def get_profile(self, validator_name: str, profile: str) -> Optional[ProfileConfig]:
        """
        Get a specific profile configuration.

        Args:
            validator_name: Name of the validator
            profile: Profile name

        Returns:
            ProfileConfig if found, None otherwise
        """
        config = self.load(validator_name)
        return config.profiles.get(profile)

    def get_family_override(
        self,
        validator_name: str,
        family: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get family-specific override configuration.

        Args:
            validator_name: Name of the validator
            family: Product family name (e.g., 'words', 'pdf', 'cells')

        Returns:
            Override dictionary if found, None otherwise
        """
        config = self.load(validator_name)
        return config.family_overrides.get(family)

    def reload(self, validator_name: Optional[str] = None) -> None:
        """
        Reload configuration from disk.

        Args:
            validator_name: Specific validator to reload, or None to clear all cache
        """
        if validator_name:
            if validator_name in self._cache:
                del self._cache[validator_name]
            if validator_name in self._file_mtimes:
                del self._file_mtimes[validator_name]
        else:
            self._cache.clear()
            self._file_mtimes.clear()

    def list_validators(self) -> List[str]:
        """
        List all available validator configurations.

        Returns:
            List of validator names that have config files
        """
        if not self.config_dir.exists():
            return []

        validators = []
        for path in self.config_dir.glob("*.yaml"):
            validators.append(path.stem)
        return sorted(validators)

    def _load_yaml(self, config_path: Path) -> Dict[str, Any]:
        """Load YAML file, return empty dict if not found."""
        if not config_path.exists():
            logger.debug(f"Config file not found: {config_path}")
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data else {}
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML config {config_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load config {config_path}: {e}")
            return {}

    def _parse_config(self, validator_name: str, raw_config: Dict[str, Any]) -> ValidatorConfig:
        """Parse raw YAML into ValidatorConfig structure."""
        # Config may be nested under validator name or at root
        config_data = raw_config.get(validator_name, raw_config)

        # Parse enabled and profile
        enabled = config_data.get("enabled", True)
        profile = config_data.get("profile", "default")

        # Parse rules
        rules: Dict[str, Rule] = {}
        rules_data = config_data.get("rules", {})
        for rule_id, rule_config in rules_data.items():
            if isinstance(rule_config, dict):
                rules[rule_id] = Rule(
                    id=rule_id,
                    enabled=rule_config.get("enabled", True),
                    level=rule_config.get("level", "warning"),
                    message=rule_config.get("message", ""),
                    params=rule_config.get("params", {})
                )

        # Parse profiles
        profiles: Dict[str, ProfileConfig] = {}
        profiles_data = config_data.get("profiles", {})
        for profile_name, profile_data in profiles_data.items():
            if isinstance(profile_data, dict):
                profiles[profile_name] = ProfileConfig(
                    name=profile_name,
                    rules=profile_data.get("rules", []),
                    overrides=profile_data.get("overrides", {})
                )
            else:
                # Handle empty profile
                profiles[profile_name] = ProfileConfig(name=profile_name)

        # Parse family overrides
        family_overrides: Dict[str, Dict[str, Any]] = {}
        family_data = config_data.get("family_overrides", {})
        for family_name, family_config in family_data.items():
            if isinstance(family_config, dict):
                family_overrides[family_name] = family_config

        return ValidatorConfig(
            name=validator_name,
            enabled=enabled,
            profile=profile,
            rules=rules,
            profiles=profiles,
            family_overrides=family_overrides,
            raw_config=config_data
        )


# Singleton instance for convenience
_default_loader: Optional[ConfigLoader] = None


def get_config_loader(config_dir: str = "./config") -> ConfigLoader:
    """
    Get the default ConfigLoader instance.

    Args:
        config_dir: Configuration directory path

    Returns:
        ConfigLoader singleton instance
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = ConfigLoader(config_dir)
    return _default_loader


def reset_config_loader() -> None:
    """Reset the default ConfigLoader instance (useful for testing)."""
    global _default_loader
    _default_loader = None
