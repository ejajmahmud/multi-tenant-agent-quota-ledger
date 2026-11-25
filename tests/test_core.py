"""Tests for Multi-Tenant Agent Quota Ledger."""
import unittest
from multi_tenant_agent_quota_ledger.core import TenantQuotaLedger, QuotaExceededError


class TestTenantQuotaLedger(unittest.TestCase):
    def test_reserve_settle_and_rollback(self):
        ledger = TenantQuotaLedger()
        ledger.set_quota("t1", max_tokens=500, max_calls=3)
        r1 = ledger.reserve("t1", tokens=300, calls=1)
        self.assertEqual(ledger.balance("t1")["remaining_tokens"], 200)
        ledger.settle(r1, actual_tokens=150)
        self.assertEqual(ledger.balance("t1")["remaining_tokens"], 350)

        r2 = ledger.reserve("t1", tokens=200, calls=1)
        ledger.rollback(r2)
        self.assertEqual(ledger.balance("t1"), {"remaining_tokens": 350, "remaining_calls": 2})

    def test_exceeding_quota_raises(self):
        ledger = TenantQuotaLedger()
        ledger.set_quota("t2", max_tokens=100, max_calls=2)
        with self.assertRaises(QuotaExceededError):
            ledger.reserve("t2", tokens=150, calls=1)
