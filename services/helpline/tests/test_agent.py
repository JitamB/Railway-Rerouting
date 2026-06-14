"""Step 30/31 verify: one handle() turns an utterance into a routed, tracked case + a reply; the
case is persisted and visible (owner-scoped) under My Queries with status `open`."""

from cascadeguard_helpline.agent import HelplineAgent
from cascadeguard_helpline.cases import get_case, list_cases


def test_handle_opens_routed_tracked_case_and_replies():
    agent = HelplineAgent()
    reply = agent.handle("pax_1", text="someone left an unattended bag in B4 coach")

    assert reply.case_id.startswith("CG-")
    assert "RPF" in reply.authority           # security -> RPF
    assert reply.status == "open"
    assert reply.case_id in reply.text        # the reply carries the trackable id

    case = get_case(reply.case_id)
    assert case is not None and case.category == "security" and case.external_reference.startswith("RM-")
    assert case.messages[0]["status"] == "open"   # history seeded


def test_speech_input_sets_speech_mode_and_persists_transcript():
    agent = HelplineAgent()
    clip = "AC is not working in my coach".encode("utf-8")
    reply = agent.handle("pax_2", audio=clip, language="hi")

    case = get_case(reply.case_id)
    assert case.input_mode == "speech" and case.language == "hi"
    assert case.transcript == "AC is not working in my coach"


def test_my_queries_is_owner_scoped_and_newest_first():
    agent = HelplineAgent()
    agent.handle("pax_owner", text="dirty toilet in S5")
    agent.handle("pax_owner", text="please process my refund / tdr")
    agent.handle("pax_other", text="medical help needed, passenger fainted")

    mine = list_cases("pax_owner")
    assert len(mine) == 2
    assert mine[0].created_at >= mine[1].created_at      # newest first
    assert all(c.passenger_id == "pax_owner" for c in mine)


def test_empty_input_returns_no_case():
    reply = HelplineAgent().handle("pax_x", text="   ")
    assert reply.case_id == "" and "didn't catch" in reply.text
