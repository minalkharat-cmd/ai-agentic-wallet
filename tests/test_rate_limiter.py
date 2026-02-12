"""Tests for the RateLimiter class."""

from main import RateLimiter


class TestRateLimiter:
    def test_allows_calls_under_limit(self):
        rl = RateLimiter(max_calls=3, period_seconds=60)
        assert rl.allow() is True
        assert rl.allow() is True
        assert rl.allow() is True

    def test_blocks_calls_over_limit(self):
        rl = RateLimiter(max_calls=2, period_seconds=60)
        assert rl.allow() is True
        assert rl.allow() is True
        assert rl.allow() is False

    def test_remaining_property(self):
        rl = RateLimiter(max_calls=5, period_seconds=60)
        assert rl.remaining == 5
        rl.allow()
        assert rl.remaining == 4
        rl.allow()
        rl.allow()
        assert rl.remaining == 2

    def test_zero_max_calls(self):
        rl = RateLimiter(max_calls=0, period_seconds=60)
        assert rl.allow() is False
        assert rl.remaining == 0
