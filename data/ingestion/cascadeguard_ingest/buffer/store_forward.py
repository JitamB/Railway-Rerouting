"""Redis Streams store-and-forward buffer (audit-04 §1).

Decouples sources from consumers so transient gaps don't lose events, and stamps every event
with event-time + a watermark so "current delay" is never computed from a stale clock
(audit-04 §9). Redis Streams is the deliberate choice over Kafka for a single-zone build
(audit-02 §3.6).

Delivery is at-least-once via a consumer group: messages stay in the consumer's pending list
until ``ack()``-ed, so a consumer that crashes mid-batch re-reads them on restart (replay),
never losing events.
"""

from __future__ import annotations

import json
from typing import Iterator

import redis
from redis.exceptions import ResponseError


class StoreForwardBuffer:
    def __init__(self, redis_url: str, stream_key: str) -> None:
        self.stream_key = stream_key
        self.watermark_key = f"{stream_key}:watermark"
        self._r = redis.Redis.from_url(redis_url, decode_responses=True)

    def append(self, event: dict) -> str:
        """Persist an event (with event-time + watermark); returns the stream id."""
        event_time = event["event_time"]
        stream_id = self._r.xadd(
            self.stream_key, {"data": json.dumps(event), "event_time": event_time}
        )
        # Advance the high-watermark (latest event-time seen) for staleness tracking.
        current = self._r.get(self.watermark_key)
        if current is None or event_time > current:
            self._r.set(self.watermark_key, event_time)
        return stream_id

    def watermark(self) -> str | None:
        """Latest event-time persisted — the freshness bound for downstream consumers."""
        return self._r.get(self.watermark_key)

    def _ensure_group(self, group: str) -> None:
        # id="0" so a new group covers the full backlog (nothing buffered is skipped); mkstream
        # lets a consumer attach before the first append.
        try:
            self._r.xgroup_create(self.stream_key, group, id="0", mkstream=True)
        except ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    def consume(
        self, group: str, consumer: str, *, count: int = 100, block_ms: int | None = None
    ) -> Iterator[dict]:
        """Consumer-group read with at-least-once delivery and replay on restart.

        First re-delivers this consumer's un-acked pending entries (replay), then drains new
        messages. Each yielded event carries ``_stream_id`` for the caller to ``ack()``.
        With ``block_ms`` set, blocks for new messages (long-running worker); otherwise drains
        what's available and returns (testable).
        """
        self._ensure_group(group)

        # 1) replay: this consumer's pending (delivered-but-unacked) entries.
        pending = self._r.xreadgroup(group, consumer, {self.stream_key: "0"}, count=count)
        yield from self._emit(pending)

        # 2) new messages not yet delivered to anyone in the group.
        while True:
            resp = self._r.xreadgroup(
                group, consumer, {self.stream_key: ">"}, count=count, block=block_ms
            )
            if not resp:
                return
            batch = list(self._emit(resp))
            yield from batch
            if block_ms is None and len(batch) < count:
                return

    def ack(self, group: str, stream_id: str) -> None:
        self._r.xack(self.stream_key, group, stream_id)

    def _emit(self, resp) -> Iterator[dict]:
        for _stream, messages in resp or []:
            for stream_id, fields in messages:
                event = json.loads(fields["data"])
                event["_stream_id"] = stream_id
                yield event
