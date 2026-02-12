"""Tests for the CircleWallet class."""

import pytest

from main import CircleWallet


class TestCircleWallet:
    def test_init_demo_mode(self, wallet):
        """Wallet initializes in demo mode when no API keys are set."""
        assert wallet.client is None
        assert wallet.wallet_id is None

    @pytest.mark.asyncio
    async def test_demo_wallet_creation(self, wallet):
        result = await wallet.create_wallet()
        assert result["mode"] == "demo"
        assert result["blockchain"] == "ARC-TESTNET"
        assert "id" in result
        assert "address" in result

    @pytest.mark.asyncio
    async def test_get_balance_demo(self, wallet):
        balance = await wallet.get_balance()
        assert "usdc" in balance
        assert balance["usdc"] == 10.0
        assert "native" in balance

    @pytest.mark.asyncio
    async def test_transfer_demo(self, wallet):
        result = await wallet.transfer_usdc(
            to_address="0x1234567890abcdef1234567890abcdef12345678",
            amount=0.001,
            description="test"
        )
        assert result["success"] is True
        assert result["mode"] == "demo"
        assert result["amount"] == 0.001
        assert "tx_hash" in result

    @pytest.mark.asyncio
    async def test_transfer_invalid_address(self, wallet):
        result = await wallet.transfer_usdc(
            to_address="not-a-valid-address",
            amount=0.001,
        )
        assert result["success"] is False
        assert "Invalid address" in result["error"]

    @pytest.mark.asyncio
    async def test_transfer_negative_amount(self, wallet):
        result = await wallet.transfer_usdc(
            to_address="0x1234567890abcdef1234567890abcdef12345678",
            amount=-1.0,
        )
        assert result["success"] is False
        assert "positive" in result["error"]

    @pytest.mark.asyncio
    async def test_transfer_zero_amount(self, wallet):
        result = await wallet.transfer_usdc(
            to_address="0x1234567890abcdef1234567890abcdef12345678",
            amount=0,
        )
        assert result["success"] is False

    def test_invalid_blockchain_raises(self):
        wallet = CircleWallet()
        with pytest.raises(ValueError, match="Invalid blockchain"):
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                wallet.create_wallet(blockchain="INVALID")
            )

    @pytest.mark.asyncio
    async def test_create_wallet_set_returns_none_demo(self, wallet):
        result = await wallet.create_wallet_set()
        assert result is None
