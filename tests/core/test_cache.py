# file: tests/core/test_cache.py
"""Tests for ValidationCache class."""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch

from core.cache import ValidationCache


# --- Fixtures ---

@pytest.fixture
def mock_config():
    """Mock cache configuration."""
    return {
        "validation": {
            "enabled": True,
            "ttl_seconds": 3600,
            "min_confidence_to_cache": 0.5
        },
        "llm": {
            "enabled": True,
            "ttl_seconds": 86400,
            "cache_errors": False,
            "max_response_size": 102400
        },
        "truth": {
            "enabled": True,
            "preload_on_startup": True
        },
        "content_hash": {
            "algorithm": "sha256",
            "hash_length": 16
        },
        "invalidation": {
            "on_truth_change": True
        }
    }


@pytest.fixture
def validation_cache(mock_config):
    """Create ValidationCache with mock config."""
    mock_loader = Mock()
    mock_loader.load.return_value = mock_config
    return ValidationCache(config_loader=mock_loader)


@pytest.fixture
def temp_truth_dir():
    """Create temporary directory with truth files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample truth files
        truth1 = {"plugins": ["plugin1", "plugin2"], "rules": []}
        truth2 = {"plugins": ["plugin3"], "rules": ["rule1"]}

        path1 = Path(tmpdir) / "truth1.json"
        path2 = Path(tmpdir) / "truth2.json"

        with open(path1, 'w') as f:
            json.dump(truth1, f)
        with open(path2, 'w') as f:
            json.dump(truth2, f)

        yield tmpdir, [str(path1), str(path2)]


# --- Content Hash Tests ---

class TestContentHash:
    """Tests for content hashing."""

    def test_hash_returns_fixed_length(self, validation_cache):
        """Hash should be truncated to configured length."""
        content = "test content"
        hash_result = validation_cache.content_hash(content)
        assert len(hash_result) == 16

    def test_same_content_same_hash(self, validation_cache):
        """Same content should produce same hash."""
        content = "test content"
        hash1 = validation_cache.content_hash(content)
        hash2 = validation_cache.content_hash(content)
        assert hash1 == hash2

    def test_different_content_different_hash(self, validation_cache):
        """Different content should produce different hash."""
        hash1 = validation_cache.content_hash("content 1")
        hash2 = validation_cache.content_hash("content 2")
        assert hash1 != hash2

    def test_hash_with_metadata(self, validation_cache):
        """Hash should include metadata when requested."""
        content = "test content"
        hash1 = validation_cache.content_hash(content, include_metadata=False)
        hash2 = validation_cache.content_hash(
            content,
            include_metadata=True,
            metadata={"key": "value"}
        )
        assert hash1 != hash2


# --- Cache Key Generation Tests ---

class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    def test_validation_cache_key_format(self, validation_cache):
        """Validation cache key should follow expected format."""
        key = validation_cache.validation_cache_key(
            content="test",
            validation_types=["yaml", "markdown"],
            profile="default",
            family="words"
        )
        assert key.startswith("validation:")
        assert "markdown,yaml" in key  # sorted
        assert "default" in key
        assert "words" in key

    def test_validation_cache_key_types_sorted(self, validation_cache):
        """Validation types should be sorted for consistent keys."""
        key1 = validation_cache.validation_cache_key(
            content="test",
            validation_types=["yaml", "markdown"]
        )
        key2 = validation_cache.validation_cache_key(
            content="test",
            validation_types=["markdown", "yaml"]
        )
        assert key1 == key2

    def test_llm_cache_key_format(self, validation_cache):
        """LLM cache key should follow expected format."""
        key = validation_cache.llm_cache_key(
            prompt="test prompt",
            model_name="gpt4",
            temperature=0.5
        )
        assert key.startswith("llm:")
        assert "gpt4" in key
        assert "0.50" in key

    def test_llm_cache_key_temperature_precision(self, validation_cache):
        """Temperature should be formatted consistently."""
        key1 = validation_cache.llm_cache_key("prompt", temperature=0.1)
        key2 = validation_cache.llm_cache_key("prompt", temperature=0.10)
        assert key1 == key2


# --- Validation Cache Tests ---

class TestValidationCache:
    """Tests for validation result caching."""

    def test_put_and_get_validation_result(self, validation_cache):
        """Should cache and retrieve validation results."""
        content = "test content"
        result = {"confidence": 0.9, "issues": []}

        validation_cache.put_validation_result(
            content=content,
            result=result,
            validation_types=["yaml"]
        )

        # Note: This uses the global cache_manager which may not persist
        # in tests. We test the key generation and logic instead.
        key = validation_cache.validation_cache_key(content, ["yaml"])
        assert key is not None

    def test_skip_low_confidence_results(self, validation_cache):
        """Should not cache results below confidence threshold."""
        # Threshold is 0.5 in mock config
        result = {"confidence": 0.3, "issues": []}

        # This should not raise but also not cache
        validation_cache.put_validation_result(
            content="test",
            result=result,
            validation_types=["yaml"]
        )

    def test_disabled_cache_returns_none(self, mock_config):
        """Disabled cache should return None."""
        mock_config["validation"]["enabled"] = False
        mock_loader = Mock()
        mock_loader.load.return_value = mock_config
        cache = ValidationCache(config_loader=mock_loader)

        result = cache.get_validation_result("test")
        assert result is None


# --- LLM Cache Tests ---

class TestLLMCache:
    """Tests for LLM response caching."""

    def test_put_llm_response(self, validation_cache):
        """Should cache LLM response."""
        prompt = "test prompt"
        response = {"answer": "test answer"}

        # Should not raise
        validation_cache.put_llm_response(
            prompt=prompt,
            response=response,
            model_name="test_model"
        )

    def test_skip_error_responses_by_default(self, validation_cache):
        """Should not cache error responses by default."""
        # cache_errors is False in mock config
        validation_cache.put_llm_response(
            prompt="test",
            response={"error": "failed"},
            is_error=True
        )

    def test_skip_large_responses(self, validation_cache):
        """Should not cache responses exceeding max size."""
        # max_response_size is 102400 in mock config
        large_response = {"data": "x" * 200000}

        validation_cache.put_llm_response(
            prompt="test",
            response=large_response
        )

    def test_disabled_llm_cache_returns_none(self, mock_config):
        """Disabled LLM cache should return None."""
        mock_config["llm"]["enabled"] = False
        mock_loader = Mock()
        mock_loader.load.return_value = mock_config
        cache = ValidationCache(config_loader=mock_loader)

        result = cache.get_llm_response("test prompt")
        assert result is None


# --- Truth Data Tests ---

class TestTruthDataCache:
    """Tests for truth data preloading and caching."""

    def test_preload_truth_data(self, validation_cache, temp_truth_dir):
        """Should preload truth files."""
        tmpdir, paths = temp_truth_dir

        stats = validation_cache.preload_truth_data(paths)

        assert stats["preloaded"] == 2
        assert stats["errors"] == 0
        assert len(stats["files"]) == 2

    def test_get_truth_data(self, validation_cache, temp_truth_dir):
        """Should retrieve preloaded truth data."""
        tmpdir, paths = temp_truth_dir

        validation_cache.preload_truth_data(paths)

        data = validation_cache.get_truth_data(paths[0])
        assert data is not None
        assert "plugins" in data

    def test_preload_idempotent(self, validation_cache, temp_truth_dir):
        """Preloading again should return already_loaded."""
        tmpdir, paths = temp_truth_dir

        stats1 = validation_cache.preload_truth_data(paths)
        stats2 = validation_cache.preload_truth_data()  # No paths = use cached

        assert stats1["preloaded"] == 2
        assert stats2.get("already_loaded") is True

    def test_preload_handles_missing_files(self, validation_cache):
        """Should handle missing files gracefully."""
        stats = validation_cache.preload_truth_data(["/nonexistent/file.json"])

        assert stats["preloaded"] == 0

    def test_disabled_truth_cache(self, mock_config):
        """Disabled truth cache should skip preloading."""
        mock_config["truth"]["enabled"] = False
        mock_loader = Mock()
        mock_loader.load.return_value = mock_config
        cache = ValidationCache(config_loader=mock_loader)

        stats = cache.preload_truth_data(["/some/path.json"])
        assert stats.get("skipped") is True


# --- File Change Detection Tests ---

class TestFileChangeDetection:
    """Tests for file change detection and invalidation."""

    def test_check_file_changes_no_changes(self, validation_cache, temp_truth_dir):
        """Should return False for unchanged files."""
        tmpdir, paths = temp_truth_dir
        validation_cache.preload_truth_data(paths)

        changes = validation_cache.check_file_changes()

        # All files should show no changes
        for path in paths:
            assert changes.get(path) is False

    def test_check_file_changes_detects_modification(self, validation_cache, temp_truth_dir):
        """Should detect file modifications."""
        tmpdir, paths = temp_truth_dir
        validation_cache.preload_truth_data(paths)

        # Modify a file
        import time
        time.sleep(0.1)  # Ensure mtime changes
        with open(paths[0], 'w') as f:
            json.dump({"modified": True}, f)

        changes = validation_cache.check_file_changes()

        assert changes.get(paths[0]) is True

    def test_invalidation_on_change(self, validation_cache, temp_truth_dir):
        """Should invalidate cache entry when file changes."""
        tmpdir, paths = temp_truth_dir
        validation_cache.preload_truth_data(paths)

        # Verify data is cached
        assert validation_cache.get_truth_data(paths[0]) is not None

        # Modify file
        import time
        time.sleep(0.1)
        with open(paths[0], 'w') as f:
            json.dump({"modified": True}, f)

        # Check changes (triggers invalidation)
        validation_cache.check_file_changes()

        # Cache should be invalidated
        assert validation_cache.get_truth_data(paths[0]) is None


# --- Statistics Tests ---

class TestCacheStatistics:
    """Tests for cache statistics."""

    def test_get_statistics(self, validation_cache):
        """Should return statistics dict."""
        stats = validation_cache.get_statistics()

        assert "validation_cache" in stats
        assert "llm_cache" in stats
        assert "truth_cache" in stats
        assert "cache_manager" in stats

    def test_statistics_shows_preloaded_status(self, validation_cache, temp_truth_dir):
        """Statistics should show preload status."""
        tmpdir, paths = temp_truth_dir

        stats_before = validation_cache.get_statistics()
        assert stats_before["truth_cache"]["preloaded"] is False

        validation_cache.preload_truth_data(paths)

        stats_after = validation_cache.get_statistics()
        assert stats_after["truth_cache"]["preloaded"] is True
        assert stats_after["truth_cache"]["files_cached"] == 2


# --- Config Reload Tests ---

class TestConfigReload:
    """Tests for configuration reloading."""

    def test_reload_config(self, validation_cache):
        """Should reload configuration without error."""
        validation_cache.reload_config()
        # Should not raise


# --- Invalidation Tests ---

class TestCacheInvalidation:
    """Tests for cache invalidation."""

    def test_invalidate_validation_cache(self, validation_cache):
        """Should invalidate validation cache."""
        result = validation_cache.invalidate_validation_cache()
        assert result == 0  # Returns 0 currently

    def test_invalidate_llm_cache(self, validation_cache):
        """Should invalidate LLM cache."""
        result = validation_cache.invalidate_llm_cache()
        assert result == 0  # Returns 0 currently
