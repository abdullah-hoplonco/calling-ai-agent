from omar_core.expressive import EMOTIONS, plain, render
from omar_core.guards import check_sentence
from omar_core.lead import DEFAULT_LEAD
from omar_core.prompts import base_prompt


def test_cartesia_gets_its_tag_syntax():
    out = render("[Excited] Oh, that's brilliant! [laughs]", "cartesia")
    assert out == '<emotion value="excited"/> Oh, that\'s brilliant! [laughter]'


def test_warm_maps_to_cartesia_content():
    assert render("[warm] Hi there.", "cartesia") == '<emotion value="content"/> Hi there.'


def test_elevenlabs_keeps_bracket_tags():
    assert render("[curious] So, how's business? [chuckles]", "elevenlabs") == (
        "[curious] So, how's business? [laughs]"
    )


def test_unknown_moods_and_other_tags_are_dropped():
    text = '[angry] Fine. <speed ratio="2"/>Okay <b>then</b> [pause].'
    assert render(text, "elevenlabs") == "Fine. Okay then ."
    assert render(text, "cartesia") == "Fine. Okay then ."


def test_cartesia_style_input_is_accepted():
    assert render('<emotion value="happy"/> Hi.', "elevenlabs") == "[happy] Hi."


def test_plain_removes_everything_for_display_and_guards():
    assert plain("[happy] Great [laughs] news!") == "Great news!"


def test_guard_sees_words_not_tags():
    said = plain("[warm] It costs 5,000 AED.")
    assert check_sentence(said, booking_confirmed=False) is not None


def test_prompt_lists_the_allowed_moods():
    prompt = base_prompt(DEFAULT_LEAD)
    assert "[curious]" in prompt
    assert all(e in prompt for e in EMOTIONS)


def test_other_engines_get_words_only():
    assert render("[excited] Oh, brilliant! [laughs]", "deepgram") == "Oh, brilliant!"
