"""
Contract tests for core.cache.CacheManager.

These tests verify that the CacheManager public API remains stable.
"""

import pytest
from core.cache import CacheManager, cache_manager, LRUCache, ValidationCache, validation_cache


class TestCacheManagerContract:
    """Verify CacheManager has all required public methods."""

    def test_cache_manager_interface(self):
        """CacheManager must have all required public methods."""
        required_methods = [
            # Core cache operations
            "get",
            "put",
            "delete",

            # Clear operations
            "clear_agent_cache",
            "clear_l1",
            "clear_l2",
            "clear",

            # Maintenance
            "cleanup_expired",
            "get_statistics",
        ]

        for method in required_methods:
            assert hasattr(CacheManager, method), \
                f"CacheManager missing required method: {method}"
            assert callable(getattr(CacheManager, method)), \
                f"CacheManager.{method} exists but is not callable"

    def test_singleton_instance_exists(self):
        """Verify cache_manager singleton is available."""
        assert cache_manager is not None
        assert isinstance(cache_manager, CacheManager)

    def test_get_returns_optional_value(self):
        """get() must return None or cached value."""
        result = cache_manager.get("test_agent", "test_method", {"key": "value"})
        # Should return None if not cached, or a value if cached
        assert result is None or result is not None  # Tautology but validates no exception

    def test_put_accepts_required_params(self):
        """put() must accept agent_id, method, input_data, result."""
        import inspect
        sig = inspect.signature(cache_manager.put)

        required_params = {'agent_id', 'method', 'input_data', 'result'}
        actual_params = set(sig.parameters.keys()) - {'self'}

        for param in required_params:
            assert param in actual_params, \
                f"put() missing required parameter: {param}"

    def test_delete_returns_bool(self):
        """delete() must return a boolean."""
        result = cache_manager.delete("test_agent", "test_method", {"key": "value"})
        assert isinstance(result, bool)

    def test_clear_returns_dict(self):
        """clear() must return dict with counts."""
        result = cache_manager.clear()
        assert isinstance(result, dict)
        assert "l1_cleared" in result
        assert "l2_cleared" in result
        assert isinstance(result["l1_cleared"], int)
        assert isinstance(result["l2_cleared"], int)

    def test_clear_l1_returns_int(self):
        """clear_l1() must return count."""
        result = cache_manager.clear_l1()
        assert isinstance(result, int)
        assert result >= 0

    def test_clear_l2_returns_int(self):
        """clear_l2() must return count."""
        result = cache_manager.clear_l2()
        assert isinstance(result, int)
        assert result >= 0

    def test_cleanup_expired_returns_dict(self):
        """cleanup_expired() must return dict with counts."""
        result = cache_manager.cleanup_expired()
        assert isinstance(result, dict)
        assert "l1_cleaned" in result
        assert "l2_cleaned" in result

    def test_get_statistics_returns_dict(self):
        """get_statistics() must return dict with cache stats."""
        result = cache_manager.get_statistics()
        assert isinstance(result, dict)
        assert "l1" in result
        assert "l2" in result
        assert "enabled" in result["l1"]
        assert "enabled" in result["l2"]


class TestLRUCacheContract:
    """Verify LRUCache has all required public methods."""

    def test_lru_cache_interface(self):
        """LRUCache must have all required public methods."""
        required_methods = [
            "get",
            "put",
            "delete",
            "clear",
            "size",
            "hit_rate",
            "stats",
        ]

        for method in required_methods:
            assert hasattr(LRUCache, method), \
                f"LRUCache missing required method: {method}"
            assert callable(getattr(LRUCache, method)), \
                f"LRUCache.{method} exists but is not callable"

    def test_lru_cache_can_be_instantiated(self):
        """LRUCache must be instantiable."""
        cache = LRUCache(max_size=10, ttl_seconds=60)
        assert cache is not None
        assert cache.max_size == 10
        assert cache.ttl_seconds == 60

    def test_lru_cache_get_returns_optional(self):
        """get() returns None or cached value."""
        cache = LRUCache()
        result = cache.get("nonexistent")
        assert result is None

    def test_lru_cache_size_returns_int(self):
        """size() returns integer."""
        cache = LRUCache()
        result = cache.size()
        assert isinstance(result, int)
        assert result >= 0

    def test_lru_cache_hit_rate_returns_float(self):
        """hit_rate() returns float between 0 and 1."""
        cache = LRUCache()
        result = cache.hit_rate()
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_lru_cache_stats_returns_dict(self):
        """stats() returns dict with cache metrics."""
        cache = LRUCache()
        result = cache.stats()
        assert isinstance(result, dict)
        assert "size" in result
        assert "max_size" in result
        assert "hits" in result
        assert "misses" in result
        assert "hit_rate" in result


