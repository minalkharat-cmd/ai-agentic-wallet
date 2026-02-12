"""Shared test fixtures for AI Agentic Wallet."""

import os
import tempfile

import pytest

# Ensure optional SDKs don't interfere with tests
os.environ.setdefault("GEMINI_API_KEY", "")
os.environ.setdefault("CIRCLE_API_KEY", "")
os.environ.setdefault("CIRCLE_ENTITY_SECRET", "")

from main import CircleWallet, PaidAPIService, AgenticOrchestrator, TransactionStore, RateLimiter


@pytest.fixture()
def wallet():
    """A CircleWallet instance in demo mode (no API keys)."""
    return CircleWallet()


@pytest.fixture()
def tmp_db(tmp_path):
    """Return a path to a temporary SQLite database."""
    return str(tmp_path / "test_wallet.db")


@pytest.fixture()
def store(tmp_db):
    """A TransactionStore backed by a temporary database."""
    s = TransactionStore(db_path=tmp_db)
    yield s
    s.close()


@pytest.fixture()
def rate_limiter():
    """A rate limiter with generous limits for tests."""
    return RateLimiter(max_calls=100, period_seconds=60)


@pytest.fixture()
def api_service(wallet, store, rate_limiter):
    """PaidAPIService wired to demo wallet, temp store, and generous limiter."""
    return PaidAPIService(wallet, store=store, rate_limiter=rate_limiter)


@pytest.fixture()
def orchestrator(wallet, api_service):
    """AgenticOrchestrator in fallback mode (no Gemini)."""
    return AgenticOrchestrator(wallet, api_service)
