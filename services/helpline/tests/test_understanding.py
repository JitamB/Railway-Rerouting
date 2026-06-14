"""Step 29 verify: a (Hindi) utterance -> transcript -> category + extracted entities, plus the
authority routing of Step 30. Offline and deterministic — no live network."""

from cascadeguard_helpline.asr import ASR
from cascadeguard_helpline.authorities import default_authority, load_authorities
from cascadeguard_helpline.authority_router import route
from cascadeguard_helpline.intent import IntentEngine


def test_hindi_clip_transcribes_then_classifies_security_with_entities():
    # The honest ASR mock decodes the clip as text (a real utterance drives the pipeline).
    clip = "PNR 8412345678 train 12301 B4 coach mein ek lawaris bag pada hai".encode("utf-8")
    transcript = ASR().transcribe(clip, language="hi")
    assert transcript.language == "hi" and "lawaris" in transcript.text

    u = IntentEngine().understand(transcript.text)
    assert u.category == "security"           # romanized-Hindi "lawaris bag" -> security
    assert u.confidence >= 0.5
    assert u.entities["pnr"] == "8412345678"  # 10-digit PNR extracted
    assert u.entities["train_no"] == "12301"
    assert u.entities["coach"] == "B4"


def test_security_routes_to_rpf():
    auths = load_authorities()
    a = route("security", 0.8, auths, default_authority())
    assert "RPF" in a.department and a.channel == "railmadad"


def test_low_confidence_falls_back_to_general_helpdesk():
    auths = load_authorities()
    a = route("security", 0.2, auths, default_authority())  # unsure -> don't guess a department
    assert a.department == "RailMadad General Helpdesk"


def test_unknown_text_is_general():
    u = IntentEngine().understand("hello there")
    assert u.category == "general" and u.confidence == 0.0
