from omar_core import DEFAULT_LEAD, Event, start, transition
from omar_core.knowledge import TOPICS, load, lookup
from omar_core.prompts import event_menu, instructions


def tokens(text: str) -> int:
    return round(len(text.split()) * 1.35)  # rough English token count


def test_every_topic_has_content_and_stays_small():
    sections = load()
    for topic in TOPICS:
        assert sections[topic], topic
        assert tokens(sections[topic]) < 900, (topic, tokens(sections[topic]))


def test_lookup_content():
    assert "iOS" in lookup("mobile_apps") or "iPhone" in lookup("mobile_apps")
    assert "Business Bay" in lookup("company")
    assert "[VERIFY]" not in lookup("saas") and "[GAP]" not in lookup("saas")
    assert "manager" in lookup("unknown_topic")


def test_prompt_is_lean_in_every_stage():
    s = start(DEFAULT_LEAD)
    for ev in (Event.ANSWERED, Event.CONFIRM_IDENTITY, Event.GOOD_TIME, Event.INTENT_YES):
        s, _ = transition(s, ev)
        assert tokens(instructions(s)) < 600, s.stage


def test_event_menu_matches_stage():
    s, _ = transition(start(DEFAULT_LEAD), Event.ANSWERED)
    names = [n for n, _ in event_menu(s)]
    assert names == ["confirm_identity", "wrong_person"]
