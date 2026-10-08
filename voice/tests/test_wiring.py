"""The real session builds with both turn modes. Fake keys; nothing connects."""

import pytest

from omar_voice.agent import build_llm, build_session, parse_lead
from omar_voice.settings import Settings

FAKE_KEYS = {
    "GROQ_API_KEY": "gsk_test",
    "DEEPGRAM_API_KEY": "dg_test",
    "CARTESIA_API_KEY": "ct_test",
}


@pytest.fixture(autouse=True)
def keys(monkeypatch):
    for k, v in FAKE_KEYS.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)


@pytest.mark.parametrize("mode", ["flux", "livekit"])
async def test_session_builds(monkeypatch, mode):
    monkeypatch.setenv("TURN_MODE", mode)
    settings = Settings()
    session = build_session(settings, vad=None)
    assert session is not None
    assert settings.min_delay == (0.0 if mode == "flux" else 0.3)


def test_endpointing_override(monkeypatch):
    monkeypatch.setenv("ENDPOINTING_MIN_DELAY", "0.2")
    assert Settings().min_delay == 0.2


def test_fallback_llm_when_deepseek_key(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds_test")
    assert type(build_llm(Settings())).__name__ == "FallbackAdapter"
    monkeypatch.delenv("DEEPSEEK_API_KEY")
    assert type(build_llm(Settings())).__name__ == "LLM"


def test_parse_lead_from_dispatch_metadata():
    lead = parse_lead(
        '{"lead": {"name": "Rhea Fernandes", "email": "rhea.f@example.com", "leadType": "old", "submittedMonth": "March"}}'
    )
    assert lead.first_name == "Rhea" and lead.lead_type == "old" and lead.submitted_month == "March"
    assert parse_lead("").first_name == "Khalifa"
    assert parse_lead("not json").first_name == "Khalifa"


def test_flux_threshold_default_is_flux_default():
    assert Settings().flux_eot_threshold == 0.7


def test_provider_switch(monkeypatch):
    from omar_voice.agent import llm_label, parse_llm_choice, resolve_provider

    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds_test")
    s = Settings()
    assert s.llm_provider == "auto"
    assert resolve_provider(s, "deepseek") == "deepseek"
    assert resolve_provider(s, None) == "auto"
    assert build_llm(s, "deepseek").model == s.deepseek_model
    assert build_llm(s, "groq").model == s.groq_model
    auto = build_llm(s, "auto")
    assert type(auto).__name__ == "FallbackAdapter"
    assert [m.model for m in auto._llm_instances] == [s.deepseek_model, s.groq_model]
    assert "DeepSeek" in llm_label(s, "deepseek")
    assert parse_llm_choice('{"lead": {}, "llm": "deepseek"}') == "deepseek"
    assert parse_llm_choice('{"llm": "gpt"}') is None and parse_llm_choice("") is None


def test_deepseek_without_key_falls_back_to_groq(monkeypatch):
    from omar_voice.agent import resolve_provider

    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    assert resolve_provider(Settings(), "deepseek") == "groq"
    assert resolve_provider(Settings(), "auto") == "groq"


def test_env_selects_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    assert Settings().llm_provider == "deepseek"
    monkeypatch.setenv("LLM_PROVIDER", "nonsense")
    assert Settings().llm_provider == "auto"


def test_voice_choice_allowlist():
    from omar_voice.agent import parse_voice_choice

    v = parse_voice_choice('{"voice": "ef191366-f52f-447a-a398-ed8c0f2943a1"}')
    assert v and v[2] == "Hamza" and "British male" in v[1]
    assert parse_voice_choice('{"voice": "f8f5f1b2-f02d-4d8e-a40d-fd850a487b3d"}')[2] == "Nimra"
    assert parse_voice_choice('{"voice": "not-a-listed-voice"}') is None


def test_voice_picks_the_tts_engine():
    from dataclasses import replace

    from omar_voice.agent import build_tts, tts_engine

    eleven = "4O1sYUnmtThcBoSBrri7"
    cart = "6ccbfb76-1fc6-48f7-b71d-91ac6298247b"
    with_key = replace(Settings(), eleven_api_key="test-key")
    no_key = replace(Settings(), eleven_api_key="")
    assert tts_engine(with_key, eleven) == "elevenlabs"
    assert tts_engine(with_key, cart) == "cartesia"
    assert tts_engine(no_key, eleven) == "cartesia"  # no key: fall back, do not fail the call
    from livekit.plugins import deepgram, elevenlabs

    assert isinstance(build_tts(with_key, eleven), elevenlabs.TTS)
    # the turn test speaks with Deepgram Aura and reads no mood tags
    test_voice = replace(with_key, tts_override="deepgram")
    assert tts_engine(test_voice, eleven) == "deepgram"
    assert isinstance(build_tts(test_voice, eleven), deepgram.TTS)


def test_eleven_voice_id_is_the_default_when_page_sends_none():
    from dataclasses import replace

    from omar_voice.agent import tts_engine

    s = replace(Settings(), eleven_api_key="k", eleven_voice="4O1sYUnmtThcBoSBrri7")
    assert tts_engine(s, None) == "elevenlabs"
    assert tts_engine(replace(s, eleven_api_key=""), None) == "cartesia"


async def test_blocked_eleven_voice_falls_back_to_free_voice(monkeypatch):
    from dataclasses import replace

    import omar_voice.agent as a
    from omar_voice.voices import ELEVEN_FREE_VOICE

    async def blocked(settings, voice_id):
        return 402

    monkeypatch.setattr(a, "eleven_voice_status", blocked)
    s = replace(Settings(), eleven_api_key="k", eleven_voice="4O1sYUnmtThcBoSBrri7")
    voice, note = await a.usable_voice(s, "4O1sYUnmtThcBoSBrri7")
    assert voice == ELEVEN_FREE_VOICE and "paid" in note
    assert a.tts_engine(s, voice) == "elevenlabs"
    # a Cartesia voice is never checked
    assert await a.usable_voice(s, "6ccbfb76-1fc6-48f7-b71d-91ac6298247b") == (
        "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",
        "",
    )


def test_stability_from_page_is_validated():
    from omar_voice.agent import parse_stability

    assert parse_stability('{"stability": 0.15}') == 0.15
    assert parse_stability('{"stability": 0}') == 0.0
    assert parse_stability('{"stability": 1.5}') is None
    assert parse_stability('{"stability": "0.2"}') is None
    assert parse_stability('{"stability": true}') is None
    assert parse_stability("not json") is None


def test_turn_presets_from_metadata():
    from omar_voice.agent import parse_turn_choice
    from omar_voice.settings import with_turn_preset

    base = Settings()
    eager = with_turn_preset(base, parse_turn_choice('{"turn": "flux-eager"}'))
    assert eager.turn_mode == "flux" and eager.flux_eager_eot_threshold == 0.4
    assert eager.preemptive_generation
    v1 = with_turn_preset(base, parse_turn_choice('{"turn": "livekit-v1"}'))
    assert v1.turn_mode == "livekit" and v1.livekit_turn_model == "v1"
    assert with_turn_preset(base, parse_turn_choice('{"turn": "rm -rf"}')) == base
    assert parse_turn_choice("not json") is None


async def test_eager_threshold_reaches_flux(monkeypatch):
    from dataclasses import replace

    for k in ("LIVEKIT_URL", "DEEPGRAM_API_KEY", "GROQ_API_KEY", "CARTESIA_API_KEY"):
        monkeypatch.setenv(k, "x")
    s = replace(Settings(), flux_eager_eot_threshold=0.4, preemptive_generation=True)
    session = build_session(s, vad=None)
    assert session.stt._opts.eager_eot_threshold == 0.4


async def test_hindi_call_uses_multilingual_stt(monkeypatch):
    from dataclasses import replace

    from omar_voice.agent import parse_hindi_choice

    assert parse_hindi_choice('{"lang": "hi"}') is True
    assert parse_hindi_choice('{"lang": "en"}') is False
    assert parse_hindi_choice('{"lead": {}}') is None and parse_hindi_choice("") is None
    monkeypatch.setenv("LIVEKIT_URL", "x")
    flux = build_session(replace(Settings(), hindi=True), vad=None).stt._opts
    assert flux.model == "flux-general-multi" and flux.language_hint == ["en", "hi"]
    assert build_session(Settings(), vad=None).stt._opts.model == "flux-general-en"
    nova = build_session(replace(Settings(), hindi=True, turn_mode="livekit"), vad=None)
    assert nova.stt._opts.language == "multi"
