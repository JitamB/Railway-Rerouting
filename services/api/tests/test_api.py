"""API serving tests. The cascade store is overridden with canned records so the endpoints are
exercised without running the ST-GNN — we assert the *serving contract*: live risk, the
staleness watermark, the auto-docs, and that the WS streams per-station deltas."""

import pytest
from fastapi.testclient import TestClient

from cascadeguard_api.deps import CascadeStore, get_prediction_store
from cascadeguard_api.main import app

RECORDS = [
    {"station": "MGS", "cascade_risk": 0.89, "delay_mean_min": 16.8,
     "delay_interval_min": [16.0, 17.0], "why": "100% rake-link (12301->12302)",
     "mode": "live", "data_age_s": 30.0},
    {"station": "PNBE", "cascade_risk": 0.89, "delay_mean_min": 16.8,
     "delay_interval_min": [16.0, 17.0], "why": "rake-link", "mode": "live", "data_age_s": 30.0},
    {"station": "BSB", "cascade_risk": 0.87, "delay_mean_min": 16.7,
     "delay_interval_min": [16.0, 17.4], "why": "no dominant driver",
     "mode": "live", "data_age_s": 30.0},
]


@pytest.fixture
def client():
    app.dependency_overrides[get_prediction_store] = lambda: CascadeStore(records=list(RECORDS))
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_cascade_returns_live_risk_with_watermark(client):
    body = client.get("/cascade/12301").json()
    assert {r["station"] for r in body["stations"]} == {"MGS", "PNBE", "BSB"}
    assert any(r["cascade_risk"] > 0.5 for r in body["stations"])   # live risk present
    assert body["watermark"] == "based on data 30s old"             # staleness watermark


def test_station_view_lists_incoming_trains(client):
    body = client.get("/stations/BSB").json()
    assert "12301" in body["incoming_trains"] and body["cascade_risk"] == 0.87


def test_corridor_health_aggregates(client):
    body = client.get("/corridor/ECR").json()
    assert body["max_risk"] == 0.89 and body["status"] == "red"
    assert "MGS" in body["stations_at_risk"]


def test_reroute_returns_feasible_options_and_guidance(client):
    body = client.post("/reroute", params={"pnr": "PNR12345"}).json()
    trains = {o["train_no"] for o in body["options"]}
    assert "12301" not in trains and trains <= {"12303", "15049"}    # the at-risk train excluded
    assert "{" not in body["guidance"] and body["guidance"]          # template fully resolved


def test_docs_and_openapi_list_the_endpoints(client):
    assert client.get("/docs").status_code == 200
    paths = client.get("/openapi.json").json()["paths"]
    for p in ("/cascade/{train_no}", "/stations/{code}", "/corridor/{zone}", "/reroute"):
        assert p in paths


def test_ws_streams_deltas(client):
    with client.websocket_connect("/ws/live") as ws:
        deltas = []
        while True:
            msg = ws.receive_json()
            if msg["type"] == "complete":
                break
            deltas.append(msg)
    assert len(deltas) == 3 and all(d["type"] == "delta" for d in deltas)
    assert all("data_age_s" in d for d in deltas)                    # deltas carry staleness
