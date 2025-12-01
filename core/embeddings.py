# file: core/embeddings.py
"""
Embedding Service for TBCV RAG implementation.

Provides embedding generation via Ollama for semantic truth retrieval.
Supports batch processing and caching for efficiency.
"""

from __future__ import annotations

import asyncio
import hashlib
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

import aiohttp

from core.logging import get_logger
from core.config_loader import get_config_loader

logger = get_logger(__name__)


@dataclass
class EmbeddingResult:
    """Result of an embedding operation."""
    embedding: Optional[List[float]]
    text: str
    model: str
    cached: bool = False
    error: Optional[str] = None
    latency_ms: float = 0.0


class EmbeddingCache:
    """In-memory cache for embeddings."""

    def __init__(self, max_entries: int = 10000, ttl_seconds: int = 86400):
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple] = {}  # hash -> (embedding, timestamp)
        self._hits = 0
        self._misses = 0

    def _hash_text(self, text: str, model: str) -> str:
        """Create hash key for text + model."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def get(self, text: str, model: str) -> Optional[List[float]]:
        """Get cached embedding if exists and not expired."""
        key = self._hash_text(text, model)
        if key in self._cache:
            embedding, timestamp = self._cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl_seconds):
                self._hits += 1
                return embedding
            else:
                del self._cache[key]
        self._misses += 1
        return None

    def put(self, text: str, model: str, embedding: List[float]):
        """Store embedding in cache."""
        if len(self._cache) >= self.max_entries:
            self._evict_oldest()
        key = self._hash_text(text, model)
        self._cache[key] = (embedding, datetime.now())

    def _evict_oldest(self):
        """Remove oldest entries to make room."""
        if not self._cache:
            return
        # Remove 10% of oldest entries
        sorted_keys = sorted(
            self._cache.keys(),
            key=lambda k: self._cache[k][1]
        )
        for key in sorted_keys[:max(1, len(sorted_keys) // 10)]:
            del self._cache[key]

    def clear(self):
        """Clear all cached embeddings."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        return {
            "entries": len(self._cache),
            "max_entries": self.max_entries,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0.0
        }


class EmbeddingService:
    """
    Service for generating embeddings via Ollama.

    Supports:
    - Single and batch embedding generation
    - Caching for efficiency
    - Graceful fallback when unavailable
    """

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        cache_enabled: bool = True
    ):
        self._config = self._load_config()

        # Use provided values or fall back to config
        embedding_config = self._config.get("embedding", {})
        self.model = model or embedding_config.get("model", "nomic-embed-text")
        self.base_url = base_url or embedding_config.get("base_url", "http://localhost:11434")
        self.batch_size = embedding_config.get("batch_size", 100)

        # Cache setup
        cache_config = self._config.get("cache", {})
        if cache_enabled and cache_config.get("enabled", True):
            self._cache = EmbeddingCache(
                max_entries=cache_config.get("max_entries", 10000),
                ttl_seconds=cache_config.get("ttl_seconds", 86400)
            )
        else:
            self._cache = None

        self._available: Optional[bool] = None
        self._dimension: Optional[int] = None

    def _load_config(self) -> Dict[str, Any]:
        """Load RAG configuration."""
        try:
            config_loader = get_config_loader()
            config = config_loader.load("rag")
            return config.get("rag", {}) if config else {}
        except Exception as e:
            logger.warning(f"Failed to load RAG config: {e}")
            return {}

    async def is_available(self) -> bool:
        """Check if embedding service is reachable."""
        if self._available is not None:
            return self._available

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models = [m.get("name", "") for m in data.get("models", [])]
                        # Check if our model is available
                        self._available = any(
                            self.model in m or m.startswith(self.model)
                            for m in models
                        )
                        if not self._available:
                            logger.warning(
                                f"Model {self.model} not found in Ollama. "
                                f"Available: {models}"
                            )
                    else:
                        self._available = False
        except Exception as e:
            logger.warning(f"Embedding service not available: {e}")
            self._available = False

        return self._available

    async def get_embedding(
        self,
        text: str,
        use_cache: bool = True
    ) -> EmbeddingResult:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            use_cache: Whether to check/update cache

        Returns:
            EmbeddingResult with embedding or error
        """
        start_time = datetime.now()

        # Check cache first
        if use_cache and self._cache:
            cached = self._cache.get(text, self.model)
            if cached is not None:
                return EmbeddingResult(
                    embedding=cached,
                    text=text,
                    model=self.model,
                    cached=True,
                    latency_ms=0.0
                )

        # Check availability
        if not await self.is_available():
            return EmbeddingResult(
                embedding=None,
                text=text,
                model=self.model,
                error="Embedding service not available"
            )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        embedding = data.get("embedding", [])

                        # Cache the result
                        if use_cache and self._cache and embedding:
                            self._cache.put(text, self.model, embedding)

                        # Track dimension
                        if embedding and self._dimension is None:
                            self._dimension = len(embedding)

                        latency = (datetime.now() - start_time).total_seconds() * 1000

                        return EmbeddingResult(
                            embedding=embedding,
                            text=text,
                            model=self.model,
                            latency_ms=latency
                        )
                    else:
                        error_text = await resp.text()
                        return EmbeddingResult(
                            embedding=None,
                            text=text,
                            model=self.model,
                            error=f"API error {resp.status}: {error_text}"
                        )

        except asyncio.TimeoutError:
            return EmbeddingResult(
                embedding=None,
                text=text,
                model=self.model,
                error="Embedding request timed out"
            )
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return EmbeddingResult(
                embedding=None,
                text=text,
                model=self.model,
                error=str(e)
            )

    async def get_embeddings_batch(
        self,
        texts: List[str],
        use_cache: bool = True
    ) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            use_cache: Whether to check/update cache

        Returns:
            List of EmbeddingResults in same order as input
        """
        results: List[EmbeddingResult] = []
        texts_to_embed: List[tuple] = []  # (index, text)

        # Check cache first for all texts
        for i, text in enumerate(texts):
            if use_cache and self._cache:
                cached = self._cache.get(text, self.model)
                if cached is not None:
                    results.append(EmbeddingResult(
                        embedding=cached,
                        text=text,
                        model=self.model,
                        cached=True
                    ))
                    continue

            texts_to_embed.append((i, text))
            results.append(None)  # Placeholder

        # Generate embeddings for uncached texts
        if texts_to_embed:
            # Process in batches
            for batch_start in range(0, len(texts_to_embed), self.batch_size):
                batch = texts_to_embed[batch_start:batch_start + self.batch_size]

                # Generate embeddings concurrently within batch
                tasks = [
                    self.get_embedding(text, use_cache=use_cache)
                    for _, text in batch
                ]
                batch_results = await asyncio.gather(*tasks)

                # Place results in correct positions
                for (orig_index, _), result in zip(batch, batch_results):
                    results[orig_index] = result

        return results

    def get_dimension(self) -> Optional[int]:
        """Get embedding dimension (requires at least one embedding)."""
        if self._dimension:
            return self._dimension
        return self._config.get("embedding", {}).get("dimension", 768)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if self._cache:
            return self._cache.get_stats()
        return {"enabled": False}

    def clear_cache(self):
        """Clear embedding cache."""
        if self._cache:
            self._cache.clear()
            logger.info("Embedding cache cleared")


# Module-level singleton
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
