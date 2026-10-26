"""
Simple in-memory token-bucket rate limiter for LLM API calls.

Usage:
    limiter = RateLimiter(max_calls=10, period_seconds=60)
    if limiter.allow():
        response = LLMService.generate_response(...)
"""
import threading
import time
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Thread-safe token-bucket rate limiter.

    Args:
        max_calls (int): Maximum number of allowed calls within the period.
        period_seconds (float): Window duration in seconds.
    """

    def __init__(self, max_calls: int = 60, period_seconds: float = 60.0):
        if max_calls <= 0:
            raise ValueError("max_calls must be a positive integer")
        if period_seconds <= 0:
            raise ValueError("period_seconds must be a positive number")
        self._max_calls = max_calls
        self._period = period_seconds
        self._calls: list[float] = []
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def allow(self) -> bool:
        """
        Check whether a new call is allowed under the current rate budget.

        Returns:
            bool: True if the call is permitted; False if rate-limited.
        """
        now = time.monotonic()
        window_start = now - self._period

        with self._lock:
            # Prune timestamps outside the sliding window
            self._calls = [t for t in self._calls if t > window_start]

            if len(self._calls) < self._max_calls:
                self._calls.append(now)
                return True

        logger.warning(
            "Rate limit exceeded: %d/%d calls in the last %.0fs window.",
            len(self._calls),
            self._max_calls,
            self._period,
        )
        return False

    def wait_for_slot(self, timeout: float = 30.0) -> bool:
        """
        Block the calling thread until a slot becomes available or *timeout*
        seconds elapse.

        Args:
            timeout (float): Maximum seconds to wait.

        Returns:
            bool: True if a slot was acquired; False if timed out.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.allow():
                return True
            time.sleep(0.25)
        logger.error("Rate limiter timed out after %.1fs.", timeout)
        return False

    @property
    def remaining(self) -> int:
        """Return the number of calls still available in the current window."""
        now = time.monotonic()
        window_start = now - self._period
        with self._lock:
            self._calls = [t for t in self._calls if t > window_start]
            return max(0, self._max_calls - len(self._calls))

    def reset(self) -> None:
        """Clear all recorded call timestamps (useful in tests)."""
        with self._lock:
            self._calls.clear()
