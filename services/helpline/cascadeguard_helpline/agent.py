"""Helpline agent orchestrator.

Runs a grievance/query end-to-end:
  transcribe (if speech) -> understand -> fetch passenger details -> open case ->
  route to authority -> dispatch -> reply (text + optional speech).

Structured fields drive routing/dispatch; the LLM only phrases the human-readable parts.
"""

from __future__ import annotations

from dataclasses import dataclass

from .asr import ASR
from .authorities import DEFAULT_CONFIG, default_authority, load_authorities
from .authority_router import route
from .cases import open_case
from .dispatch import dispatch
from .intent import IntentEngine
from .passenger import fetch_details
from .tts import TTS


@dataclass
class HelplineReply:
    case_id: str
    text: str
    audio_url: str | None       # set if a spoken reply was synthesized
    authority: str              # department the case was routed to
    status: str                 # initial case status, e.g. "open"


class HelplineAgent:
    def __init__(self, language: str = "en", config_path: str = DEFAULT_CONFIG) -> None:
        self.language = language
        self.asr = ASR()
        self.tts = TTS()
        self.intent = IntentEngine()
        self.authorities = load_authorities(config_path)
        self.default = default_authority(config_path)

    def handle(
        self,
        passenger_id: str,
        text: str | None = None,
        audio: bytes | None = None,
        language: str | None = None,
    ) -> HelplineReply:
        """Process one helpline turn (text or speech) and return a reply + opened case.

        Structured fields (category, department, PNR, reference) drive routing/dispatch and the
        reply; only the surrounding sentence is phrasing. Offline-capable end to end.
        """
        lang = language or self.language
        input_mode = "text"
        transcript = (text or "").strip()
        if audio is not None and not transcript:
            t = self.asr.transcribe(audio, language)
            transcript, lang, input_mode = t.text, t.language, "speech"

        if not transcript:
            return HelplineReply("", "Sorry, I didn't catch that — please type or say it again.",
                                 None, "", "")

        understanding = self.intent.understand(transcript)
        details = fetch_details(  # PII: attached to the authority payload, not the trackable case
            passenger_id,
            understanding.entities.get("pnr"),
            understanding.entities.get("train_no"),
            understanding.entities.get("coach"),
        )
        authority = route(understanding.category, understanding.confidence, self.authorities, self.default)
        case = open_case(passenger_id, understanding, details, authority,
                         language=lang, transcript=transcript, input_mode=input_mode)
        result = dispatch(case, details, authority.channel)
        case.external_reference = result.reference

        reply_text = (
            f"Thank you. I've logged your concern as case {case.case_id} and routed it to "
            f"{authority.department} (ref {result.reference}). You can track its status under My Queries."
        )
        audio_url = None
        if input_mode == "speech" and self.tts.synthesize(reply_text, lang):
            audio_url = f"/helpline/audio/{case.case_id}"  # served when TTS is enabled

        return HelplineReply(
            case_id=case.case_id,
            text=reply_text,
            audio_url=audio_url,
            authority=authority.department,
            status=case.status.value,
        )


def run() -> None:
    """Service entrypoint. The agent is invoked in-process by services/api (routers helpline +
    queries); there is no separate consumer loop in this build."""
    print("HelplineAgent is invoked via services/api (POST /helpline/chat). Nothing to run here.")


if __name__ == "__main__":
    run()
