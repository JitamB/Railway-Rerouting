"""Pipeline orchestration tests — torch-free via a stub predictor (the heavy ST-GNN is tested
in ml/). We assert the *wiring*: a twin-injected delay flows to a push when (and only when) the
cost-sensitive trigger fires, the chosen alternative is feasible, and the degradation mode never
over-states confidence."""

from dataclasses import dataclass

from cascadeguard_worker.pipeline import process_event

# event at MGS at sim-min 58 (epoch 06:00 + 58 = 06:58Z), received 30s later -> data_age 30s -> live
EVENT = {
    "train_no": "12301", "station": "MGS",
    "event_time": "2026-06-12T06:58:00+00:00",
    "received_time": "2026-06-12T06:58:30+00:00",
    "delay_min": 18.0, "source": "twin",
}


@dataclass
class FakeCascade:
    station: str
    cascade_risk: float
    delay_mean_min: float
    delay_interval_min: tuple
    why: str
    mode: str = "live"


class RecSender:
    def __init__(self):
        self.sent = []

    def send(self, token, title, body, data=None):
        self.sent.append((token, title, body, data))
        return "mock-test-id"


def _predictor(cascades):
    return lambda station: cascades


def test_confident_tail_cascade_flows_to_a_push():
    cascades = [FakeCascade("BSB", 0.87, 16.7, (16.0, 17.4), "100% rake-link (12301->12302)")]
    sender = RecSender()
    out = process_event(EVENT, predictor=_predictor(cascades), sender=sender)

    assert out["notified"] is True and out["reason"] == "triggered"
    assert out["push_id"] == "mock-test-id" and len(sender.sent) == 1
    assert out["chosen"] in {"12303", "15049"}      # a feasible MGS->BSB alternative was picked
    assert "{" not in out["alert"]                  # every template field resolved
    assert out["mode"] == "live"


def test_low_confidence_small_delay_does_not_fire():
    # interval lower bound ~0 => confidence ~0 => expected benefit < false-alarm cost
    cascades = [FakeCascade("BSB", 0.2, 3.0, (0.0, 4.0), "minor")]
    sender = RecSender()
    out = process_event(EVENT, predictor=_predictor(cascades), sender=sender)

    assert out["notified"] is False and out["reason"] == "below trigger"
    assert sender.sent == []                         # no push when the utility says don't


def test_ood_fallback_degrades_mode_even_on_a_live_feed():
    cascades = [FakeCascade("BSB", 0.87, 16.7, (16.0, 17.4), "ood", mode="schedule_prior")]
    out = process_event(EVENT, predictor=_predictor(cascades), sender=RecSender())
    assert out["mode"] == "schedule_prior"           # never present an OOD prediction as "live"
