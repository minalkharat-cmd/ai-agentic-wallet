"""Tests for the PaidAPIService class."""

import pytest

from main import PaidAPIService, RateLimiter


class TestPaidAPIService:
    @pytest.mark.asyncio
    async def test_weather_service(self, api_service):
        result = await api_service.call_service("weather", {"city": "Tokyo"})
        assert result["success"] is True
        assert result["cost_usdc"] == 0.001
        assert result["result"]["city"] == "Tokyo"
        assert "tx_hash" in result

    @pytest.mark.asyncio
    async def test_stock_service(self, api_service):
        result = await api_service.call_service("stock", {"symbol": "AAPL"})
        assert result["success"] is True
        assert result["cost_usdc"] == 0.002
        assert result["result"]["symbol"] == "AAPL"

    @pytest.mark.asyncio
    async def test_news_service(self, api_service):
        result = await api_service.call_service("news", {"topic": "AI"})
        assert result["success"] is True
        assert result["cost_usdc"] == 0.003
        assert len(result["result"]["headlines"]) == 3

    @pytest.mark.asyncio
    async def test_translation_service(self, api_service):
        result = await api_service.call_service(
            "translation", {"text": "hello", "target_language": "es"}
        )
        assert result["success"] is True
        assert result["cost_usdc"] == 0.005

    @pytest.mark.asyncio
    async def test_unknown_service(self, api_service):
        result = await api_service.call_service("unknown", {})
        assert "error" in result
        assert "Unknown service" in result["error"]

    @pytest.mark.asyncio
    async def test_call_history_populated(self, api_service):
        assert len(api_service.call_history) == 0
        await api_service.call_service("weather", {"city": "NYC"})
        assert len(api_service.call_history) == 1
        assert api_service.call_history[0]["service"] == "weather"

    @pytest.mark.asyncio
    async def test_transaction_persisted(self, api_service):
        await api_service.call_service("weather", {"city": "London"})
        rows = api_service.store.get_recent_transactions(5)
        assert len(rows) == 1
        assert rows[0]["service"] == "weather"

    @pytest.mark.asyncio
    async def test_rate_limit_enforced(self, wallet, store):
        limiter = RateLimiter(max_calls=1, period_seconds=60)
        svc = PaidAPIService(wallet, store=store, rate_limiter=limiter)

        r1 = await svc.call_service("weather", {"city": "A"})
        assert r1["success"] is True

        r2 = await svc.call_service("weather", {"city": "B"})
        assert "error" in r2
        assert "Rate limit" in r2["error"]

    @pytest.mark.asyncio
    async def test_sanitize_strips_control_chars(self, api_service):
        result = await api_service.call_service(
            "weather", {"city": "Tokyo<script>alert(1)</script>"}
        )
        assert result["success"] is True
        assert "<script>" not in result["result"]["city"]

    def test_sanitize_truncates_long_input(self):
        long_val = "a" * 500
        cleaned = PaidAPIService._sanitize(long_val)
        assert len(cleaned) <= PaidAPIService._MAX_PARAM_LEN
