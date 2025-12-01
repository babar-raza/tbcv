# file: tests/core/test_embeddings.py
"""Tests for EmbeddingService - RAG embedding generation."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

from core.embeddings import (
    EmbeddingService,
    EmbeddingResult,
    EmbeddingCache,
    get_embedding_service
)


# --- EmbeddingCache Tests ---

class TestEmbeddingCache:
    """Tests for EmbeddingCache."""

    def test_cache_init(self):
        """Should initialize with default values."""
        cache = EmbeddingCache()
        assert cache.max_entries == 10000
        assert cache.ttl_seconds == 86400

    def test_cache_put_get(self):
        """Should store and retrieve embeddings."""
        cache = EmbeddingCache()
        embedding = [0.1, 0.2, 0.3]

        cache.put("test text", "model", embedding)
        result = cache.get("test text", "model")

        assert result == embedding

    def test_cache_miss(self):
        """Should return None for missing entries."""
        cache = EmbeddingCache()
        result = cache.get("not in cache", "model")
        assert result is None

    def test_cache_different_models(self):
        """Different models should have separate cache entries."""
        cache = EmbeddingCache()

        cache.put("text", "model1", [1.0, 2.0])
        cache.put("text", "model2", [3.0, 4.0])

        assert cache.get("text", "model1") == [1.0, 2.0]
        assert cache.get("text", "model2") == [3.0, 4.0]

    def test_cache_stats(self):
        """Should track cache statistics."""
        cache = EmbeddingCache()

        cache.put("text1", "model", [1.0])
        cache.get("text1", "model")  # hit
        cache.get("text2", "model")  # miss

        stats = cache.get_stats()
        assert stats["entries"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_cache_clear(self):
        """Should clear all entries."""
        cache = EmbeddingCache()
        cache.put("text", "model", [1.0])

        cache.clear()

        assert cache.get("text", "model") is None
        stats = cache.get_stats()
        assert stats["entries"] == 0

    def test_cache_eviction(self):
        """Should evict oldest entries when full."""
        cache = EmbeddingCache(max_entries=5)

        for i in range(6):
            cache.put(f"text{i}", "model", [float(i)])

        # Should have evicted some entries
        assert cache.get_stats()["entries"] <= 5


# --- EmbeddingResult Tests ---

class TestEmbeddingResult:
    """Tests for EmbeddingResult dataclass."""

    def test_result_with_embedding(self):
        """Should store embedding successfully."""
        result = EmbeddingResult(
            embedding=[0.1, 0.2, 0.3],
            text="test",
            model="nomic"
        )
        assert result.embedding == [0.1, 0.2, 0.3]
        assert result.error is None

    def test_result_with_error(self):
        """Should store error information."""
        result = EmbeddingResult(
            embedding=None,
            text="test",
            model="nomic",
            error="Service unavailable"
        )
        assert result.embedding is None
        assert result.error == "Service unavailable"

    def test_result_cached_flag(self):
        """Should track cached status."""
        result = EmbeddingResult(
            embedding=[0.1],
            text="test",
            model="nomic",
            cached=True
        )
        assert result.cached is True


# --- EmbeddingService Tests ---

class TestEmbeddingService:
    """Tests for EmbeddingService."""

    @pytest.fixture
    def mock_config(self):
        """Mock RAG configuration."""
        return {
            "rag": {
                "embedding": {
                    "model": "nomic-embed-text",
                    "base_url": "http://localhost:11434",
                    "batch_size": 10
                },
                "cache": {
                    "enabled": True,
                    "max_entries": 100,
                    "ttl_seconds": 3600
                }
            }
        }

    @pytest.fixture
    def service(self, mock_config):
        """Create EmbeddingService with mock config."""
        with patch('core.embeddings.get_config_loader') as mock_loader:
            mock_loader.return_value.load.return_value = mock_config
            return EmbeddingService()

    def test_init_loads_config(self, service):
        """Should load configuration on init."""
        assert service.model == "nomic-embed-text"
        assert "localhost" in service.base_url

    def test_init_with_custom_model(self):
        """Should accept custom model parameter."""
        with patch('core.embeddings.get_config_loader') as mock_loader:
            mock_loader.return_value.load.return_value = {}
            service = EmbeddingService(model="custom-model")
            assert service.model == "custom-model"

    def test_cache_disabled(self):
        """Should work without cache."""
        with patch('core.embeddings.get_config_loader') as mock_loader:
            mock_loader.return_value.load.return_value = {}
            service = EmbeddingService(cache_enabled=False)
            assert service._cache is None

    @pytest.mark.asyncio
    async def test_is_available_when_service_up(self, service):
        """Should return True when service is available."""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "models": [{"name": "nomic-embed-text:latest"}]
            })
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_session.return_value)
            mock_session.return_value.__aexit__ = AsyncMock()
            mock_session.return_value.get = MagicMock(return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_response),
                __aexit__=AsyncMock()
            ))

            result = await service.is_available()
            assert result is True

    @pytest.mark.asyncio
    async def test_is_available_when_service_down(self, service):
        """Should return False when service is unavailable."""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(
                side_effect=Exception("Connection refused")
            )

            result = await service.is_available()
            assert result is False

    @pytest.mark.asyncio
    async def test_get_embedding_returns_cached(self, service):
        """Should return cached embedding if available."""
        # Pre-populate cache
        test_embedding = [0.1, 0.2, 0.3]
        service._cache.put("test text", service.model, test_embedding)

        result = await service.get_embedding("test text")

        assert result.embedding == test_embedding
        assert result.cached is True

    @pytest.mark.asyncio
    async def test_get_embedding_service_unavailable(self, service):
        """Should return error when service unavailable."""
        service._available = False

        result = await service.get_embedding("test text", use_cache=False)

        assert result.embedding is None
        assert "not available" in result.error

    @pytest.mark.asyncio
    async def test_get_embeddings_batch_uses_cache(self, service):
        """Should use cache for batch requests."""
        # Pre-populate cache for one text
        service._cache.put("text1", service.model, [1.0, 2.0])

        with patch.object(service, 'get_embedding', wraps=service.get_embedding) as mock_get:
            # Mock for non-cached texts
            mock_get.side_effect = [
                EmbeddingResult(embedding=[1.0, 2.0], text="text1", model=service.model, cached=True),
                EmbeddingResult(embedding=[3.0, 4.0], text="text2", model=service.model)
            ]

            results = await service.get_embeddings_batch(["text1", "text2"])

            assert len(results) == 2
            # First should be from cache
            assert results[0].cached is True

    def test_get_cache_stats(self, service):
        """Should return cache statistics."""
        stats = service.get_cache_stats()
        assert "entries" in stats
        assert "hits" in stats

    def test_clear_cache(self, service):
        """Should clear the cache."""
        service._cache.put("text", service.model, [1.0])
        service.clear_cache()
        assert service._cache.get("text", service.model) is None


# --- Module-level singleton Tests ---

class TestGetEmbeddingService:
    """Tests for get_embedding_service singleton."""

    def test_returns_singleton(self):
        """Should return same instance."""
        with patch('core.embeddings.get_config_loader') as mock_loader:
            mock_loader.return_value.load.return_value = {}

            # Reset singleton
            import core.embeddings
            core.embeddings._embedding_service = None

            service1 = get_embedding_service()
            service2 = get_embedding_service()

            assert service1 is service2
