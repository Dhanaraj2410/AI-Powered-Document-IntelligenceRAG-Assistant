"""
Pytest tests for the TTLCache utility (cache_service.py).
"""
import time
import threading
import pytest

from rag_app.services.cache_service import TTLCache


class TestTTLCacheBasic:
    def test_set_and_get_value(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_missing_key_returns_none(self):
        cache = TTLCache(ttl_seconds=60)
        assert cache.get("nonexistent") is None

    def test_value_expires_after_ttl(self):
        cache = TTLCache(ttl_seconds=1)
        cache.set("temp", "data", ttl=1)
        assert cache.get("temp") == "data"
        time.sleep(1.1)
        assert cache.get("temp") is None

    def test_delete_removes_key(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("k", "v")
        assert cache.delete("k") is True
        assert cache.get("k") is None

    def test_delete_nonexistent_returns_false(self):
        cache = TTLCache(ttl_seconds=60)
        assert cache.delete("ghost") is False

    def test_clear_empties_cache(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.size == 0

    def test_size_property(self):
        cache = TTLCache(ttl_seconds=60)
        assert cache.size == 0
        cache.set("x", "y")
        assert cache.size == 1

    def test_invalid_ttl_raises(self):
        with pytest.raises(ValueError):
            TTLCache(ttl_seconds=0)

    def test_invalid_max_size_raises(self):
        with pytest.raises(ValueError):
            TTLCache(max_size=0)


class TestTTLCacheEviction:
    def test_lru_eviction_when_max_size_reached(self):
        cache = TTLCache(ttl_seconds=60, max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # triggers eviction
        assert cache.size == 3

    def test_purge_expired_removes_stale_entries(self):
        cache = TTLCache(ttl_seconds=60, max_size=10)
        cache.set("short", "val", ttl=1)
        cache.set("long", "val", ttl=300)
        time.sleep(1.1)
        removed = cache.purge_expired()
        assert removed == 1
        assert cache.get("long") == "val"


class TestTTLCacheKeyGeneration:
    def test_make_key_is_deterministic(self):
        k1 = TTLCache.make_key("query", user_id=1, q="hello")
        k2 = TTLCache.make_key("query", user_id=1, q="hello")
        assert k1 == k2

    def test_different_args_produce_different_keys(self):
        k1 = TTLCache.make_key("rag", user_id=1)
        k2 = TTLCache.make_key("rag", user_id=2)
        assert k1 != k2


class TestTTLCacheThreadSafety:
    def test_concurrent_writes_do_not_corrupt_state(self):
        cache = TTLCache(ttl_seconds=60, max_size=200)
        errors = []

        def writer(i):
            try:
                cache.set(f"key_{i}", i)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
