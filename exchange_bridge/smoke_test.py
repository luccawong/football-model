"""OddsPapi credential smoke test using GET /sports."""
from __future__ import annotations
import os
from .oddspapi import OddsPapiError, fetch_sports

def main() -> int:
    key = (os.environ.get("ODDSPAPI_API_KEY") or os.environ.get("THE_ODDS_API_KEY") or "").strip()
    if not key:
        print("FAIL: ODDSPAPI_API_KEY/THE_ODDS_API_KEY secret is not available.")
        return 2
    try:
        sports, rate = fetch_sports(key)
    except OddsPapiError as exc:
        print(f"FAIL: {exc}")
        return 1
    soccer = [s for s in sports if int(s.get("sportId", -1)) == 10]
    if not soccer:
        print("FAIL: authenticated but soccer sportId=10 was not returned.")
        return 1
    print("OK: OddsPapi API key authenticated; soccer sportId=10 is available.")
    print(f"RateLimit remaining={rate.get('remaining')} limit={rate.get('limit')}.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
