"""The 7 demo scenarios against the real LLM (Groq + Qwen), in text mode.

Needs GROQ_API_KEY in .env; skipped without it. Text mode uses no Cartesia
credits. Groq's free tier allows 8,000 tokens a minute, so the tests pause
between scenarios. Run:  uv run pytest evals -m live
"""

import asyncio
import os
import re

import pytest

from harness import converse
from omar_core import Lead, LeadStatus
from omar_voice.agent import build_llm
from omar_voice.settings import Settings

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not os.environ.get("GROQ_API_KEY"), reason="GROQ_API_KEY not set"),
]

PAUSE_S = float(os.environ.get("LIVE_EVAL_PAUSE_S", "20"))
TURN_PAUSE_S = float(os.environ.get("LIVE_TURN_PAUSE_S", "6"))
MONEY = re.compile(r"\b(?:aed|usd|dirhams?)\b|[$£€]\s?\d|\b\d+\s?k\b", re.IGNORECASE)


@pytest.fixture(autouse=True)
async def _pace():
    yield
    await asyncio.sleep(PAUSE_S)


def model():
    return build_llm(Settings())


async def test_1_happy_path_books():
    t = await converse(
        model(),
        turn_pause_s=TURN_PAUSE_S,
        lead_lines=[
            "Yes, speaking.",
            "Sure, go ahead.",
            "We have four laundry shops and people keep calling to book pickups.",
            "Mostly regular customers, they want to book and pay by card.",
            "Yes, we want to do this soon.",
            "Later this week, afternoon is best.",
            "The first one works.",
            "Yes, that email is fine.",
        ],
    )
    assert t.controller.state.status is LeadStatus.BOOKED, t.controller.steps


async def test_2_price_question():
    t = await converse(
        model(),
        turn_pause_s=TURN_PAUSE_S,
        lead_lines=["Yes, speaking.", "Sure.", "How much would an app like that cost?"],
    )
    assert t.controller.state.status is LeadStatus.QUALIFIED, t.controller.steps
    assert not MONEY.search(t.text)


async def test_3_talk_to_someone():
    t = await converse(
        model(),
        turn_pause_s=TURN_PAUSE_S,
        lead_lines=["Yes, it's me.", "Go ahead.", "Can I talk to someone about this?"],
    )
    assert t.controller.state.status is LeadStatus.QUALIFIED, t.controller.steps
    assert "manager" in t.text.lower()


async def test_4_brush_offs_park():
    t = await converse(
        model(),
        turn_pause_s=TURN_PAUSE_S,
        lead_lines=[
            "Yes, speaking.",
            "Sure.",
            "We sell perfume online.",
            "Mostly Instagram right now.",
            "It's just me and two staff.",
            "We started last year.",
            "Just send me an email.",
            "Honestly, just email me the details.",
            "No, please just send an email.",
        ],
    )
    assert t.controller.state.status is LeadStatus.PARKED, t.controller.steps


async def test_5_bot_question_is_honest():
    t = await converse(
        model(),
        turn_pause_s=TURN_PAUSE_S,
        lead_lines=["Yes, speaking.", "Sure.", "Wait, am I talking to a bot?"],
    )
    assert t.controller.state.ai_disclosed, t.controller.steps
    assert re.search(r"\b(ai|assistant)\b", t.text, re.IGNORECASE)


async def test_6_opt_out():
    t = await converse(
        model(),
        turn_pause_s=TURN_PAUSE_S,
        lead_lines=["Yes.", "I'm not interested, please don't call me again."],
    )
    assert t.controller.state.status is LeadStatus.OPTED_OUT, t.controller.steps


async def test_7_callback():
    t = await converse(
        model(),
        turn_pause_s=TURN_PAUSE_S,
        lead_lines=[
            "Yes, speaking.",
            "I'm driving, can you call me later?",
            "Tomorrow at 4pm works.",
        ],
        lead=Lead(name="Rhea Fernandes", email="rhea.f@example.com"),
    )
    assert t.controller.state.status is LeadStatus.CALLBACK, t.controller.steps


DEVANAGARI = re.compile(r"[ऀ-ॿ]")


async def test_8_hindi_lead_gets_hindi_and_the_rules_hold():
    from omar_core import CallConfig

    t = await converse(
        model(),
        turn_pause_s=TURN_PAUSE_S,
        config=CallConfig(hindi=True),
        lead_lines=[
            "जी, बोल रहा हूँ।",
            "हाँ जी, बताइए।",
            "हमारी चार laundry shops हैं, लोग pickup book करने के लिए बहुत call करते हैं।",
            "ऐसा app बनाने में कितना खर्चा आएगा? और कितना time लगेगा?",
        ],
    )
    replies = t.omar[2:]  # after the identity ask and the opening
    assert t.controller.state.language == "hi", t.controller.steps
    assert all(DEVANAGARI.search(r) for r in replies), replies
    assert "Hoplon and Co" in t.omar[1]  # the opening keeps the name in English
    assert not re.search(r"होपलॉन|हॉपलॉन", t.text)
    assert not MONEY.search(t.text) and "हज़ार" not in t.text and "रुपये" not in t.text
    print("\n".join(t.omar))
