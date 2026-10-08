"""The 7 demo scenarios with a scripted LLM. Tests our wiring, not the model."""

import re

import pytest

from fake_llm import ScriptedLLM, last_is_tool_output, last_user_text
from harness import converse
from omar_core import LeadStatus

# Lead phrase -> event the "model" reports
RULES = [
    (r"\byes,? speaking\b|\bthat's me\b", "confirm_identity", None),
    (r"\bgo ahead\b|\bsure\b", "good_time", None),
    (r"\bhow much\b|\bcost\b", "ask_price", None),
    (r"\btalk to someone\b", "ask_manager", None),
    (r"\blet's do it\b|\bmove ahead\b", "intent_yes", None),
    (r"\bsend me an email\b", "objection", None),
    (r"\bare you a bot\b", "ask_bot", None),
    (r"\bnot interested\b|\bdon't call\b", "not_interested", None),
    (r"\bcall me later\b|\bbusy\b", "not_now", None),
    (r"\btomorrow at 4\b", "callback_in_window", "tomorrow at 4pm"),
    (r"\bmorning\b|\bafternoon\b", "give_preference", "{text}"),
    (r"\bfirst one\b", "accept_slot", "first"),
    (r"\bthat email is fine\b", "email_ok", None),
]


def policy(ctx, tools):
    out = last_is_tool_output(ctx)
    if out is not None:
        return f"Sure. {out[:60]}"
    text = last_user_text(ctx)
    if "report_lead_event" in tools:
        for pattern, event, detail in RULES:
            if re.search(pattern, text):
                args = {"event": event}
                if detail:
                    args["detail"] = detail.format(text=text)
                return ("tool", "report_lead_event", args)
    return "That sounds great, tell me more about your customers."


async def run(lines, **kw):
    return await converse(ScriptedLLM(policy), lines, **kw)


async def test_1_happy_path_books():
    t = await run(
        [
            "Yes, speaking",
            "Sure, go ahead",
            "We have four shops",
            "Customers want pickup",
            "Yes, let's do it",
            "Later this week in the afternoon",
            "The first one",
            "Yes, that email is fine",
        ]
    )
    assert t.controller.state.status is LeadStatus.BOOKED
    assert "this call is recorded" in t.text
    assert "You're booked for" in t.omar[-1]


async def test_2_price_question_goes_to_booking_without_numbers():
    t = await run(["Yes, speaking", "Sure", "How much does an app cost?"])
    assert t.controller.state.status is LeadStatus.QUALIFIED
    assert not re.search(r"AED|\$|\d+\s?k\b", t.text)


async def test_3_talk_to_someone():
    t = await run(["Yes, speaking", "Sure", "Can I talk to someone?"])
    assert t.controller.state.status is LeadStatus.QUALIFIED
    assert "connect you with my manager" in t.text


async def test_4_three_brush_offs_park():
    t = await run(
        [
            "Yes, speaking",
            "Sure",
            "ok",
            "fine",
            "we sell perfume",
            "mostly online",
            "Just send me an email",
            "Just send me an email",
            "Just send me an email",
        ]
    )
    assert t.controller.state.status is LeadStatus.PARKED


async def test_5_bot_question_is_honest():
    t = await run(["Yes, speaking", "Sure", "Are you a bot?"])
    assert t.controller.state.ai_disclosed
    assert "AI assistant" in t.text


async def test_6_opt_out():
    t = await run(["Yes, speaking", "Not interested, don't call me again"])
    assert t.controller.state.status is LeadStatus.OPTED_OUT
    assert "won't call again" in t.omar[-1]


async def test_7_callback():
    t = await run(["Yes, speaking", "I'm busy, call me later", "Tomorrow at 4"])
    assert t.controller.state.status is LeadStatus.CALLBACK


@pytest.mark.parametrize(
    "bad,rule",
    [
        ("A basic app costs around AED 40,000.", "no_budget"),
        ("Great news, you're booked for Tuesday.", "no_booked_before_calendar"),
    ],
)
async def test_guard_replaces_forbidden_llm_text(bad, rule):
    def leaky(ctx, tools):
        return bad if last_user_text(ctx) == "tell me" else policy(ctx, tools)

    t = await converse(ScriptedLLM(leaky), ["Yes, speaking", "Sure", "tell me"])
    assert bad not in t.text
    assert t.agent.guard_hits[-1]["rule"] == rule


async def test_tools_follow_the_stage():
    llm = ScriptedLLM(policy)
    await converse(llm, ["Yeah.", "What is this about?"])
    assert "report_lead_event" in llm.calls[0] and "lookup_service" in llm.calls[0]


async def test_code_confirms_identity_without_the_llm():
    llm = ScriptedLLM(lambda ctx, tools: "This should not be said.")
    t = await converse(llm, ["Yeah."])
    assert t.controller.stage.value == "OPENING"
    assert "this call is recorded" in t.text
    assert "should not be said" not in t.text
    assert t.controller.steps[-1].by == "code"
