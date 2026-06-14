"""Helpline router — chat endpoint for the grievance/support agent.

Accepts a text message or a regional-language audio clip, delegates to the helpline agent
(services/helpline), and returns the agent's reply plus the opened case. Audio uploads are
transcribed by the agent's ASR; safety-critical/routing fields come from structured data.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile

from ..deps import get_helpline_agent

router = APIRouter(prefix="/helpline", tags=["helpline"])


@router.post("/chat")
async def chat(
    passenger_id: str,
    text: str | None = None,
    audio: UploadFile | None = None,
    language: str | None = None,
    agent=Depends(get_helpline_agent),
) -> dict:
    """One helpline turn (text or speech). Returns reply + the opened/updated case."""
    audio_bytes = await audio.read() if audio is not None else None
    reply = agent.handle(passenger_id, text=text, audio=audio_bytes, language=language)
    return {
        "case_id": reply.case_id,
        "text": reply.text,
        "audio_url": reply.audio_url,
        "authority": reply.authority,
        "status": reply.status,
    }
