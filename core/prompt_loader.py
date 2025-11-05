# file: core/prompt_loader.py
"""
Centralized prompt loader for TBCV system.
Loads prompts from JSON files in the prompts/ directory using only stdlib.
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PromptLoader:
    """
    Centralized prompt loader that loads and caches prompts from JSON files.
    
    Uses only Python standard library for loading and caching.
    Prompts are stored in the prompts/ directory as JSON files.
    """
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        Initialize the prompt loader.
        
        Args:
            prompts_dir: Path to prompts directory (defaults to ./prompts)
        """
        if prompts_dir is None:
            # Default to prompts directory relative to project root
            current_dir = Path(__file__).parent.parent
            prompts_dir = current_dir / "prompts"
        
        self.prompts_dir = Path(prompts_dir)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._loaded_files: set = set()
        
        if not self.prompts_dir.exists():
            logger.warning(f"Prompts directory not found: {self.prompts_dir}")
    
    def _load_file(self, file_key: str) -> Dict[str, Any]:
        """
        Load a prompt file from disk and cache it.
        
        Args:
            file_key: The file key (e.g., 'validator', 'enhancer')
            
        Returns:
            Dictionary containing the prompts from the file
        """
        if file_key in self._cache:
            return self._cache[file_key]
        
        file_path = self.prompts_dir / f"{file_key}.json"
        
        if not file_path.exists():
            logger.warning(f"Prompt file not found: {file_path}")
            self._cache[file_key] = {}
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._cache[file_key] = data
            self._loaded_files.add(file_key)
            logger.debug(f"Loaded prompts from {file_path}")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in prompt file {file_path}: {e}")
            self._cache[file_key] = {}
            return {}
        except Exception as e:
            logger.error(f"Error loading prompt file {file_path}: {e}")
            self._cache[file_key] = {}
            return {}
    
    def get_prompt(self, file_key: str, prompt_key: str) -> str:
        """
        Get a prompt template string.
        
        Args:
            file_key: The file key (e.g., 'validator', 'enhancer', 'code_analysis')
            prompt_key: The prompt key within the file
            
        Returns:
            The prompt template string, or empty string if not found
        """
        file_data = self._load_file(file_key)
        
        if prompt_key not in file_data:
            logger.warning(f"Prompt not found: {file_key}.{prompt_key}")
            return ""
        
        prompt_data = file_data[prompt_key]
        
        if isinstance(prompt_data, str):
            return prompt_data
        elif isinstance(prompt_data, dict) and 'template' in prompt_data:
            return prompt_data['template']
        else:
            logger.warning(f"Invalid prompt format for {file_key}.{prompt_key}")
            return ""
    
    def get_prompt_with_description(self, file_key: str, prompt_key: str) -> Dict[str, str]:
        """
        Get a prompt with its description.
        
        Args:
            file_key: The file key (e.g., 'validator', 'enhancer', 'code_analysis')
            prompt_key: The prompt key within the file
            
        Returns:
            Dictionary with 'template' and 'description' keys
        """
        file_data = self._load_file(file_key)
        
        if prompt_key not in file_data:
            logger.warning(f"Prompt not found: {file_key}.{prompt_key}")
            return {"template": "", "description": ""}
        
        prompt_data = file_data[prompt_key]
        
        if isinstance(prompt_data, str):
            return {"template": prompt_data, "description": ""}
        elif isinstance(prompt_data, dict):
            return {
                "template": prompt_data.get("template", ""),
                "description": prompt_data.get("description", "")
            }
        else:
            logger.warning(f"Invalid prompt format for {file_key}.{prompt_key}")
            return {"template": "", "description": ""}
    
    def format_prompt(self, file_key: str, prompt_key: str, **kwargs) -> str:
        """
        Get a prompt and format it with the provided arguments.
        
        Args:
            file_key: The file key (e.g., 'validator', 'enhancer', 'code_analysis')
            prompt_key: The prompt key within the file
            **kwargs: Arguments to format into the template
            
        Returns:
            The formatted prompt string
        """
        template = self.get_prompt(file_key, prompt_key)
        
        if not template:
            return ""
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing template argument for {file_key}.{prompt_key}: {e}")
            return template
        except Exception as e:
            logger.error(f"Error formatting prompt {file_key}.{prompt_key}: {e}")
            return template
    
    def list_files(self) -> list:
        """
        List available prompt files.
        
        Returns:
            List of available file keys
        """
        if not self.prompts_dir.exists():
            return []
        
        files = []
        for file_path in self.prompts_dir.glob("*.json"):
            files.append(file_path.stem)
        
        return sorted(files)
    
    def list_prompts(self, file_key: str) -> list:
        """
        List available prompts in a file.
        
        Args:
            file_key: The file key to list prompts for
            
        Returns:
            List of prompt keys in the file
        """
        file_data = self._load_file(file_key)
        return list(file_data.keys())
    
    def reload_file(self, file_key: str) -> bool:
        """
        Force reload a prompt file from disk.
        
        Args:
            file_key: The file key to reload
            
        Returns:
            True if successfully reloaded, False otherwise
        """
        if file_key in self._cache:
            del self._cache[file_key]
        
        if file_key in self._loaded_files:
            self._loaded_files.remove(file_key)
        
        data = self._load_file(file_key)
        return bool(data)
    
    def clear_cache(self):
        """Clear the entire cache and force reload on next access."""
        self._cache.clear()
        self._loaded_files.clear()


# Global instance
prompt_loader = PromptLoader()


# Convenience functions for common usage patterns
def get_prompt(file_key: str, prompt_key: str) -> str:
    """
    Get a prompt template string using the global loader.
    
    Args:
        file_key: The file key (e.g., 'validator', 'enhancer', 'code_analysis')
        prompt_key: The prompt key within the file
        
    Returns:
        The prompt template string
    """
    return prompt_loader.get_prompt(file_key, prompt_key)


def format_prompt(file_key: str, prompt_key: str, **kwargs) -> str:
    """
    Get and format a prompt using the global loader.
    
    Args:
        file_key: The file key (e.g., 'validator', 'enhancer', 'code_analysis')
        prompt_key: The prompt key within the file
        **kwargs: Arguments to format into the template
        
    Returns:
        The formatted prompt string
    """
    return prompt_loader.format_prompt(file_key, prompt_key, **kwargs)


# Backward compatibility functions for existing code
def get_contradiction_prompt(content: str, plugin_info: list, api_patterns: dict, validation_requirements: dict) -> str:
    """Backward compatibility function for contradiction prompt."""
    return format_prompt(
        'validator', 
        'contradiction_detection',
        content=content[:2000],
        plugin_info=json.dumps(plugin_info, indent=2),
        api_patterns=json.dumps(api_patterns, indent=2),
        validation_requirements=json.dumps(validation_requirements, indent=2)
    )


def get_omission_prompt(content: str, plugin_info: list, validation_requirements: dict, code_quality_rules: dict) -> str:
    """Backward compatibility function for omission prompt."""
    return format_prompt(
        'validator',
        'omission_detection', 
        content=content[:2000],
        plugin_info=json.dumps(plugin_info, indent=2),
        validation_requirements=json.dumps(validation_requirements, indent=2),
        code_quality_rules=json.dumps(code_quality_rules, indent=2)
    )
