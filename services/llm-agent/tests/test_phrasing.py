import asyncio

import pytest

from cascadeguard_llm.client import LlmClient
from cascadeguard_llm.phrasing import enrich, render_template
from cascadeguard_llm.prompts import build_guidance_prompt

FIELDS = {
    "train_no": "12301", "risk_pct": 78, "threshold": 30,
    "alt_train": "12303", "alt_platform": "5", "alt_depart": "+12 min",
    "dest": "BSB", "alt_eta": "65 min", "delta_min": 10, "seats_status": "AVL 69",
    "delay_min": 18,
}


class _FailClient:
    async def phrase(self, prompt, max_tokens=200):
        raise RuntimeError("network off")


class _OkClient:
    def __init__(self, text):
        self._text = text

    async def phrase(self, prompt, max_tokens=200):
        return self._text


def test_render_template_fills_safety_fields():
    text = render_template("high", "en", FIELDS)
    assert "12303" in text and "Platform 5" in text and "BSB" in text
    assert "{" not in text  # all placeholders resolved


def test_render_template_unknown_language_falls_back_to_english():
    assert render_template("high", "ta", FIELDS) == render_template("high", "en", FIELDS)


def test_enrich_falls_back_to_template_when_llm_unreachable():
    tpl = render_template("high", "en", FIELDS)
    out = asyncio.run(enrich(tpl, "prompt", _FailClient()))
    assert out == tpl                       # offline: the templated alert is what ships


def test_enrich_upgrades_prose_when_reachable():
    tpl = render_template("high", "en", FIELDS)
    better = "Your 12301 is at high risk. Best option: 12303 from Platform 5 — seats available."
    out = asyncio.run(enrich(tpl, "prompt", _OkClient(better), safety_fields=["12303", "5"]))
    assert out == better                    # online: improved prose, safety fields preserved


def test_enrich_rejects_llm_output_that_drops_a_safety_field():
    tpl = render_template("high", "en", FIELDS)
    unsafe = "Take the next available train, it should be fine."  # dropped train no / platform
    out = asyncio.run(enrich(tpl, "prompt", _OkClient(unsafe), safety_fields=["12303"]))
    assert out == tpl                       # safety preserved: fall back to the template


def test_llm_client_without_key_raises_for_fallback():
    client = LlmClient(api_key="")  # no key
    with pytest.raises(RuntimeError):
        asyncio.run(client.phrase("hi"))


def test_build_guidance_prompt_includes_facts():
    alts = [{"train_no": "12303", "platform": "5", "departs_min": 12, "arrives_dest_min": 65}]
    prompt = build_guidance_prompt("PNBE", "BSB", 18, 0.78, alts)
    assert "PNBE -> BSB" in prompt and "12303" in prompt and "78%" in prompt
