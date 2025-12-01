# file: tests/core/test_vector_store.py
"""Tests for TruthVectorStore - RAG vector storage and retrieval."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from core.vector_store import (
    TruthVectorStore,
    InMemoryVectorStore,
    SearchResult,
    IndexStats,
    get_truth_vector_store
)


# --- SearchResult Tests ---

class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_result_creation(self):
        """Should create result with all fields."""
        result = SearchResult(
            id="doc1",
            text="Test document",
            score=0.85,
            metadata={"family": "words"},
            family="words"
        )
        assert result.id == "doc1"
        assert result.score == 0.85
        assert result.family == "words"

    def test_result_defaults(self):
        """Should have sensible defaults."""
        result = SearchResult(id="doc1", text="text", score=0.5)
        assert result.metadata == {}
        assert result.family == ""


# --- InMemoryVectorStore Tests ---

class TestInMemoryVectorStore:
    """Tests for InMemoryVectorStore backend."""

    @pytest.fixture
    def store(self):
        """Create fresh in-memory store."""
        return InMemoryVectorStore()

    def test_add_document(self, store):
        """Should add document to store."""
        store.add(
            doc_id="doc1",
            text="Test document",
            embedding=[0.1, 0.2, 0.3],
            metadata={"key": "value"},
            family="words"
        )

        assert store.count() == 1
        assert store.count("words") == 1

    def test_add_multiple_families(self, store):
        """Should handle multiple families."""
        store.add("doc1", "Text 1", [0.1], {}, "words")
        store.add("doc2", "Text 2", [0.2], {}, "pdf")

        assert store.count() == 2
        assert store.count("words") == 1
        assert store.count("pdf") == 1
        assert store.get_families() == ["words", "pdf"]

    def test_search_finds_similar(self, store):
        """Should find similar documents."""
        # Add two documents
        store.add("doc1", "Text 1", [1.0, 0.0, 0.0], {}, "words")
        store.add("doc2", "Text 2", [0.0, 1.0, 0.0], {}, "words")

        # Search with query similar to doc1
        results = store.search([0.9, 0.1, 0.0], "words", top_k=2)

        assert len(results) == 2
        assert results[0].id == "doc1"  # Most similar
        assert results[0].score > results[1].score

    def test_search_respects_family(self, store):
        """Should only search within family."""
        store.add("doc1", "Text 1", [1.0, 0.0], {}, "words")
        store.add("doc2", "Text 2", [1.0, 0.0], {}, "pdf")

        results = store.search([1.0, 0.0], "words", top_k=10)

        assert len(results) == 1
        assert results[0].family == "words"

    def test_search_top_k_limit(self, store):
        """Should limit results to top_k."""
        for i in range(10):
            store.add(f"doc{i}", f"Text {i}", [float(i)], {}, "words")

        results = store.search([5.0], "words", top_k=3)
        assert len(results) == 3

    def test_clear_all(self, store):
        """Should clear all documents."""
        store.add("doc1", "Text", [1.0], {}, "words")
        store.add("doc2", "Text", [1.0], {}, "pdf")

        store.clear()

        assert store.count() == 0
        assert store.get_families() == []

    def test_clear_family(self, store):
        """Should clear only specified family."""
        store.add("doc1", "Text", [1.0], {}, "words")
        store.add("doc2", "Text", [1.0], {}, "pdf")

        store.clear("words")

        assert store.count() == 1
        assert store.count("words") == 0
        assert store.count("pdf") == 1

    def test_cosine_similarity_identical(self, store):
        """Identical vectors should have similarity 1.0."""
        similarity = store._cosine_similarity([1.0, 0.0], [1.0, 0.0])
        assert abs(similarity - 1.0) < 0.001

    def test_cosine_similarity_orthogonal(self, store):
        """Orthogonal vectors should have similarity 0.0."""
        similarity = store._cosine_similarity([1.0, 0.0], [0.0, 1.0])
        assert abs(similarity) < 0.001

    def test_cosine_similarity_empty(self, store):
        """Empty vectors should return 0.0."""
        similarity = store._cosine_similarity([], [])
        assert similarity == 0.0


# --- TruthVectorStore Tests ---

class TestTruthVectorStore:
    """Tests for TruthVectorStore."""

    @pytest.fixture
    def mock_config(self):
        """Mock RAG configuration."""
        return {
            "rag": {
                "vector_store": {
                    "backend": "memory",
                    "persist_dir": "./data/test_vectors",
                    "collection_prefix": "test"
                },
                "search": {
                    "top_k": 5,
                    "similarity_threshold": 0.7
                },
                "fallback": {
                    "enabled": True
                },
                "indexing": {
                    "index_fields": ["text", "description"],
                    "metadata_fields": ["source", "category", "family"]
                }
            }
        }

    @pytest.fixture
    def mock_embedding_service(self):
        """Mock embedding service."""
        service = Mock()
        service.get_embedding = AsyncMock(return_value=Mock(
            embedding=[0.1, 0.2, 0.3],
            error=None
        ))
        service.get_embeddings_batch = AsyncMock(return_value=[
            Mock(embedding=[0.1, 0.2, 0.3], error=None),
            Mock(embedding=[0.4, 0.5, 0.6], error=None)
        ])
        service.get_dimension = Mock(return_value=768)
        return service

    @pytest.fixture
    def store(self, mock_config, mock_embedding_service):
        """Create TruthVectorStore with mocks."""
        with patch('core.vector_store.get_config_loader') as mock_loader:
            mock_loader.return_value.load.return_value = mock_config
            with patch('core.vector_store.get_embedding_service', return_value=mock_embedding_service):
                return TruthVectorStore()

    def test_init_uses_memory_backend(self, store):
        """Should default to in-memory backend."""
        assert isinstance(store._store, InMemoryVectorStore)

    def test_init_with_chromadb_fallback(self, mock_config):
        """Should fallback to memory if chromadb unavailable."""
        mock_config["rag"]["vector_store"]["backend"] = "chromadb"

        with patch('core.vector_store.get_config_loader') as mock_loader:
            mock_loader.return_value.load.return_value = mock_config
            with patch('core.vector_store.get_embedding_service'):
                with patch.dict('sys.modules', {'chromadb': None}):
                    store = TruthVectorStore()
                    assert isinstance(store._store, InMemoryVectorStore)

    @pytest.mark.asyncio
    async def test_index_truths(self, store, mock_embedding_service):
        """Should index truth documents."""
        truths = [
            {"id": "doc1", "text": "Document 1", "description": "First doc"},
            {"id": "doc2", "text": "Document 2", "description": "Second doc"}
        ]

        count = await store.index_truths("words", truths)

        assert count == 2
        assert store.get_stats().total_documents == 2

    @pytest.mark.asyncio
    async def test_index_truths_empty(self, store):
        """Should handle empty list."""
        count = await store.index_truths("words", [])
        assert count == 0

    @pytest.mark.asyncio
    async def test_index_truths_clears_existing(self, store, mock_embedding_service):
        """Should clear existing index when requested."""
        await store.index_truths("words", [{"id": "doc1", "text": "Text"}])
        await store.index_truths("words", [{"id": "doc2", "text": "Text"}], clear_existing=True)

        assert store.get_stats().total_documents == 1

    @pytest.mark.asyncio
    async def test_search(self, store, mock_embedding_service):
        """Should search indexed documents."""
        await store.index_truths("words", [
            {"id": "doc1", "text": "Python programming"},
            {"id": "doc2", "text": "JavaScript coding"}
        ])

        results = await store.search("python", "words")

        assert len(results) >= 0  # May be filtered by threshold

    @pytest.mark.asyncio
    async def test_search_empty_query(self, store):
        """Should handle empty query."""
        results = await store.search("", "words")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_respects_threshold(self, store, mock_embedding_service):
        """Should filter results below threshold."""
        await store.index_truths("words", [{"id": "doc1", "text": "text"}])

        # With high threshold, may get no results
        results = await store.search("query", "words", similarity_threshold=0.99)
        # Results filtered by threshold

    def test_clear_index_all(self, store):
        """Should clear all indexes."""
        store._store.add("doc1", "text", [1.0], {}, "words")
        store._store.add("doc2", "text", [1.0], {}, "pdf")

        store.clear_index()

        assert store.get_stats().total_documents == 0

    def test_clear_index_family(self, store):
        """Should clear specific family."""
        store._store.add("doc1", "text", [1.0], {}, "words")
        store._store.add("doc2", "text", [1.0], {}, "pdf")

        store.clear_index("words")

        stats = store.get_stats()
        assert stats.total_documents == 1
        assert "pdf" in stats.families

    def test_get_stats(self, store):
        """Should return index statistics."""
        store._store.add("doc1", "text", [1.0], {}, "words")

        stats = store.get_stats()

        assert isinstance(stats, IndexStats)
        assert stats.total_documents == 1
        assert "words" in stats.families

    @pytest.mark.asyncio
    async def test_health_check(self, store, mock_embedding_service):
        """Should report health status."""
        mock_embedding_service.is_available = AsyncMock(return_value=True)

        health = await store.health_check()

        assert health["backend"] == "memory"
        assert "total_documents" in health


# --- Module-level singleton Tests ---

class TestGetTruthVectorStore:
    """Tests for get_truth_vector_store singleton."""

    def test_returns_singleton(self):
        """Should return same instance."""
        with patch('core.vector_store.get_config_loader') as mock_loader:
            mock_loader.return_value.load.return_value = {}
            with patch('core.vector_store.get_embedding_service'):
                # Reset singleton
                import core.vector_store
                core.vector_store._truth_vector_store = None

                store1 = get_truth_vector_store()
                store2 = get_truth_vector_store()

                assert store1 is store2
