import uuid

import pytest
import redis

from cascadeguard_ingest.buffer.store_forward import StoreForwardBuffer

REDIS_URL = "redis://localhost:6379/0"


def _redis_up() -> bool:
    try:
        return redis.Redis.from_url(REDIS_URL).ping()
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _redis_up(), reason="Redis not running on localhost:6379")


@pytest.fixture
def buffer():
    key = f"test.cg.events.{uuid.uuid4().hex[:8]}"
    buf = StoreForwardBuffer(REDIS_URL, key)
    yield buf
    buf._r.delete(key, buf.watermark_key)  # cleanup


def _events(n: int) -> list[dict]:
    return [
        {
            "train_no": f"123{i:02d}",
            "station": "MGS",
            "event_time": f"2026-06-12T06:{i:02d}:00+00:00",
            "received_time": f"2026-06-12T06:{i:02d}:30+00:00",
            "delay_min": float(i),
            "source": "twin",
        }
        for i in range(n)
    ]


def test_append_advances_watermark(buffer):
    for ev in _events(3):
        buffer.append(ev)
    assert buffer.watermark() == "2026-06-12T06:02:00+00:00"


def test_events_survive_consumer_restart(buffer):
    events = _events(5)
    for ev in events:
        buffer.append(ev)

    group, consumer = "g1", "c1"

    # first read: drains the 5 buffered events (now pending/unacked)
    first = list(buffer.consume(group, consumer))
    assert [e["train_no"] for e in first] == [e["train_no"] for e in events]

    # simulate a crash before ack -> a restarted consumer replays the same 5, none lost
    replay = list(buffer.consume(group, consumer))
    assert [e["_stream_id"] for e in replay] == [e["_stream_id"] for e in first]

    # ack them -> nothing left to replay
    for e in replay:
        buffer.ack(group, e["_stream_id"])
    assert list(buffer.consume(group, consumer)) == []
