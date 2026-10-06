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
def test_session_builds(monkeypatch, mode):
    monkeypatch.setenv("TURN_MODE", mode)
    settings = Settings()
    session = build_session(settings, vad=None)
    assert session is not None
    assert settings.min_delay == (0.2 if mode == "flux" else 0.3)


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
