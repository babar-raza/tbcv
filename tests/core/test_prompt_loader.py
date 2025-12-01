# tests/core/test_prompt_loader.py
"""
Unit tests for core/prompt_loader.py - PromptLoader.
Target coverage: 100% (Currently 0%)
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open

from core.prompt_loader import PromptLoader, get_prompt, format_prompt


@pytest.mark.unit
class TestPromptLoader:
    """Test PromptLoader class."""

    def test_initialization_default_dir(self):
        """Test PromptLoader initialization with default directory."""
        loader = PromptLoader()

        assert loader.prompts_dir is not None
        assert isinstance(loader.prompts_dir, Path)
        assert loader._cache == {}
        assert loader._loaded_files == set()

    def test_initialization_custom_dir(self, temp_dir):
        """Test PromptLoader initialization with custom directory."""
        loader = PromptLoader(str(temp_dir))

        assert loader.prompts_dir == temp_dir

    def test_initialization_nonexistent_dir(self, temp_dir):
        """Test initialization with nonexistent directory logs warning."""
        nonexistent = temp_dir / "nonexistent"

        with patch('core.prompt_loader.logger') as mock_logger:
            loader = PromptLoader(str(nonexistent))

            mock_logger.warning.assert_called_once()
            assert "not found" in mock_logger.warning.call_args[0][0]

    def test_load_file_success(self, temp_dir):
        """Test successfully loading a prompt file."""
        # Create a test prompt file
        prompts_data = {
            "test_prompt": "This is a test prompt",
            "another_prompt": {"template": "Another test", "description": "Description"}
        }

        prompt_file = temp_dir / "test_prompts.json"
        prompt_file.write_text(json.dumps(prompts_data))

        loader = PromptLoader(str(temp_dir))
        result = loader._load_file("test_prompts")

        assert result == prompts_data
        assert "test_prompts" in loader._cache
        assert "test_prompts" in loader._loaded_files

    def test_load_file_caching(self, temp_dir):
        """Test that loaded files are cached."""
        prompts_data = {"prompt": "Test"}
        prompt_file = temp_dir / "cached.json"
        prompt_file.write_text(json.dumps(prompts_data))

        loader = PromptLoader(str(temp_dir))

        # First load
        result1 = loader._load_file("cached")
        # Second load (should use cache)
        result2 = loader._load_file("cached")

        assert result1 == result2
        assert loader._cache["cached"] == prompts_data

    def test_load_file_not_found(self, temp_dir):
        """Test loading a nonexistent file."""
        loader = PromptLoader(str(temp_dir))

        with patch('core.prompt_loader.logger') as mock_logger:
            result = loader._load_file("nonexistent")

            assert result == {}
            assert loader._cache["nonexistent"] == {}
            mock_logger.warning.assert_called()

    def test_load_file_invalid_json(self, temp_dir):
        """Test loading a file with invalid JSON."""
        prompt_file = temp_dir / "invalid.json"
        prompt_file.write_text("{ invalid json }")

        loader = PromptLoader(str(temp_dir))

        with patch('core.prompt_loader.logger') as mock_logger:
            result = loader._load_file("invalid")

            assert result == {}
            mock_logger.error.assert_called()
            assert "Invalid JSON" in mock_logger.error.call_args[0][0]

    def test_load_file_read_error(self, temp_dir):
        """Test handling of file read errors."""
        # Create the file so file_path.exists() returns True
        error_file = temp_dir / "error.json"
        error_file.write_text("{}")  # Create valid JSON file

        loader = PromptLoader(str(temp_dir))

        with patch('builtins.open', side_effect=IOError("Cannot read")):
            with patch('core.prompt_loader.logger') as mock_logger:
                result = loader._load_file("error")

                assert result == {}
                mock_logger.error.assert_called()

    def test_get_prompt_string_format(self, temp_dir):
        """Test getting a prompt in string format."""
        prompts_data = {"simple": "This is a simple prompt"}
        prompt_file = temp_dir / "test.json"
        prompt_file.write_text(json.dumps(prompts_data))

        loader = PromptLoader(str(temp_dir))
        result = loader.get_prompt("test", "simple")

        assert result == "This is a simple prompt"

    def test_get_prompt_dict_format(self, temp_dir):
        """Test getting a prompt in dict format with template."""
        prompts_data = {
            "complex": {
                "template": "Complex prompt template",
                "description": "A complex prompt"
            }
        }
        prompt_file = temp_dir / "test.json"
        prompt_file.write_text(json.dumps(prompts_data))

        loader = PromptLoader(str(temp_dir))
        result = loader.get_prompt("test", "complex")

        assert result == "Complex prompt template"

    def test_get_prompt_not_found(self, temp_dir):
        """Test getting a nonexistent prompt."""
        prompts_data = {"exists": "Exists"}
        prompt_file = temp_dir / "test.json"
        prompt_file.write_text(json.dumps(prompts_data))

        loader = PromptLoader(str(temp_dir))

        with patch('core.prompt_loader.logger') as mock_logger:
            result = loader.get_prompt("test", "nonexistent")

            assert result == ""
            mock_logger.warning.assert_called()

    def test_get_prompt_invalid_format(self, temp_dir):
        """Test getting a prompt with invalid format."""
        prompts_data = {"invalid": ["not", "a", "string"]}
        prompt_file = temp_dir / "test.json"
        prompt_file.write_text(json.dumps(prompts_data))

        loader = PromptLoader(str(temp_dir))

        with patch('core.prompt_loader.logger') as mock_logger:
            result = loader.get_prompt("test", "invalid")

            assert result == ""
            mock_logger.warning.assert_called()

    def test_get_prompt_with_description(self, temp_dir):
        """Test getting prompt with description."""
        prompts_data = {
            "with_desc": {
                "template": "Template text",
                "description": "Description text"
            }
        }
        prompt_file = temp_dir / "test.json"
        prompt_file.write_text(json.dumps(prompts_data))

        loader = PromptLoader(str(temp_dir))
        result = loader.get_prompt_with_description("test", "with_desc")

        assert result["template"] == "Template text"
        assert result["description"] == "Description text"

    def test_get_prompt_with_description_string_format(self, temp_dir):
        """Test getting description for string-format prompt."""
        prompts_data = {"simple": "Simple string"}
        prompt_file = temp_dir / "test.json"
        prompt_file.write_text(json.dumps(prompts_data))

        loader = PromptLoader(str(temp_dir))
        result = loader.get_prompt_with_description("test", "simple")

        assert result["template"] == "Simple string"
        assert result["description"] == ""

    def test_format_prompt_success(self, temp_dir):
        """Test formatting a prompt with variables."""
        prompts_data = {
            "greeting": "Hello {name}, you are {age} years old"
        }
        prompt_file = temp_dir / "test.json"
        prompt_file.write_text(json.dumps(prompts_data))

        loader = PromptLoader(str(temp_dir))
        result = loader.format_prompt("test", "greeting", name="Alice", age=30)

        assert result == "Hello Alice, you are 30 years old"

    def test_format_prompt_missing_variable(self, temp_dir):
        """Test formatting with missing variable returns unformatted."""
        prompts_data = {"greeting": "Hello {name}"}
        prompt_file = temp_dir / "test.json"
        prompt_file.write_text(json.dumps(prompts_data))

        loader = PromptLoader(str(temp_dir))

        with patch('core.prompt_loader.logger') as mock_logger:
            result = loader.format_prompt("test", "greeting")

            # Should return unformatted template
            assert "{name}" in result
            mock_logger.error.assert_called()

    def test_format_prompt_nonexistent(self, temp_dir):
        """Test formatting a nonexistent prompt."""
        loader = PromptLoader(str(temp_dir))
        result = loader.format_prompt("test", "nonexistent", var="value")

        assert result == ""

    def test_list_files(self, temp_dir):
        """Test listing available prompt files."""
        # Create multiple prompt files
        (temp_dir / "file1.json").write_text(json.dumps({}))
        (temp_dir / "file2.json").write_text(json.dumps({}))
        (temp_dir / "file3.json").write_text(json.dumps({}))

        loader = PromptLoader(str(temp_dir))
        files = loader.list_files()

        assert len(files) == 3
        assert "file1" in files
        assert "file2" in files
        assert "file3" in files
        assert files == sorted(files)  # Should be sorted

    def test_list_files_empty_dir(self, temp_dir):
        """Test listing files in empty directory."""
        loader = PromptLoader(str(temp_dir))
        files = loader.list_files()

        assert files == []

    def test_list_files_nonexistent_dir(self, temp_dir):
        """Test listing files when directory doesn't exist."""
        nonexistent = temp_dir / "nonexistent"
        loader = PromptLoader(str(nonexistent))
        files = loader.list_files()

        assert files == []

    def test_list_prompts(self, temp_dir):
        """Test listing prompts in a file."""
        prompts_data = {
            "prompt1": "Test 1",
            "prompt2": "Test 2",
            "prompt3": "Test 3"
        }
        prompt_file = temp_dir / "test.json"
        prompt_file.write_text(json.dumps(prompts_data))

        loader = PromptLoader(str(temp_dir))
        prompts = loader.list_prompts("test")

        assert len(prompts) == 3
        assert "prompt1" in prompts
        assert "prompt2" in prompts
        assert "prompt3" in prompts

    def test_reload_file(self, temp_dir):
        """Test reloading a file from disk."""
        prompt_file = temp_dir / "reload.json"
        prompt_file.write_text(json.dumps({"v1": "Version 1"}))

        loader = PromptLoader(str(temp_dir))

        # Load initial version
        result1 = loader.get_prompt("reload", "v1")
        assert result1 == "Version 1"

        # Update file
        prompt_file.write_text(json.dumps({"v1": "Version 2"}))

        # Reload
        success = loader.reload_file("reload")
        assert success is True

        # Get updated version
        result2 = loader.get_prompt("reload", "v1")
        assert result2 == "Version 2"

    def test_reload_nonexistent_file(self, temp_dir):
        """Test reloading a nonexistent file."""
        loader = PromptLoader(str(temp_dir))
        success = loader.reload_file("nonexistent")

        assert success is False

    def test_clear_cache(self, temp_dir):
        """Test clearing the cache."""
        prompts_data = {"prompt": "Test"}
        prompt_file = temp_dir / "test.json"
        prompt_file.write_text(json.dumps(prompts_data))

        loader = PromptLoader(str(temp_dir))

        # Load file
        loader.get_prompt("test", "prompt")
        assert len(loader._cache) > 0
        assert len(loader._loaded_files) > 0

        # Clear cache
        loader.clear_cache()

        assert loader._cache == {}
        assert loader._loaded_files == set()


