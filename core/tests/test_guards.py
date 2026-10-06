import pytest

from omar_core.guards import check_sentence, split_complete


@pytest.mark.parametrize(
    "text,rule",
    [
        ("A basic app usually costs around AED 40,000.", "no_budget"),
        ("Most clients spend about $5k on this.", "no_budget"),
        ("It's roughly twenty thousand dirhams.", "no_budget"),
        ("We usually deliver in 6 to 8 weeks.", "no_timeline"),
        ("That normally takes three months.", "no_timeline"),
        ("Great, you're booked for Tuesday.", "no_booked_before_calendar"),
        ("I've scheduled that for you.", "no_booked_before_calendar"),
        ("No, I'm a real person.", "never_deny_ai"),
        ("I'm not an AI, don't worry.", "never_deny_ai"),
        ("Let me refer you to the team.", "say_my_manager"),
        ("You can speak to a human about it.", "say_my_manager"),
    ],
)
def test_forbidden_sentences(text, rule):
    v = check_sentence(text, booking_confirmed=False)
    assert v is not None and v.rule == rule


@pytest.mark.parametrize(
    "text",
    [
        "A quick 30-minute call with my manager would help.",
        "We've been doing this for about fourteen years.",
        "Would Tuesday at 11am or Wednesday at 3pm suit you better?",
        "Yes, I'm Hoplon's AI assistant.",
        "Let me connect you with my manager.",
        "We have over a hundred and fifty clients.",
        "Is now a good time for two minutes?",
    ],
)
def test_safe_sentences(text):
    assert check_sentence(text, booking_confirmed=False) is None


def test_booked_allowed_after_confirmation():
    assert check_sentence("You're booked for Tuesday.", booking_confirmed=True) is None


def test_split_complete():
    done, rest = split_complete("Hi there. How are you? I was")
    assert done == ["Hi there.", "How are you?"] and rest == "I was"
    assert split_complete("No end yet") == ([], "No end yet")
