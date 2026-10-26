"""
Pytest tests for the RateLimiter utility.
"""
import time
import threading
import pytest

from rag_app.services.rate_limiter import RateLimiter


class TestRateLimiterBasic:
    def test_allows_calls_within_limit(self):
        limiter = RateLimiter(max_calls=5, period_seconds=60)
        for _ in range(5):
            assert limiter.allow() is True

    def test_blocks_calls_over_limit(self):
        limiter = RateLimiter(max_calls=3, period_seconds=60)
        for _ in range(3):
            limiter.allow()
        assert limiter.allow() is False

    def test_remaining_decrements_correctly(self):
        limiter = RateLimiter(max_calls=10, period_seconds=60)
        assert limiter.remaining == 10
        limiter.allow()
        assert limiter.remaining == 9

    def test_reset_clears_all_calls(self):
        limiter = RateLimiter(max_calls=3, period_seconds=60)
        for _ in range(3):
            limiter.allow()
        assert limiter.remaining == 0
        limiter.reset()
        assert limiter.remaining == 3

    def test_invalid_max_calls_raises(self):
        with pytest.raises(ValueError):
            RateLimiter(max_calls=0)

    def test_invalid_period_raises(self):
        with pytest.raises(ValueError):
            RateLimiter(period_seconds=-1)


class TestRateLimiterSliding:
    def test_sliding_window_allows_after_expiry(self):
        """Calls made in the previous window should not block new ones."""
        limiter = RateLimiter(max_calls=2, period_seconds=0.2)
        limiter.allow()
        limiter.allow()
        assert limiter.allow() is False
        time.sleep(0.25)  # wait for window to slide
        assert limiter.allow() is True

    def test_wait_for_slot_acquires_within_timeout(self):
        limiter = RateLimiter(max_calls=1, period_seconds=0.3)
        limiter.allow()  # exhaust the budget
        acquired = limiter.wait_for_slot(timeout=1.0)
        assert acquired is True

    def test_wait_for_slot_times_out(self):
        limiter = RateLimiter(max_calls=1, period_seconds=60)
        limiter.allow()
        acquired = limiter.wait_for_slot(timeout=0.1)
        assert acquired is False


class TestRateLimiterThreadSafety:
    def test_concurrent_calls_do_not_exceed_limit(self):
        max_calls = 10
        limiter = RateLimiter(max_calls=max_calls, period_seconds=60)
        successes = []
        lock = threading.Lock()

        def attempt():
            result = limiter.allow()
            with lock:
                successes.append(result)

        threads = [threading.Thread(target=attempt) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert sum(successes) == max_calls
