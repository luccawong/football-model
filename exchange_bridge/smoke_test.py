"""OddsPapi v4 credential smoke test using unmetered GET /account."""
from __future__ import annotations
import os
from .oddspapi import OddsPapiError, fetch_account


def main() -> int:
    key = (os.environ.get("ODDSPAPI_API_KEY") or os.environ.get("THE_ODDS_API_KEY") or "").strip()
    if not key:
        print("FAIL: ODDSPAPI_API_KEY/THE_ODDS_API_KEY secret is not available.")
        return 2
    try:
        account, _ = fetch_account(key)
    except OddsPapiError as exc:
        print(f"FAIL: {exc}")
        return 1

    subscriptions = account.get("subscriptions", []) or []
    active = [s for s in subscriptions if s.get("is_active") is True]
    current_id = account.get("current_subscription_id")
    current = next((s for s in subscriptions if s.get("subscription_id") == current_id), None)
    if current is None and active:
        current = active[0]

    # Never print account.api_key or the secret.
    if current:
        sport_ids = current.get("sport_ids", []) or []
        bookmakers = current.get("bookmakers", {}) or {}
        print("OK: OddsPapi v4 API key authenticated.")
        print(
            f"Subscription active={bool(current.get('is_active'))} "
            f"request_count={current.get('request_count')} "
            f"request_limit={current.get('request_limit')} "
            f"soccer_access={10 in sport_ids} "
            f"betfair_ex_declared={'betfair-ex' in bookmakers}."
        )
    else:
        print("OK: OddsPapi v4 API key authenticated; no active subscription object was identified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
