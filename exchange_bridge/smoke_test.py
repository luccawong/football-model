"""Quota-free credential smoke test using GET /v4/sports."""
from __future__ import annotations
import os
from .the_odds_api import fetch_sports, OddsApiError

def main() -> int:
    key = os.environ.get("THE_ODDS_API_KEY", "")
    if not key:
        print("FAIL: THE_ODDS_API_KEY secret is not available to this workflow.")
        return 2
    try:
        sports, quota = fetch_sports(key)
    except OddsApiError as exc:
        print(f"FAIL: {exc}")
        return 1
    soccer = [s for s in sports if str(s.get("group", "")).casefold() == "soccer" and s.get("active")]
    print(f"OK: The Odds API key authenticated. Active soccer sport keys visible: {len(soccer)}.")
    print(f"Quota headers: remaining={quota.get('remaining')} used={quota.get('used')} last_cost={quota.get('last_cost')}.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
