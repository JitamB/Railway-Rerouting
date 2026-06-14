"""Step 32 verify: POST /helpline/chat returns a case id + authority; GET /queries lists it with
status; the case detail is owner-scoped. Uses the real agent (offline, in-memory case store)."""

import pytest
from fastapi.testclient import TestClient

from cascadeguard_api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_chat_opens_case_then_appears_in_my_queries(client):
    r = client.post("/helpline/chat", params={
        "passenger_id": "api_pax_1",
        "text": "there is an unattended bag in coach B4",
    })
    body = r.json()
    assert body["case_id"].startswith("CG-")
    assert "RPF" in body["authority"] and body["status"] == "open"

    listed = client.get("/queries", params={"passenger_id": "api_pax_1"}).json()
    assert any(q["case_id"] == body["case_id"] and q["status"] == "open" for q in listed)
    assert listed[0]["category"] == "security"


def test_query_detail_is_owner_scoped(client):
    case_id = client.post("/helpline/chat", params={
        "passenger_id": "api_pax_2", "text": "dirty toilet, please clean S3",
    }).json()["case_id"]

    ok = client.get(f"/queries/{case_id}", params={"passenger_id": "api_pax_2"})
    assert ok.status_code == 200 and ok.json()["history"][0]["status"] == "open"

    denied = client.get(f"/queries/{case_id}", params={"passenger_id": "someone_else"})
    assert denied.status_code == 404   # a passenger only sees their own cases
