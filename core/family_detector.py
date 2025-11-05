# file: tbcv/core/family_detector.py
"""
Family detection logic for TBCV system.
Automatically detects document families based on YAML front-matter, path heuristics, and available rules/truth files.
"""

import os
import re
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

from .io_win import read_text


class FamilyDetector:
    """Detects document family from various sources."""
    
    def __init__(self, rules_dir: str = "rules", truth_dir: str = "truth"):
        """
        Initialize family detector.
        
        Args:
            rules_dir: Directory containing rule files
            truth_dir: Directory containing truth files
        """
        self.rules_dir = Path(rules_dir)
        self.truth_dir = Path(truth_dir)
        
    def detect_family(self, file_path: str) -> Optional[str]:
        """
        Detect family for a given file.
        
        Priority:
        1. YAML front-matter family field
        2. Path heuristics
        3. Available rules/truth files
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Detected family name or None
        """
        file_path = Path(file_path)
        
        # Try YAML front-matter first
        family = self._detect_from_yaml(file_path)
        if family:
            return family
            
        # Try path heuristics
        family = self._detect_from_path(file_path)
        if family:
            return family
            
        # Default based on available rules/truth
        return self._detect_from_available_files()
    
    def _detect_from_yaml(self, file_path: Path) -> Optional[str]:
        """Extract family from YAML front-matter."""
        try:
            content = read_text(file_path)
            
            # Check for YAML front-matter
            if not content.startswith("---"):
                return None
                
            # Extract front-matter
            parts = content.split("---", 2)
            if len(parts) < 3:
                return None
                
            yaml_content = parts[1].strip()
            if not yaml_content:
                return None
                
            # Parse YAML
            front_matter = yaml.safe_load(yaml_content)
            if isinstance(front_matter, dict):
                return front_matter.get("family")
                
        except Exception:
            # Ignore YAML parsing errors
            pass
            
        return None
    
    def _detect_from_path(self, file_path: Path) -> Optional[str]:
        """Detect family from path patterns."""
        path_str = str(file_path).lower()
        
        # Common path patterns
        if "word" in path_str or "vocab" in path_str or "dictionary" in path_str:
            return "words"
        
        if "code" in path_str or "programming" in path_str or "script" in path_str:
            return "code"
            
        if "config" in path_str or "setting" in path_str:
            return "config"
            
        return None
    
    def _detect_from_available_files(self) -> Optional[str]:
        """Detect family based on available rules/truth files."""
        # Check what families we have rules for
        available_families = set()
        
        if self.rules_dir.exists():
            for rule_file in self.rules_dir.glob("*.json"):
                family = rule_file.stem
                available_families.add(family)
                
        if self.truth_dir.exists():
            for truth_file in self.truth_dir.glob("*.json"):
                family = truth_file.stem
                available_families.add(family)
        
        # Default to "words" if available, otherwise first available
        if "words" in available_families:
            return "words"
        elif available_families:
            return sorted(available_families)[0]
            
        return None
    
    def get_available_families(self) -> list[str]:
        """Get list of all available families."""
        families = set()
        
        if self.rules_dir.exists():
            for rule_file in self.rules_dir.glob("*.json"):
                families.add(rule_file.stem)
                
        if self.truth_dir.exists():
            for truth_file in self.truth_dir.glob("*.json"):
                families.add(truth_file.stem)
                
        return sorted(families)
    
    def has_family_support(self, family: str) -> bool:
        """Check if a family has rules and/or truth files."""
        rules_exist = (self.rules_dir / f"{family}.json").exists()
        truth_exists = (self.truth_dir / f"{family}.json").exists()
        return rules_exist or truth_exists


# Global instance
family_detector = FamilyDetector()
