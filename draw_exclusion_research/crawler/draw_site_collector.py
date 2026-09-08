from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import Message
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class HttpSnapshot:
    source_url: str
    captured_at_utc: datetime
    html_bytes: bytes
    http_date: str | None
    last_modified: str | None
    content_type: str | None
    status_code: int

    def decode_html(self) -> str:
        charset = "utf-8"
        if self.content_type:
            message = Message()
            message["content-type"] = self.content_type
            charset = message.get_content_charset() or charset
        return self.html_bytes.decode(charset, errors="strict")


def collect(source_url: str, timeout_seconds: int = 30) -> HttpSnapshot:
    """Fetch one immutable source document without using or storing gate credentials."""
    request = Request(
        source_url,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "DrawExclusionResearch/1.0 (+authorized research snapshot)",
        },
        method="GET",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        body = response.read()
        return HttpSnapshot(
            source_url=response.geturl(),
            captured_at_utc=datetime.now(timezone.utc),
            html_bytes=body,
            http_date=response.headers.get("Date"),
            last_modified=response.headers.get("Last-Modified"),
            content_type=response.headers.get("Content-Type"),
            status_code=response.status,
        )
