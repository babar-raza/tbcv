# file: core\rule_manager.py
"""
Generic rule management system for family-specific validation rules.
Loads and manages API patterns, validation requirements, and plugin rules.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FamilyRules:
    """Container for family-specific validation rules."""
    family: str
    plugin_aliases: Dict[str, List[str]]
    api_patterns: Dict[str, List[str]]
    dependencies: Dict[str, List[str]]
    non_editable_yaml_fields: Set[str]
    validation_requirements: Dict[str, Any]
    code_quality_rules: Dict[str, Any]
    format_patterns: Dict[str, List[str]]

class RuleManager:
    """Manages family-specific validation rules loaded from JSON."""
    
    def __init__(self):
        self.rules_cache: Dict[str, FamilyRules] = {}
        self.rules_directory = Path("rules")
        self.global_non_editable_fields = {
            'layout', 'categories', 'date', 'draft', 'lastmod', 'title', 'weight', 'author'
        }
        
    def get_family_rules(self, family: str) -> FamilyRules:
        """Get rules for a specific family, loading if necessary."""
        if family not in self.rules_cache:
            self._load_family_rules(family)
        return self.rules_cache.get(family, self._get_default_rules(family))
    
    def _load_family_rules(self, family: str) -> None:
        """Load rules from JSON file for a family."""
        rules_file = self.rules_directory / f"{family}.json"
        
        try:
            if rules_file.exists():
                with open(rules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.rules_cache[family] = self._parse_rules_data(family, data)
                logger.info(f"Loaded rules for family: {family}")
            else:
                logger.warning(f"Rules file not found: {rules_file}, using defaults")
                self.rules_cache[family] = self._get_default_rules(family)
        except Exception as e:
            logger.error(f"Failed to load rules for {family}: {e}")
            self.rules_cache[family] = self._get_default_rules(family)
    
    def _parse_rules_data(self, family: str, data: Dict[str, Any]) -> FamilyRules:
        """Parse JSON data into FamilyRules structure."""
        return FamilyRules(
            family=family,
            plugin_aliases=data.get("plugin_aliases", {}),
            api_patterns=data.get("api_patterns", {}),
            dependencies=data.get("dependencies", {}),
            non_editable_yaml_fields=set(data.get("non_editable_yaml_fields", [])) | self.global_non_editable_fields,
            validation_requirements=data.get("validation_requirements", {}),
            code_quality_rules=data.get("code_quality_rules", {}),
            format_patterns=data.get("format_patterns", {})
        )
    
    def _get_default_rules(self, family: str) -> FamilyRules:
        """Get default rules when no JSON file exists."""
        return FamilyRules(
            family=family,
            plugin_aliases={},
            api_patterns={
                "document_creation": [r"new\s+\w+"],
                "save_operations": [r"\.Save\s*\("],
                "load_operations": [r"new\s+\w+\s*\("]
            },
            dependencies={},
            non_editable_yaml_fields=self.global_non_editable_fields.copy(),
            validation_requirements={},
            code_quality_rules={
                "forbidden_patterns": {
                    "hardcoded_paths": [r"C:\\\\", r"/Users/", r"C:/temp"],
                    "magic_numbers": [r"\\b\\d{2,}\\b(?!\\s*(px|em|%|ms|s))"]
                },
                "required_patterns": {
                    "error_handling": [r"try\\s*{", r"catch\\s*\\("],
                    "resource_disposal": [r"using\\s*\\(", r"\\.Dispose\\(\\)"]
                }
            },
            format_patterns={}
        )
    
    def get_api_patterns(self, family: str) -> Dict[str, List[str]]:
        """Get API patterns for a family."""
        rules = self.get_family_rules(family)
        return rules.api_patterns
    
    def get_plugin_aliases(self, family: str) -> Dict[str, List[str]]:
        """Get plugin aliases for a family."""
        rules = self.get_family_rules(family)
        return rules.plugin_aliases
    
    def get_dependencies(self, family: str, plugin_id: str) -> List[str]:
        """Get dependencies for a specific plugin."""
        rules = self.get_family_rules(family)
        return rules.dependencies.get(plugin_id, [])
    
    def get_non_editable_fields(self, family: str) -> Set[str]:
        """Get non-editable YAML fields for a family."""
        rules = self.get_family_rules(family)
        return rules.non_editable_yaml_fields
    
    def get_validation_requirements(self, family: str) -> Dict[str, Any]:
        """Get validation requirements for a family."""
        rules = self.get_family_rules(family)
        return rules.validation_requirements
    
    def get_code_quality_rules(self, family: str) -> Dict[str, Any]:
        """Get code quality rules for a family."""
        rules = self.get_family_rules(family)
        return rules.code_quality_rules
    
    def reload_rules(self, family: Optional[str] = None) -> None:
        """Reload rules from disk."""
        if family:
            if family in self.rules_cache:
                del self.rules_cache[family]
            self._load_family_rules(family)
        else:
            self.rules_cache.clear()
            logger.info("Cleared all rule caches")

# Global instance
rule_manager = RuleManager()
