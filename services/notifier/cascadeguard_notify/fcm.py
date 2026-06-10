"""Firebase Cloud Messaging delivery.

Delivers the (template-first) alert to the passenger PWA even when the app is closed. Phrasing
may be upgraded asynchronously by the llm-agent, but delivery never waits on it.
"""

from __future__ import annotations


class FcmSender:
    def __init__(self, project_id: str | None = None, credentials_json: str | None = None) -> None:
        ...

    def send(self, device_token: str, title: str, body: str, data: dict | None = None) -> str:
        """Send a push; returns the FCM message id."""
        ...