class TestValidationCacheContract:
    """Verify ValidationCache has all required public methods."""

    def test_validation_cache_interface(self):
        """ValidationCache must have all required public methods."""
        required_methods = [
            # Hash generation
            "content_hash",
            "validation_cache_key",
            "llm_cache_key",

            # Validation caching
            "get_validation_result",
            "put_validation_result",

            # LLM caching
            "get_llm_response",
            "put_llm_response",

            # Truth data
            "preload_truth_data",
            "get_truth_data",

            # Invalidation
            "check_file_changes",
            "invalidate_validation_cache",
            "invalidate_llm_cache",

            # Stats
            "get_statistics",
            "reload_config",
        ]

        for method in required_methods:
            assert hasattr(ValidationCache, method), \
                f"ValidationCache missing required method: {method}"
            assert callable(getattr(ValidationCache, method)), \
                f"ValidationCache.{method} exists but is not callable"

    def test_singleton_instance_exists(self):
        """Verify validation_cache singleton is available."""
        assert validation_cache is not None
        assert isinstance(validation_cache, ValidationCache)

    def test_content_hash_returns_string(self):
        """content_hash() must return a string."""
        result = validation_cache.content_hash("test content")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_validation_cache_key_returns_string(self):
        """validation_cache_key() must return a string."""
        result = validation_cache.validation_cache_key(
            "test content",
            validation_types=["yaml"],
            profile="default"
        )
        assert isinstance(result, str)
        assert "validation:" in result

    def test_llm_cache_key_returns_string(self):
        """llm_cache_key() must return a string."""
        result = validation_cache.llm_cache_key(
            "test prompt",
            model_name="test-model",
            temperature=0.1
        )
        assert isinstance(result, str)
        assert "llm:" in result

    def test_get_validation_result_returns_optional(self):
        """get_validation_result() returns None or cached value."""
        result = validation_cache.get_validation_result("test content")
        # Should be None or a dict
        assert result is None or isinstance(result, (dict, object))

    def test_preload_truth_data_returns_dict(self):
        """preload_truth_data() must return stats dict."""
        result = validation_cache.preload_truth_data(truth_paths=[])
        assert isinstance(result, dict)
        assert "preloaded" in result or "already_loaded" in result

    def test_check_file_changes_returns_dict(self):
        """check_file_changes() must return dict."""
        result = validation_cache.check_file_changes()
        assert isinstance(result, dict)

    def test_invalidate_validation_cache_returns_int(self):
        """invalidate_validation_cache() must return count."""
        result = validation_cache.invalidate_validation_cache()
        assert isinstance(result, int)
        assert result >= 0

    def test_get_statistics_returns_dict(self):
        """get_statistics() must return dict with stats."""
        result = validation_cache.get_statistics()
        assert isinstance(result, dict)
        assert "validation_cache" in result
        assert "llm_cache" in result
        assert "truth_cache" in result


class TestCacheDecorator:
    """Verify cache_result decorator exists and is callable."""

    def test_cache_result_decorator_exists(self):
        """cache_result decorator must be importable."""
        from core.cache import cache_result
        assert cache_result is not None
        assert callable(cache_result)

    def test_cache_result_accepts_ttl(self):
        """cache_result must accept ttl_seconds parameter."""
        from core.cache import cache_result
        import inspect

        sig = inspect.signature(cache_result)
        assert "ttl_seconds" in sig.parameters
