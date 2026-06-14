import pytest

from cascadeguard_notify.fcm import FcmSender


@pytest.fixture(autouse=True)
def _no_fcm_env(monkeypatch):
    monkeypatch.delenv("FCM_PROJECT_ID", raising=False)
    monkeypatch.delenv("FCM_CREDENTIALS_JSON", raising=False)


def test_unconfigured_sender_is_mock_and_delivers_a_token():
    sender = FcmSender()
    assert sender.mock is True

    msg_id = sender.send("test-device-token", "Re-route", "Take 12303 from Platform 5",
                         data={"train_no": "12303", "platform": "5"})
    assert msg_id.startswith("mock-fcm-")   # a "push" was delivered (mock id returned)
    assert msg_id != sender.send("test-device-token", "x", "y")  # unique per send


def test_configured_sender_is_not_mock():
    # credentials present -> would use the real FCM path (not exercised without firebase-admin)
    sender = FcmSender(project_id="demo", credentials_json='{"type": "service_account"}')
    assert sender.mock is False
