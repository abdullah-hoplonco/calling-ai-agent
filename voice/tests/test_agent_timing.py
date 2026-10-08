"""The agent's timing hooks, driven with a synthetic turn (no LiveKit session)."""

from types import SimpleNamespace

import pytest

from omar_core import DEFAULT_LEAD
from omar_voice.agent import OmarAgent
from omar_voice.controller import CallController
from omar_voice.settings import Settings
from omar_voice.timing import AudioClock, LlmRequest


class Bus:
    def __init__(self):
        self.sent = []

    def send(self, topic, payload):
        self.sent.append((topic, payload))


class Word(str):
    end_time: float


def word(text, end):
    w = Word(text)
    w.end_time = end
    return w


@pytest.fixture
def agent(monkeypatch):
    clock = {"t": 1000.0}
    monkeypatch.setattr("omar_voice.agent.time.time", lambda: clock["t"])
    a = OmarAgent(CallController(lead=DEFAULT_LEAD), Settings(), Bus())
    a.controller.start()
    return a, clock


def test_turn_measured_from_last_word_end(agent):
    a, clock = agent
    audio = AudioClock()
    for i in range(300):  # 6 s of audio arriving in real time from t=994
        audio.add_frame(0.02, 994.0 + i * 0.02)
    alt = SimpleNamespace(words=[word("yes", 4.5), word("speaking", 5.0)], end_time=5.6)

    clock["t"] = 999.5  # Flux sends the final transcript at 999.5 (word ended at 999.0)
    a._note_final_transcript(alt, audio)
    clock["t"] = 999.7  # turn committed
    a._start_turn("Yes, speaking", {})
    req = LlmRequest(start=999.7, first_token=1000.0, end=1000.3)
    a.marks.requests.append(req)
    a.marks.first_out = 1000.1
    a.on_tts_metrics(ttfb=0.15, duration=0.5, audio_duration=2.0)
    a.on_assistant_message(
        SimpleNamespace(
            metrics={"started_speaking_at": 1000.35}, text_content="Great.", interrupted=False
        )
    )
    a.finish()

    row = a.book.rows[1]
    assert row["userEndSource"] == "words"
    assert row["turnDetectMs"] == pytest.approx(500.0)  # 999.0 -> 999.5
    assert row["commitMs"] == pytest.approx(200.0)
    assert row["llmMs"] == pytest.approx(300.0)
    assert row["guardMs"] == pytest.approx(100.0)
    assert row["ttsMs"] == pytest.approx(250.0)
    assert row["totalMs"] == pytest.approx(1350.0)
    assert row["unexplainedMs"] == pytest.approx(0.0, abs=0.2)
    assert row["ttsRealtimeFactor"] == 0.25
    assert any(t == "omar.latency" for t, _ in a.bus.sent)


def test_falls_back_to_livekit_anchor_without_words(agent):
    a, clock = agent
    clock["t"] = 1000.0
    a._start_turn("hello", {"stopped_speaking_at": 999.2})
    assert a.marks.user_end == 999.2 and a.marks.user_end_source == "livekit"


def test_greeting_row_is_shown_but_not_measured(agent):
    a, _ = agent
    a.on_assistant_message(
        SimpleNamespace(
            metrics={"started_speaking_at": 1000.0},
            text_content="Hi, is this Khalifa?",
            interrupted=False,
        )
    )
    assert a.book.rows[1]["totalMs"] is None and a.book.summary()["overall"]["n"] == 0


def test_audio_based_end_wins_over_word_times(agent):
    a, clock = agent
    from omar_voice.timing import VoiceEnd

    a._voice_end = VoiceEnd()
    for i in range(100):  # 1 s of voice at -20 dBFS, then 1 s of silence, frames of 10 ms
        a._voice_end.add(-20.0 if i < 50 else -80.0, 998.0 + i * 0.02)
    audio = AudioClock()
    audio.add_frame(10.0, 990.0)
    alt = SimpleNamespace(words=[word("yes", 9.5)], end_time=9.9)
    clock["t"] = 1000.0
    a._note_final_transcript(alt, audio)
    assert a._pending_user["user_end_source"] == "audio"
    assert a._pending_user["user_end"] == pytest.approx(998.98)


def test_llm_request_gets_provider_tokens_and_cost(agent):
    a, clock = agent
    clock["t"] = 1000.0
    a._start_turn("Tell me more", {"stopped_speaking_at": 999.0})
    a.marks.requests.append(LlmRequest(start=1000.0, first_token=1000.6, end=1001.0))
    a.on_llm_metrics("api.deepseek.com", "deepseek-flash", 0.6, 1.0, 1300, 60)
    req = a.marks.requests[0]
    assert req.provider == "deepseek" and req.prompt_tokens == 1300 and req.cost_usd > 0
    u = a.usage["deepseek"]
    assert u["requests"] == 1 and u["costUsd"] == pytest.approx(req.cost_usd)
    a.on_llm_metrics("api.groq.com", "qwen/qwen3.8-27b", 0.2, 0.5, 1200, 50)
    assert a.usage["groq"]["costUsd"] == 0.0  # free tier


async def test_key_format_checked_before_any_network_call():
    from omar_voice.agent import check_deepseek_key

    assert "does not look like" in await check_deepseek_key("hello")
    assert "does not look like" in await check_deepseek_key("")


def test_preemptive_draft_changes_no_state_until_the_turn_commits(agent):
    """Voice calls: a draft LLM request before the commit is held aside, then adopted."""
    a, _clock = agent
    a.turn_hook = True
    stage = a.controller.stage
    draft = LlmRequest(start=999.0, first_token=999.3, user_id="draft-1")
    a._track_request(draft)
    assert draft.early and a._early_reqs == [draft]
    assert a.controller.stage is stage and a.marks is None  # nothing committed yet
    a._note_first_out(draft)
    assert draft.first_out == 1000.0 and a.marks is None


def test_dropped_draft_is_replaced_by_the_fresh_request(agent):
    a, _clock = agent
    a.turn_hook = True
    a._start_turn("we mostly use whatsapp", {})
    draft = LlmRequest(start=999.0, first_token=999.3, user_id="draft-1", early=True)
    a.marks.requests.append(draft)
    a._committed_ids.update({"draft-1", "final-1"})
    fresh = LlmRequest(start=1000.0, user_id="final-1")
    a._track_request(fresh)
    assert a.marks.requests == [fresh]


def test_adopted_draft_counts_from_the_commit(agent):
    """Text the draft made before the commit cannot be heard earlier than the commit."""
    a, clock = agent
    clock["t"] = 1000.0
    a._start_turn("we mostly use whatsapp", {})
    a.marks.stt_final = 999.8
    a.marks.user_end = 999.0
    draft = LlmRequest(start=999.4, first_token=999.7, user_id="d", early=True)
    a.marks.requests.append(draft)
    a.marks.first_out = 999.8
    a.on_assistant_message(
        SimpleNamespace(
            metrics={"started_speaking_at": 1000.3}, text_content="Ha.", interrupted=False
        )
    )
    a.finish()
    row = a.book.rows[1]
    assert row["preemptive"] and row["headStartMs"] == pytest.approx(600.0)
    assert row["llmMs"] == 0.0 and row["guardMs"] == 0.0
    assert row["ttsMs"] == pytest.approx(300.0)
    assert row["unexplainedMs"] == pytest.approx(0.0, abs=0.2)