@pytest.mark.unit
class TestConvenienceFunctions:
    """Test global convenience functions."""

    def test_get_prompt_global(self):
        """Test global get_prompt function."""
        with patch('core.prompt_loader.prompt_loader') as mock_loader:
            mock_loader.get_prompt.return_value = "Test prompt"

            result = get_prompt("file", "key")

            assert result == "Test prompt"
            mock_loader.get_prompt.assert_called_once_with("file", "key")

    def test_format_prompt_global(self):
        """Test global format_prompt function."""
        with patch('core.prompt_loader.prompt_loader') as mock_loader:
            mock_loader.format_prompt.return_value = "Formatted: value"

            result = format_prompt("file", "key", param="value")

            assert result == "Formatted: value"
            mock_loader.format_prompt.assert_called_once_with("file", "key", param="value")


@pytest.mark.integration
class TestPromptLoaderIntegration:
    """Integration tests for PromptLoader."""

    def test_full_workflow(self, temp_dir):
        """Test complete prompt loading workflow."""
        # Create a realistic prompt file
        prompts = {
            "validation": {
                "template": "Validate {content} using {rules}",
                "description": "Validation prompt"
            },
            "enhancement": "Enhance {content}"
        }
        prompt_file = temp_dir / "validator.json"
        prompt_file.write_text(json.dumps(prompts))

        loader = PromptLoader(str(temp_dir))

        # Test listing
        assert "validator" in loader.list_files()

        # Test getting prompts
        validation = loader.get_prompt("validator", "validation")
        assert "Validate" in validation

        enhancement = loader.get_prompt("validator", "enhancement")
        assert "Enhance" in enhancement

        # Test formatting
        formatted = loader.format_prompt("validator", "validation", content="doc", rules="strict")
        assert "doc" in formatted
        assert "strict" in formatted

        # Test prompt listing
        prompts_list = loader.list_prompts("validator")
        assert len(prompts_list) == 2

    def test_backward_compatibility_functions(self):
        """Test backward compatibility functions."""
        from core.prompt_loader import get_contradiction_prompt, get_omission_prompt

        with patch('core.prompt_loader.format_prompt', return_value="Formatted"):
            # Test contradiction prompt
            result = get_contradiction_prompt("content", [], {}, {})
            assert result == "Formatted"

            # Test omission prompt
            result = get_omission_prompt("content", [], {}, {})
            assert result == "Formatted"
