import pytest

from omar_core import DEFAULT_LEAD, Event, start, transition
from omar_core.quick_events import quick_event


def at(stage_events):
    s = start(DEFAULT_LEAD)
    for e in stage_events:
        s, _ = transition(s, e)
    return s


IDENTITY = at([Event.ANSWERED])
OPENING = at([Event.ANSWERED, Event.CONFIRM_IDENTITY])


@pytest.mark.parametrize("text", ["Yeah.", "Yes, speaking.", "That's me", "Yep", "Okay."])
def test_identity_yes(text):
    assert quick_event(IDENTITY, text) is Event.CONFIRM_IDENTITY


@pytest.mark.parametrize("text", ["Wrong number.", "No, you have the wrong person", "I'm not him"])
def test_identity_wrong(text):
    assert quick_event(IDENTITY, text) is Event.WRONG_PERSON


@pytest.mark.parametrize(
    "text",
    [
        "Yes. This is. Who am I talking to?",
        "Yeah. Hello?",
        "Yes. Who is it?",
        "Yes I filled a form for an app and I want to know more",
    ],
)
def test_identity_yes_with_question_or_more(text):
    assert quick_event(IDENTITY, text) is Event.CONFIRM_IDENTITY


@pytest.mark.parametrize("text", ["Who is this?", "Which company?", "Hello?", "No."])
def test_identity_unclear_gets_scripted_reask(text):
    assert quick_event(IDENTITY, text) is Event.IDENTITY_UNCLEAR


def test_identity_goes_to_llm_after_two_reasks():
    s = IDENTITY
    for _ in range(2):
        s, fx = transition(s, Event.IDENTITY_UNCLEAR)
        assert "speaking with Khalifa?" in fx.say
    assert s.stage.value == "IDENTITY"
    assert quick_event(s, "Hello?") is None


@pytest.mark.parametrize(
    "text,event",
    [
        ("Sure, go ahead.", Event.GOOD_TIME),
        ("Yeah okay", Event.GOOD_TIME),
        ("I'm driving, call me later", Event.NOT_NOW),
        ("Not interested, don't call me", Event.NOT_INTERESTED),
        ("I don't want to be recorded", Event.OBJECTS_RECORDING),
    ],
)
def test_opening(text, event):
    assert quick_event(OPENING, text) is event


def test_other_stages_are_llm_only():
    info = at([Event.ANSWERED, Event.CONFIRM_IDENTITY, Event.GOOD_TIME])
    assert quick_event(info, "Yes") is None
