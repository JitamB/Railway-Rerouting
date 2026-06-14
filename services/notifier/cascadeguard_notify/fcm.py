"""Firebase Cloud Messaging delivery.

Delivers the (template-first) alert to the passenger app even when it's closed. Phrasing may be
upgraded asynchronously by the llm-agent, but delivery never waits on it. When FCM credentials
aren't configured, ``send`` returns a clearly-labelled mock message id instead of failing —
honest-mock, so the demo runs without Firebase (firebase-admin is imported lazily).
"""

from __future__ import annotations

import json
import os
import uuid


class FcmSender:
    def __init__(self, project_id: str | None = None, credentials_json: str | None = None) -> None:
        self.project_id = project_id or os.getenv("FCM_PROJECT_ID")
        self._credentials_json = credentials_json or os.getenv("FCM_CREDENTIALS_JSON")
        self._app = None
        self.mock = not (self.project_id and self._credentials_json)

    def send(self, device_token: str, title: str, body: str, data: dict | None = None) -> str:
        """Send a push; returns the FCM message id (or a labelled mock id when unconfigured)."""
        if self.mock:
            return f"mock-fcm-{uuid.uuid4().hex[:12]}"  # FCM not configured — honest mock

        from firebase_admin import credentials, initialize_app, messaging  # lazy import

        if self._app is None:
            cred = credentials.Certificate(json.loads(self._credentials_json))
            self._app = initialize_app(cred, {"projectId": self.project_id})
        message = messaging.Message(
            token=device_token,
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
        )
        return messaging.send(message, app=self._app)
