"""Tests for the AgenticOrchestrator class."""

import pytest

from main import AgenticOrchestrator


class TestAgenticOrchestrator:
    @pytest.mark.asyncio
    async def test_weather_query(self, orchestrator):
        response = await orchestrator.process("What's the weather in Tokyo?")
        assert "Tokyo" in response
        assert "USDC" in response

    @pytest.mark.asyncio
    async def test_stock_query(self, orchestrator):
        response = await orchestrator.process("Get TSLA stock price")
        assert "TSLA" in response
        assert "USDC" in response

    @pytest.mark.asyncio
    async def test_news_query(self, orchestrator):
        response = await orchestrator.process("Latest news about AI")
        assert "AI" in response or "ai" in response.lower()

    @pytest.mark.asyncio
    async def test_balance_query(self, orchestrator):
        response = await orchestrator.process("Check my wallet balance")
        assert "USDC" in response
        assert "Balance" in response

    @pytest.mark.asyncio
    async def test_history_empty(self, orchestrator):
        response = await orchestrator.process("Show transaction history")
        assert "No transactions" in response

    @pytest.mark.asyncio
    async def test_history_after_calls(self, orchestrator):
        await orchestrator.process("weather in London")
        response = await orchestrator.process("Show transaction history")
        assert "weather" in response.lower()

    @pytest.mark.asyncio
    async def test_unknown_query(self, orchestrator):
        response = await orchestrator.process("do something random")
        assert "weather" in response.lower() or "stock" in response.lower()

    @pytest.mark.asyncio
    async def test_empty_query(self, orchestrator):
        response = await orchestrator.process("")
        assert "Please enter a query" in response

    @pytest.mark.asyncio
    async def test_query_truncation(self, orchestrator):
        long_query = "weather " + "x" * 1000
        response = await orchestrator.process(long_query)
        # Should not crash, may or may not match weather
        assert isinstance(response, str)


class TestExtractHelpers:
    def test_extract_city_with_preposition(self, orchestrator):
        assert orchestrator._extract_city("weather in Tokyo?") == "Tokyo"
        assert orchestrator._extract_city("weather for London") == "London"
        assert orchestrator._extract_city("weather at Paris!") == "Paris"

    def test_extract_city_capitalised(self, orchestrator):
        assert orchestrator._extract_city("weather Mumbai") == "Mumbai"

    def test_extract_city_default(self, orchestrator):
        assert orchestrator._extract_city("weather") == "Mumbai"

    def test_extract_symbol(self, orchestrator):
        assert orchestrator._extract_symbol("Get TSLA stock price") == "TSLA"
        assert orchestrator._extract_symbol("AAPL price") == "AAPL"

    def test_extract_symbol_default(self, orchestrator):
        assert orchestrator._extract_symbol("stock price") == "AAPL"

    def test_extract_topic(self, orchestrator):
        assert orchestrator._extract_topic("news about AI") == "ai"
        assert orchestrator._extract_topic("news on crypto") == "crypto"

    def test_extract_topic_default(self, orchestrator):
        assert orchestrator._extract_topic("latest news") == "technology"
