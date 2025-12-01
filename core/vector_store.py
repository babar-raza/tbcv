# file: core/vector_store.py
"""
Vector Store for TBCV RAG implementation.

Provides semantic storage and retrieval of truth data using embeddings.
Supports multiple backends (ChromaDB, FAISS, in-memory).
"""

from __future__ import annotations

import os
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from core.logging import get_logger
from core.config_loader import get_config_loader
from core.embeddings import get_embedding_service, EmbeddingService

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """Result from a vector search."""
    id: str
    text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    family: str = ""


@dataclass
class IndexStats:
    """Statistics about the vector index."""
    total_documents: int
    families: List[str]
    last_updated: Optional[str]
    embedding_dimension: Optional[int]


class InMemoryVectorStore:
    """
    Simple in-memory vector store for testing and fallback.

    Uses cosine similarity for search.
    """

    def __init__(self):
        self._documents: Dict[str, Dict] = {}  # id -> {text, embedding, metadata}
        self._families: Dict[str, List[str]] = {}  # family -> [doc_ids]

    def add(
        self,
        doc_id: str,
        text: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        family: str
    ):
        """Add a document to the store."""
        self._documents[doc_id] = {
            "text": text,
            "embedding": embedding,
            "metadata": metadata,
            "family": family
        }
        if family not in self._families:
            self._families[family] = []
        if doc_id not in self._families[family]:
            self._families[family].append(doc_id)

    def search(
        self,
        query_embedding: List[float],
        family: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """Search for similar documents."""
        results = []

        # Get documents for this family
        doc_ids = self._families.get(family, [])

        for doc_id in doc_ids:
            doc = self._documents.get(doc_id)
            if not doc:
                continue

            # Calculate cosine similarity
            score = self._cosine_similarity(query_embedding, doc["embedding"])
            results.append(SearchResult(
                id=doc_id,
                text=doc["text"],
                score=score,
                metadata=doc["metadata"],
                family=family
            ))

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def clear(self, family: Optional[str] = None):
        """Clear documents, optionally for specific family."""
        if family:
            doc_ids = self._families.get(family, [])
            for doc_id in doc_ids:
                self._documents.pop(doc_id, None)
            self._families.pop(family, None)
        else:
            self._documents.clear()
            self._families.clear()

    def count(self, family: Optional[str] = None) -> int:
        """Count documents, optionally for specific family."""
        if family:
            return len(self._families.get(family, []))
        return len(self._documents)

    def get_families(self) -> List[str]:
        """Get list of indexed families."""
        return list(self._families.keys())


class TruthVectorStore:
    """
    Vector store for semantic truth retrieval.

    Supports:
    - Multiple storage backends (memory, chromadb)
    - Family-based indexing
    - Semantic search with similarity threshold
    - Graceful fallback when embeddings unavailable
    """

    def __init__(
        self,
        backend: Optional[str] = None,
        persist_dir: Optional[str] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        self._config = self._load_config()

        vector_config = self._config.get("vector_store", {})
        self.backend = backend or vector_config.get("backend", "memory")
        self.persist_dir = persist_dir or vector_config.get("persist_dir", "./data/vector_store")
        self.collection_prefix = vector_config.get("collection_prefix", "tbcv_truth")

        self._embedding_service = embedding_service or get_embedding_service()
        self._store = self._init_store()
        self._last_updated: Optional[datetime] = None

    def _load_config(self) -> Dict[str, Any]:
        """Load RAG configuration."""
        try:
            config_loader = get_config_loader()
            config = config_loader.load("rag")
            return config.get("rag", {}) if config else {}
        except Exception as e:
            logger.warning(f"Failed to load RAG config: {e}")
            return {}

    def _init_store(self):
        """Initialize the vector store backend."""
        if self.backend == "chromadb":
            return self._init_chromadb()
        else:
            logger.info("Using in-memory vector store")
            return InMemoryVectorStore()

    def _init_chromadb(self):
        """Initialize ChromaDB backend."""
        try:
            import chromadb
            from chromadb.config import Settings

            # Ensure persist directory exists
            Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

            client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info(f"Initialized ChromaDB at {self.persist_dir}")
            return client

        except ImportError:
            logger.warning("ChromaDB not installed, falling back to in-memory store")
            return InMemoryVectorStore()
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            return InMemoryVectorStore()

    def _get_collection(self, family: str):
        """Get or create a collection for a family."""
        if isinstance(self._store, InMemoryVectorStore):
            return self._store

        collection_name = f"{self.collection_prefix}_{family}"
        try:
            return self._store.get_or_create_collection(
                name=collection_name,
                metadata={"family": family}
            )
        except Exception as e:
            logger.error(f"Failed to get collection {collection_name}: {e}")
            return None

    async def index_truths(
        self,
        family: str,
        truths: List[Dict[str, Any]],
        clear_existing: bool = True
    ) -> int:
        """
        Index truth data for semantic search.

        Args:
            family: Truth family (e.g., "words", "pdf")
            truths: List of truth dictionaries
            clear_existing: Whether to clear existing index first

        Returns:
            Number of documents indexed
        """
        if not truths:
            return 0

        # Clear existing if requested
        if clear_existing:
            self.clear_index(family)

        # Prepare documents
        texts = []
        ids = []
        metadatas = []

        index_fields = self._config.get("indexing", {}).get(
            "index_fields", ["text", "description", "content"]
        )
        metadata_fields = self._config.get("indexing", {}).get(
            "metadata_fields", ["source", "category", "family", "version"]
        )

        for i, truth in enumerate(truths):
            # Build text from index fields
            text_parts = []
            for field in index_fields:
                if field in truth and truth[field]:
                    text_parts.append(str(truth[field]))

            if not text_parts:
                continue

            text = " ".join(text_parts)
            doc_id = truth.get("id") or f"{family}_{i}_{hashlib.md5(text.encode()).hexdigest()[:8]}"

            # Extract metadata
            metadata = {"family": family}
            for field in metadata_fields:
                if field in truth:
                    metadata[field] = truth[field]

            texts.append(text)
            ids.append(doc_id)
            metadatas.append(metadata)

        if not texts:
            return 0

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} truths in {family}")
        embedding_results = await self._embedding_service.get_embeddings_batch(texts)

        # Filter out failed embeddings
        valid_docs = []
        for doc_id, text, metadata, result in zip(ids, texts, metadatas, embedding_results):
            if result.embedding:
                valid_docs.append((doc_id, text, result.embedding, metadata))
            else:
                logger.warning(f"Failed to embed document {doc_id}: {result.error}")

        if not valid_docs:
            logger.error("No documents could be embedded")
            return 0

        # Add to store
        if isinstance(self._store, InMemoryVectorStore):
            for doc_id, text, embedding, metadata in valid_docs:
                self._store.add(doc_id, text, embedding, metadata, family)
        else:
            collection = self._get_collection(family)
            if collection:
                try:
                    collection.add(
                        ids=[d[0] for d in valid_docs],
                        documents=[d[1] for d in valid_docs],
                        embeddings=[d[2] for d in valid_docs],
                        metadatas=[d[3] for d in valid_docs]
                    )
                except Exception as e:
                    logger.error(f"Failed to add documents to ChromaDB: {e}")
                    return 0

        self._last_updated = datetime.now()
        logger.info(f"Indexed {len(valid_docs)} documents for family {family}")
        return len(valid_docs)

    async def search(
        self,
        query: str,
        family: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[SearchResult]:
        """
        Search for relevant truths.

        Args:
            query: Search query
            family: Truth family to search
            top_k: Maximum number of results
            similarity_threshold: Minimum similarity score

        Returns:
            List of SearchResults sorted by relevance
        """
        search_config = self._config.get("search", {})
        top_k = top_k or search_config.get("top_k", 5)
        similarity_threshold = similarity_threshold or search_config.get("similarity_threshold", 0.7)

        # Generate query embedding
        result = await self._embedding_service.get_embedding(query)
        if not result.embedding:
            logger.warning(f"Failed to embed query: {result.error}")
            return []

        # Search the store
        if isinstance(self._store, InMemoryVectorStore):
            results = self._store.search(result.embedding, family, top_k)
        else:
            collection = self._get_collection(family)
            if not collection:
                return []

            try:
                query_result = collection.query(
                    query_embeddings=[result.embedding],
                    n_results=top_k,
                    include=["documents", "metadatas", "distances"]
                )

                results = []
                if query_result and query_result.get("ids"):
                    ids = query_result["ids"][0]
                    documents = query_result.get("documents", [[]])[0]
                    metadatas = query_result.get("metadatas", [[]])[0]
                    distances = query_result.get("distances", [[]])[0]

                    for i, doc_id in enumerate(ids):
                        # Convert distance to similarity (ChromaDB uses L2 distance)
                        distance = distances[i] if i < len(distances) else 0
                        similarity = 1 / (1 + distance)  # Convert to similarity

                        results.append(SearchResult(
                            id=doc_id,
                            text=documents[i] if i < len(documents) else "",
                            score=similarity,
                            metadata=metadatas[i] if i < len(metadatas) else {},
                            family=family
                        ))

            except Exception as e:
                logger.error(f"ChromaDB search failed: {e}")
                return []

        # Filter by similarity threshold
        filtered_results = [r for r in results if r.score >= similarity_threshold]

        logger.debug(
            f"Search '{query[:50]}...' in {family}: "
            f"{len(results)} results, {len(filtered_results)} above threshold"
        )

        return filtered_results

    def clear_index(self, family: Optional[str] = None):
        """Clear index for a family or all families."""
        if isinstance(self._store, InMemoryVectorStore):
            self._store.clear(family)
        else:
            if family:
                collection_name = f"{self.collection_prefix}_{family}"
                try:
                    self._store.delete_collection(collection_name)
                except Exception:
                    pass  # Collection may not exist
            else:
                # Clear all collections with our prefix
                try:
                    collections = self._store.list_collections()
                    for col in collections:
                        if col.name.startswith(self.collection_prefix):
                            self._store.delete_collection(col.name)
                except Exception as e:
                    logger.warning(f"Failed to clear collections: {e}")

        logger.info(f"Cleared index for {'all families' if not family else family}")

    def get_stats(self) -> IndexStats:
        """Get index statistics."""
        if isinstance(self._store, InMemoryVectorStore):
            return IndexStats(
                total_documents=self._store.count(),
                families=self._store.get_families(),
                last_updated=self._last_updated.isoformat() if self._last_updated else None,
                embedding_dimension=self._embedding_service.get_dimension()
            )
        else:
            families = []
            total = 0
            try:
                collections = self._store.list_collections()
                for col in collections:
                    if col.name.startswith(self.collection_prefix):
                        family = col.name.replace(f"{self.collection_prefix}_", "")
                        families.append(family)
                        total += col.count()
            except Exception as e:
                logger.warning(f"Failed to get stats: {e}")

            return IndexStats(
                total_documents=total,
                families=families,
                last_updated=self._last_updated.isoformat() if self._last_updated else None,
                embedding_dimension=self._embedding_service.get_dimension()
            )

    async def health_check(self) -> Dict[str, Any]:
        """Check health of vector store and embedding service."""
        embedding_available = await self._embedding_service.is_available()
        stats = self.get_stats()

        return {
            "status": "healthy" if embedding_available else "degraded",
            "embedding_service": embedding_available,
            "backend": self.backend,
            "total_documents": stats.total_documents,
            "families": stats.families,
            "cache_stats": self._embedding_service.get_cache_stats()
        }


# Module-level singleton
_truth_vector_store: Optional[TruthVectorStore] = None


def get_truth_vector_store() -> TruthVectorStore:
    """Get the global truth vector store instance."""
    global _truth_vector_store
    if _truth_vector_store is None:
        _truth_vector_store = TruthVectorStore()
    return _truth_vector_store
