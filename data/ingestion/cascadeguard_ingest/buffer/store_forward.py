"""Redis Streams store-and-forward buffer (audit-04 §1).

Decouples sources from consumers so transient gaps don't lose events, and stamps every event
with event-time + a watermark so "current delay" is never computed from a stale clock
(audit-04 §9). Redis Streams is the deliberate choice over Kafka for a single-zone build
(audit-02 §3.6).
"""

from __future__ import annotations

from typing import Iterator


class StoreForwardBuffer:
    def __init__(self, redis_url: str, stream_key: str) -> None:
        ...

    def append(self, event: dict) -> str:
        """Persist an event (with event-time + watermark); returns the stream id."""
        ...

    def consume(self, group: str, consumer: str) -> Iterator[dict]:
        """Consumer-group read with at-least-once delivery and replay on restart."""
        ...
