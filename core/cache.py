# Location: scripts/tbcv/core/cache.py
"""
Two-level caching system for TBCV.
L1: In-memory LRU cache for fast access
L2: Persistent SQLite cache for longer-term storage

WHAT CHANGED (important):
- All reads of `settings.cache.l1.*` and `settings.cache.l2.*` now tolerate
  BOTH object-style (model.enabled) and dict-style (model["enabled"]) access.
- This prevents AttributeError if YAML merging ever produces plain dicts.

The rest of the logic is unchanged.
"""

import gzip
import hashlib
import pickle
import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from collections import OrderedDict
import threading

from .config import get_settings
from .database import db_manager
from .logging import get_logger, PerformanceLogger

logger = get_logger(__name__)

# ---------- small helpers to read attr/dict safely ----------

def _gx(obj: Any, key: str, default: Any = None) -> Any:
    """
    Get attribute or dict key `key` from `obj`.
    - If obj has attribute → return getattr
    - Else if obj is dict → return obj.get
    - Else → default
    """
    if hasattr(obj, key):
        return getattr(obj, key)
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default

def _ensure_bool(x: Any) -> bool:
    """Coerce truthy/falsy to a real bool."""
    return bool(x)

# ------------------------------------------------------------

class LRUCache:
    """Thread-safe LRU cache implementation."""
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
        self.access_times = {}
        self.lock = threading.RLock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache with TTL check."""
        with self.lock:
            if key not in self.cache:
                self._misses += 1
                return None

            access_time = self.access_times.get(key, 0)
            if time.time() - access_time > self.ttl_seconds:
                # expired
                del self.cache[key]
                del self.access_times[key]
                self._misses += 1
                return None

            value = self.cache.pop(key)
            self.cache[key] = value
            self.access_times[key] = time.time()
            self._hits += 1
            return value

    def put(self, key: str, value: Any) -> None:
        """Insert item; evict least-recently-used if needed."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
            self.cache[key] = value
            self.access_times[key] = time.time()

            while len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.access_times[oldest_key]

    def delete(self, key: str) -> bool:
        """Delete single key."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                del self.access_times[key]
                return True
            return False

    def clear(self) -> None:
        """Flush all keys."""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self._hits = 0
            self._misses = 0

    def size(self) -> int:
        """Current key count."""
        return len(self.cache)

    def hit_rate(self) -> float:
        """Hit ratio since last clear."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def stats(self) -> Dict[str, Any]:
        """Basic stats for dashboards."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate(),
            "ttl_seconds": self.ttl_seconds,
        }


class CacheManager:
    """Two-level cache manager with L1 (memory) and L2 (persistent DB)."""

    def __init__(self):
        self.settings = get_settings()
        self._setup_caches()

    def _setup_caches(self):
        """Initialize L1 and L2 based on settings (robust to dicts)."""
        cache_cfg = self.settings.cache
        l1_cfg = _gx(cache_cfg, "l1", {})
        l2_cfg = _gx(cache_cfg, "l2", {})

        # L1 in-memory cache
        if _ensure_bool(_gx(l1_cfg, "enabled", True)):
            self.l1_cache = LRUCache(
                max_size=int(_gx(l1_cfg, "max_entries", 1000)),
                ttl_seconds=int(_gx(l1_cfg, "ttl_seconds", 3600)),
            )
            logger.info(
                "L1 cache initialized",
                max_entries=_gx(l1_cfg, "max_entries", 1000),
                ttl_seconds=_gx(l1_cfg, "ttl_seconds", 3600),
            )
        else:
            self.l1_cache = None
            logger.info("L1 cache disabled")

        # L2 persistent cache (DB-backed)
        if _ensure_bool(_gx(l2_cfg, "enabled", True)):
            logger.info("L2 cache initialized", database_path=_gx(l2_cfg, "database_path", "./data/cache/tbcv_cache.db"))
        else:
            logger.info("L2 cache disabled")

    def _generate_cache_key(self, agent_id: str, method: str, input_data: Any) -> str:
        """Stable key from agent+method+normalized input."""
        if isinstance(input_data, dict):
            normalized = str(sorted(input_data.items()))
        else:
            normalized = str(input_data)
        input_hash = hashlib.sha256(normalized.encode()).hexdigest()[:16]
        return f"{agent_id}:{method}:{input_hash}"

    def _serialize_data(self, data: Any) -> bytes:
        """Pickle + optional gzip based on L2 settings."""
        serialized = pickle.dumps(data)
        l2_cfg = _gx(self.settings.cache, "l2", {})
        if _ensure_bool(_gx(l2_cfg, "compression_enabled", True)) and len(serialized) > int(
            _gx(l2_cfg, "compression_threshold_bytes", 1024)
        ):
            serialized = gzip.compress(serialized)
        return serialized

    def _deserialize_data(self, data: bytes) -> Any:
        """Unpickle (auto-try gzip)."""
        try:
            try:
                return pickle.loads(gzip.decompress(data))
            except gzip.BadGzipFile:
                return pickle.loads(data)
        except Exception as e:
            logger.error("Failed to deserialize cache data", error=str(e))
            return None

    def get(self, agent_id: str, method: str, input_data: Any) -> Optional[Any]:
        """Fetch from L1, fall back to L2."""
        cache_key = self._generate_cache_key(agent_id, method, input_data)
        with PerformanceLogger(logger, f"cache_get_{agent_id}_{method}") as perf:
            # L1
            if self.l1_cache:
                result = self.l1_cache.get(cache_key)
                if result is not None:
                    perf.add_context(cache_level="L1", cache_hit=True)
                    logger.debug("L1 cache hit", cache_key=cache_key, agent_id=agent_id, method=method)
                    return result

            # L2
            l2_cfg = _gx(self.settings.cache, "l2", {})
            if _ensure_bool(_gx(l2_cfg, "enabled", True)):
                cache_entry = db_manager.get_cache_entry(cache_key)
                if cache_entry:
                    result = self._deserialize_data(cache_entry.result_data)
                    if result is not None and self.l1_cache:
                        self.l1_cache.put(cache_key, result)
                    perf.add_context(cache_level="L2", cache_hit=bool(cache_entry))
                    if cache_entry:
                        logger.debug("L2 cache hit", cache_key=cache_key, agent_id=agent_id, method=method)
                    return result

            perf.add_context(cache_hit=False)
            logger.debug("Cache miss", cache_key=cache_key, agent_id=agent_id, method=method)
            return None

    def put(self, agent_id: str, method: str, input_data: Any, result: Any, ttl_seconds: Optional[int] = None) -> None:
        """Store into L1 (if enabled) and L2 (if enabled)."""
        cache_key = self._generate_cache_key(agent_id, method, input_data)
        with PerformanceLogger(logger, f"cache_put_{agent_id}_{method}") as perf:
            if self.l1_cache:
                self.l1_cache.put(cache_key, result)
                perf.add_context(l1_stored=True)

            l2_cfg = _gx(self.settings.cache, "l2", {})
            if _ensure_bool(_gx(l2_cfg, "enabled", True)):
                try:
                    serialized = self._serialize_data(result)
                    size_bytes = len(serialized)
                    if ttl_seconds is None:
                        ttl_seconds = self._get_default_ttl(method)
                    expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(ttl_seconds))
                    input_hash = hashlib.sha256(str(input_data).encode()).hexdigest()

                    db_manager.store_cache_entry(
                        cache_key=cache_key,
                        agent_id=agent_id,
                        method_name=method,
                        input_hash=input_hash,
                        result_data=serialized,
                        expires_at=expires_at,
                        size_bytes=size_bytes,
                    )
                    perf.add_context(l2_stored=True, size_bytes=size_bytes)
                    logger.debug("Cache stored", cache_key=cache_key, agent_id=agent_id, method=method, size_bytes=size_bytes)
                except Exception as e:
                    logger.error("Failed to store in L2 cache", cache_key=cache_key, error=str(e))

    def _get_default_ttl(self, method: str) -> int:
        """Return an appropriate TTL; default falls back to L1 ttl or 3600."""
        ttl_map = {
            "fuzzy_detection": 86400,
            "llm_validation": 86400,
            "content_update": 3600,
            "truth_loading": 604800,
            "plugin_analysis": 43200,
        }
        for pattern, ttl in ttl_map.items():
            if pattern in method.lower():
                return ttl
        # fall back to configured L1 ttl if present, else 3600
        l1_cfg = _gx(self.settings.cache, "l1", {})
        return int(_gx(l1_cfg, "ttl_seconds", 3600))

    def delete(self, agent_id: str, method: str, input_data: Any) -> bool:
        """Delete from both layers."""
        cache_key = self._generate_cache_key(agent_id, method, input_data)
        deleted = False

        if self.l1_cache:
            deleted |= self.l1_cache.delete(cache_key)

        l2_cfg = _gx(self.settings.cache, "l2", {})
        if _ensure_bool(_gx(l2_cfg, "enabled", True)):
            try:
                from .database import CacheEntry
                with db_manager.get_session() as session:
                    result = session.query(CacheEntry).filter(CacheEntry.cache_key == cache_key).delete()
                    session.commit()
                    deleted |= (result > 0)
            except Exception as e:
                logger.error("Failed to delete from L2 cache", cache_key=cache_key, error=str(e))

        if deleted:
            logger.debug("Cache entry deleted", cache_key=cache_key)
        return deleted

    def clear_agent_cache(self, agent_id: str) -> None:
        """Remove all cache entries for a given agent_id (both layers)."""
        if self.l1_cache:
            keys_to_delete = []
            with self.l1_cache.lock:
                for key in list(self.l1_cache.cache.keys()):
                    if key.startswith(f"{agent_id}:"):
                        keys_to_delete.append(key)
            for key in keys_to_delete:
                self.l1_cache.delete(key)

        l2_cfg = _gx(self.settings.cache, "l2", {})
        if _ensure_bool(_gx(l2_cfg, "enabled", True)):
            try:
                from .database import CacheEntry
                with db_manager.get_session() as session:
                    deleted = session.query(CacheEntry).filter(CacheEntry.agent_id == agent_id).delete()
                    session.commit()
                    logger.info("Agent cache cleared", agent_id=agent_id, entries_deleted=deleted)
            except Exception as e:
                logger.error("Failed to clear agent cache", agent_id=agent_id, error=str(e))

    def cleanup_expired(self) -> Dict[str, int]:
        """Purge expired entries from both layers."""
        result = {"l1_cleaned": 0, "l2_cleaned": 0}

        if self.l1_cache:
            current_time = time.time()
            expired_keys = []
            with self.l1_cache.lock:
                for key, access_time in list(self.l1_cache.access_times.items()):
                    if current_time - access_time > self.l1_cache.ttl_seconds:
                        expired_keys.append(key)
            for key in expired_keys:
                self.l1_cache.delete(key)
                result["l1_cleaned"] += 1

        l2_cfg = _gx(self.settings.cache, "l2", {})
        if _ensure_bool(_gx(l2_cfg, "enabled", True)):
            result["l2_cleaned"] = db_manager.cleanup_expired_cache()

        logger.info("Cache cleanup completed", **result)
        return result

    def get_statistics(self) -> Dict[str, Any]:
        """Return consolidated L1/L2 stats."""
        stats = {"l1": {"enabled": False}, "l2": {"enabled": False}}

        if self.l1_cache:
            stats["l1"] = {"enabled": True, **self.l1_cache.stats()}

        l2_cfg = _gx(self.settings.cache, "l2", {})
        if _ensure_bool(_gx(l2_cfg, "enabled", True)):
            try:
                from .database import CacheEntry
                with db_manager.get_session() as session:
                    total_entries = session.query(CacheEntry).count()
                    sizes = session.query(CacheEntry.size_bytes).all()
                    total_size_bytes = sum(s[0] or 0 for s in sizes)
                stats["l2"] = {
                    "enabled": True,
                    "total_entries": total_entries,
                    "total_size_bytes": total_size_bytes,
                    "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
                    "database_path": _gx(l2_cfg, "database_path", "./data/cache/tbcv_cache.db"),
                }
            except Exception as e:
                logger.error("Failed to get L2 cache statistics", error=str(e))
                stats["l2"] = {"enabled": True, "error": str(e)}

        return stats

# Global cache manager instance (imported by agents)
cache_manager = CacheManager()
# ================================================================
# Decorator: cache_result
# ================================================================
def cache_result(ttl_seconds: int = 3600):
    """
    Decorator that caches the result of an agent method in both L1 and L2 caches.

    Usage example:
        @cache_result(ttl_seconds=3600)
        async def detect_plugins(self, params):
            ...

    How it works:
        • Generates a deterministic cache key from the agent ID, method name,
          and function arguments (params).
        • Checks L1 (memory) → L2 (persistent DB) caches.
        • On hit, returns the cached result immediately.
        • On miss, executes the wrapped function and stores its result in both caches.

    Parameters
    ----------
    ttl_seconds : int
        Number of seconds the result remains valid in the L2 cache.
    """

    def decorator(func):
        async def async_wrapper(self, *args, **kwargs):
            # derive stable key from agent + function name + args
            key_input = {"args": args, "kwargs": kwargs}
            cached = cache_manager.get(self.agent_id, func.__name__, key_input)
            if cached is not None:
                self.logger.debug("Cache hit (async)", method=func.__name__)
                return cached

            result = await func(self, *args, **kwargs)
            cache_manager.put(self.agent_id, func.__name__, key_input, result, ttl_seconds)
            self.logger.debug("Cache stored (async)", method=func.__name__)
            return result

        def sync_wrapper(self, *args, **kwargs):
            key_input = {"args": args, "kwargs": kwargs}
            cached = cache_manager.get(self.agent_id, func.__name__, key_input)
            if cached is not None:
                self.logger.debug("Cache hit (sync)", method=func.__name__)
                return cached

            result = func(self, *args, **kwargs)
            cache_manager.put(self.agent_id, func.__name__, key_input, result, ttl_seconds)
            self.logger.debug("Cache stored (sync)", method=func.__name__)
            return result

        # choose wrapper type automatically
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
