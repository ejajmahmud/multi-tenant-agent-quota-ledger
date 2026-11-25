"""Core thread-safe atomic reserve/settle/rollback quota ledger."""
import threading
from typing import Any, Dict


class QuotaExceededError(Exception):
    """Raised when a tenant lacks sufficient remaining token or call quota."""


class TenantQuotaLedger:
    """Thread-safe per-tenant reservation and settlement ledger for autonomous agents."""

    def __init__(self):
        self._lock = threading.Lock()
        self._quotas: Dict[str, Dict[str, int]] = {}
        self._reservations: Dict[str, Dict[str, Any]] = {}
        self._seq = 0

    def set_quota(self, tenant_id: str, max_tokens: int, max_calls: int):
        with self._lock:
            self._quotas[tenant_id] = {
                "max_tokens": max_tokens,
                "max_calls": max_calls,
                "used_tokens": 0,
                "used_calls": 0,
            }

    def reserve(self, tenant_id: str, tokens: int, calls: int = 1) -> str:
        with self._lock:
            q = self._quotas.get(tenant_id)
            if not q:
                raise KeyError(f"Unknown tenant {tenant_id}")
            if q["used_tokens"] + tokens > q["max_tokens"]:
                raise QuotaExceededError("Token quota exceeded")
            if q["used_calls"] + calls > q["max_calls"]:
                raise QuotaExceededError("Tool call quota exceeded")

            q["used_tokens"] += tokens
            q["used_calls"] += calls
            self._seq += 1
            rid = f"res-{self._seq}"
            self._reservations[rid] = {"tenant_id": tenant_id, "tokens": tokens, "calls": calls, "open": True}
            return rid

    def settle(self, reservation_id: str, actual_tokens: int):
        with self._lock:
            res = self._reservations.get(reservation_id)
            if not res or not res["open"]:
                raise ValueError("Invalid or already closed reservation")
            q = self._quotas[res["tenant_id"]]
            delta = actual_tokens - res["tokens"]
            q["used_tokens"] = max(0, q["used_tokens"] + delta)
            res["open"] = False

    def rollback(self, reservation_id: str):
        with self._lock:
            res = self._reservations.get(reservation_id)
            if not res or not res["open"]:
                raise ValueError("Invalid or already closed reservation")
            q = self._quotas[res["tenant_id"]]
            q["used_tokens"] = max(0, q["used_tokens"] - res["tokens"])
            q["used_calls"] = max(0, q["used_calls"] - res["calls"])
            res["open"] = False

    def balance(self, tenant_id: str) -> Dict[str, int]:
        with self._lock:
            q = self._quotas[tenant_id]
            return {
                "remaining_tokens": q["max_tokens"] - q["used_tokens"],
                "remaining_calls": q["max_calls"] - q["used_calls"],
            }
