"""Hindi calls (CallConfig.hindi): language follow, scripted lines, guards, quick events."""

import pytest

from omar_core import DEFAULT_LEAD, CallConfig, Event, Stage, start, transition
from omar_core.expressive import render
from omar_core.guards import check_sentence, split_complete
from omar_core.lang import BRAND, detect, fix_brand, gendered
from omar_core.prompts import instructions
from omar_core.quick_events import quick_event


def hindi_call(**cfg):
    s = start(DEFAULT_LEAD, CallConfig(hindi=True, **cfg))
    s, _ = transition(s, Event.ANSWERED)
    return s


@pytest.mark.parametrize(
    ("text", "lang"),
    [
        ("जी, बोल रहा हूँ", "hi"),
        ("आपकी website का budget कितना है", "hi"),  # Hindi with English words
        ("haan ji main bol raha hoon", "hi"),  # Roman Hindi
        ("Yes, speaking", "en"),
        ("ok", None),  # too short to tell
    ],
)
def test_detect(text, lang):
    assert detect(text) == lang


@pytest.mark.parametrize(
    "text",
    ["मैं होपलॉन एंड को से हूँ।", "हॉप्लॉन and Co की team", "Hoplon & Co", "होपलॉन"],
)
def test_brand_stays_in_english(text):
    assert BRAND in fix_brand(text)
    assert "होप" not in fix_brand(text) and "हॉप" not in fix_brand(text)


def test_render_fixes_the_brand_for_tts():
    assert render("[happy] मैं होपलॉन एंड को से हूँ।", "elevenlabs").endswith(f"{BRAND} से हूँ।")


def test_gendered_verbs():
    assert gendered("मैं बोल {g:रही/रहा} हूँ", True) == "मैं बोल रही हूँ"
    assert gendered("मैं बोल {g:रही/रहा} हूँ", False) == "मैं बोल रहा हूँ"


def test_scripted_lines_follow_the_lead():
    s = hindi_call()
    s.language = "hi"
    s, fx = transition(s, Event.CONFIRM_IDENTITY)
    assert "Hoplon and Co से Nimra बोल रही हूँ" in fx.say
    assert "record" in fx.say  # the legal recording notice is still there
    s.language = "en"
    s, fx = transition(s, Event.NOT_INTERESTED)
    assert fx.say == "Understood, I won't call again. Have a great day!"


def test_male_agent_speaks_male_hindi():
    s = hindi_call(agent_name="Hamza", agent_female=False)
    s.language = "hi"
    s, fx = transition(s, Event.CONFIRM_IDENTITY)
    assert "Hamza बोल रहा हूँ" in fx.say


def test_english_only_call_never_speaks_hindi():
    s = start(DEFAULT_LEAD)
    s, _ = transition(s, Event.ANSWERED)
    s.language = "hi"  # cannot happen in practice (controller only follows with hindi on)
    s, fx = transition(s, Event.CONFIRM_IDENTITY)
    assert fx.say.startswith("Hi Khalifa, this is Nimra from Hoplon and Co.")


def test_prompt_has_the_language_rule_only_for_hindi_calls():
    s = hindi_call()
    s.language = "hi"
    p = instructions(s)
    assert "Reply language: Hindi" in p and "Hoplon and Co" in p and "a woman" in p
    assert "Reply language" not in instructions(start(DEFAULT_LEAD))


@pytest.mark.parametrize(
    ("sentence", "rule"),
    [
        ("इसमें लगभग दो से तीन हफ़्ते लगेंगे।", "no_timeline"),
        ("ये करीब पचास हज़ार रुपये का काम है।", "no_budget"),
        ("आपकी meeting बुक हो गई है।", "no_booked_before_calendar"),
        ("मैं एक असली इंसान हूँ।", "never_deny_ai"),
        ("मैं AI नहीं हूँ।", "never_deny_ai"),
        ("मैं आपको किसी इंसान से बात करवाती हूँ।", "say_my_manager"),
    ],
)
def test_hindi_guards(sentence, rule):
    v = check_sentence(sentence, booking_confirmed=False, lang="hi")
    assert v is not None and v.rule == rule
    assert any("ऀ" <= ch <= "ॿ" for ch in v.replacement)  # the safe line is Hindi


@pytest.mark.parametrize(
    "sentence",
    ["आपका दिन अच्छा रहे!", "2 के बाद call करती हूँ।", "मैं calendar पर confirm कर लेती हूँ।"],
)
def test_hindi_guards_allow_normal_sentences(sentence):
    assert check_sentence(sentence, booking_confirmed=False, lang="hi") is None


def test_hindi_sentences_split_on_danda():
    assert split_complete("नमस्ते। आप कैसे हैं? मैं ठीक") == (["नमस्ते।", "आप कैसे हैं?"], "मैं ठीक")


@pytest.mark.parametrize(
    ("text", "event"),
    [
        ("जी, बोल रहा हूँ", Event.CONFIRM_IDENTITY),
        ("हाँ जी", Event.CONFIRM_IDENTITY),
        ("गलत नंबर है", Event.WRONG_PERSON),
        ("जी नहीं", Event.IDENTITY_UNCLEAR),  # "no" is not a yes
    ],
)
def test_hindi_quick_events_identity(text, event):
    assert quick_event(hindi_call(), text) is event


@pytest.mark.parametrize(
    ("text", "event"),
    [
        ("हाँ जी, बताइए", Event.GOOD_TIME),
        ("अभी बिज़ी हूँ, बाद में कॉल करो", Event.NOT_NOW),
        ("मुझे इंटरेस्ट नहीं है", Event.NOT_INTERESTED),
        ("रिकॉर्डिंग मत करो", Event.OBJECTS_RECORDING),
    ],
)
def test_hindi_quick_events_opening(text, event):
    s, _ = transition(hindi_call(), Event.CONFIRM_IDENTITY)
    assert s.stage is Stage.OPENING
    assert quick_event(s, text) is event
