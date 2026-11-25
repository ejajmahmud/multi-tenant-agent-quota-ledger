"""CLI for Multi-Tenant Agent Quota Ledger."""
import argparse
import json
from .core import TenantQuotaLedger


def main():
    parser = argparse.ArgumentParser(description="Multi-Tenant Agent Quota Ledger CLI")
    parser.add_argument("--cap", type=int, default=1000, help="Max token quota")
    args = parser.parse_args()

    ledger = TenantQuotaLedger()
    ledger.set_quota("org-demo", max_tokens=args.cap, max_calls=5)
    rid = ledger.reserve("org-demo", tokens=300, calls=1)
    ledger.settle(rid, actual_tokens=180)
    print(json.dumps(ledger.balance("org-demo"), indent=2))


if __name__ == "__main__":
    main()
