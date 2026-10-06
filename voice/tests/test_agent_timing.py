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
