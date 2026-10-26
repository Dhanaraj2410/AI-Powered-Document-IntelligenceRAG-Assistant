"""
Lightweight TTL-based in-memory cache for RAG query results and embeddings.

Reduces redundant LLM and embedding calls for repeated or similar queries.
"""
import threading
import time
import hashlib
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TTLCache:
    """
    Thread-safe in-memory cache with per-entry time-to-live expiry.

    Args:
        ttl_seconds (int): Default entry lifetime in seconds (default 300 = 5 min).
        max_size (int): Maximum number of entries before LRU eviction (default 512).
    """

    def __init__(self, ttl_seconds: int = 300, max_size: int = 512):
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if max_size <= 0:
            raise ValueError("max_size must be positive")
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._store: dict[str, tuple[Any, float]] = {}  # key -> (value, expires_at)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a cached value by key.

        Returns:
            Cached value if present and not expired, else None.
        """
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                logger.debug("Cache miss (expired): %s", key)
                return None
            logger.debug("Cache hit: %s", key)
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store a value under key with an optional per-entry TTL override.

        Args:
            key (str): Cache key.
            value (Any): Value to store.
            ttl (int | None): Entry TTL override in seconds; uses class default if None.
        """
        effective_ttl = ttl if ttl is not None else self._ttl
        expires_at = time.monotonic() + effective_ttl

        with self._lock:
            if key not in self._store and len(self._store) >= self._max_size:
                self._evict_oldest()
            self._store[key] = (value, expires_at)
            logger.debug("Cache set: %s (ttl=%ds)", key, effective_ttl)

    def delete(self, key: str) -> bool:
        """Remove a key from the cache. Returns True if key existed."""
        with self._lock:
            return self._store.pop(key, None) is not None

    def clear(self) -> None:
        """Flush all entries from the cache."""
        with self._lock:
            self._store.clear()
        logger.info("Cache cleared.")

    def purge_expired(self) -> int:
        """Remove all expired entries and return the count removed."""
        now = time.monotonic()
        with self._lock:
            expired_keys = [k for k, (_, exp) in self._store.items() if now > exp]
            for k in expired_keys:
                del self._store[k]
        if expired_keys:
            logger.debug("Purged %d expired cache entries.", len(expired_keys))
        return len(expired_keys)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _evict_oldest(self) -> None:
        """Evict the entry with the earliest expiry (must hold self._lock)."""
        if not self._store:
            return
        oldest_key = min(self._store, key=lambda k: self._store[k][1])
        del self._store[oldest_key]
        logger.debug("Cache evicted oldest entry: %s", oldest_key)

    @property
    def size(self) -> int:
        """Return current number of entries (including potentially expired ones)."""
        with self._lock:
            return len(self._store)

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def make_key(*args, **kwargs) -> str:
        """
        Generate a deterministic cache key from arbitrary positional and
        keyword arguments by hashing their JSON representation.

        Example::

            key = TTLCache.make_key("query_rag", user_id=1, question="What is AI?")
        """
        raw = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Module-level singleton instances used across the application
# ---------------------------------------------------------------------------

#: Short-lived cache for RAG query results (5 minutes)
query_cache = TTLCache(ttl_seconds=300, max_size=256)

#: Longer-lived cache for document embeddings (30 minutes)
embedding_cache = TTLCache(ttl_seconds=1800, max_size=1024)
