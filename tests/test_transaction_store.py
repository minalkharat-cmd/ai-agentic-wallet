"""Tests for the TransactionStore persistence layer."""

import json

from main import TransactionStore


class TestTransactionStore:
    def test_record_and_retrieve(self, store):
        row_id = store.record_transaction(
            service="weather",
            params={"city": "Tokyo"},
            cost=0.001,
            tx_hash="0xabc123",
            result={"temperature": "22C"},
        )
        assert row_id is not None

        rows = store.get_recent_transactions(limit=5)
        assert len(rows) == 1
        assert rows[0]["service"] == "weather"
        assert rows[0]["cost_usdc"] == 0.001
        assert rows[0]["tx_hash"] == "0xabc123"

    def test_recent_transactions_ordering(self, store):
        for i in range(5):
            store.record_transaction(
                service=f"svc-{i}", params={}, cost=0.001 * i,
                tx_hash=f"0x{i}", result={},
            )
        rows = store.get_recent_transactions(limit=3)
        assert len(rows) == 3
        # Most recent first
        assert rows[0]["service"] == "svc-4"

    def test_total_spent(self, store):
        assert store.get_total_spent() == 0.0
        store.record_transaction("a", {}, 0.5, "0x1", {})
        store.record_transaction("b", {}, 0.3, "0x2", {})
        assert abs(store.get_total_spent() - 0.8) < 1e-9

    def test_state_get_set(self, store):
        assert store.get_state("missing") == ""
        assert store.get_state("missing", "default") == "default"
        store.set_state("wallet_id", "w-123")
        assert store.get_state("wallet_id") == "w-123"
        # Overwrite
        store.set_state("wallet_id", "w-456")
        assert store.get_state("wallet_id") == "w-456"

    def test_close_and_reopen(self, tmp_db):
        s1 = TransactionStore(db_path=tmp_db)
        s1.record_transaction("x", {}, 1.0, "0xf", {})
        s1.close()

        s2 = TransactionStore(db_path=tmp_db)
        assert s2.get_total_spent() == 1.0
        s2.close()
