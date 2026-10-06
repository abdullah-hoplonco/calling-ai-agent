import pytest

from omar_voice.timing import AudioClock, LlmRequest, TurnMarks, breakdown, parts_sum_ms

T0 = 1_000.0


def test_audio_clock_maps_stream_time_to_arrival():
    c = AudioClock()
    for i in range(100):  # 100 frames of 20 ms, arriving in real time from T0
        c.add_frame(0.02, T0 + i * 0.02)
    assert c.wall_at(0.0) == pytest.approx(T0)
    assert c.wall_at(1.234) == pytest.approx(T0 + 1.234)
    assert c.wall_at(5.0) is None  # not received yet


def test_audio_clock_keeps_mapping_when_frames_arrive_late():
    c = AudioClock()
    c.add_frame(0.02, T0)
    c.add_frame(0.02, T0 + 0.5)  # network stall: second frame arrives late
    assert c.wall_at(0.03) == pytest.approx(T0 + 0.51)


def plain_turn():
    return TurnMarks(
        lead_text="We run four laundry shops",
        user_end=T0,
        user_end_source="words",
        stt_final=T0 + 0.45,  # Flux waited 450 ms
        commit=T0 + 0.65,
        requests=[LlmRequest(start=T0 + 0.66, first_token=T0 + 0.95, end=T0 + 1.3)],
        first_out=T0 + 1.10,
        playout=T0 + 1.35,
        tts_ttfb=[0.2],
        tts_gen_s=1.0,
        tts_audio_s=4.0,
    )


def test_plain_turn_parts_sum_to_total():
    b = breakdown(plain_turn())
    assert b["totalMs"] == 1350.0
    assert b["turnDetectMs"] == 450.0
    assert b["commitMs"] == 200.0
    assert b["llmMs"] == 300.0  # commit -> first token, includes request setup
    assert b["guardMs"] == 150.0
    assert b["ttsMs"] == 250.0
    assert b["toolMs"] is None
    assert parts_sum_ms(b) == b["totalMs"] and b["unexplainedMs"] == 0.0
    assert b["ttsRealtimeFactor"] == 0.25 and b["ttsTtfbMs"] == 200.0


def test_tool_turn_splits_tool_step_from_reply():
    m = plain_turn()
    m.requests = [
        LlmRequest(start=T0 + 0.66, first_token=T0 + 0.9, end=T0 + 0.95, tool_call=True),
        LlmRequest(start=T0 + 1.0, first_token=T0 + 1.3, end=T0 + 1.6),
    ]
    m.first_out, m.playout = T0 + 1.45, T0 + 1.7
    b = breakdown(m)
    assert b["toolTurn"] and b["llmRequests"] == 2
    assert b["toolMs"] == 350.0 and b["llmMs"] == 300.0
    assert parts_sum_ms(b) == b["totalMs"] == 1700.0


def test_scripted_turn_has_no_llm_parts():
    m = TurnMarks(
        user_end=T0,
        user_end_source="words",
        stt_final=T0 + 0.4,
        commit=T0 + 0.5,
        playout=T0 + 0.8,
        scripted=True,
    )
    b = breakdown(m)
    assert b["llmMs"] is None and b["ttsMs"] == 300.0
    assert b["totalMs"] == 800.0 and b["unexplainedMs"] == 0.0


def test_missing_marks_are_reported_not_hidden():
    m = plain_turn()
    m.user_end, m.user_end_source = None, "none"
    b = breakdown(m)
    assert b["totalMs"] is None and b["turnDetectMs"] is None
    assert b["serverTotalMs"] == 900.0  # from final transcript to audio
    assert b["unexplainedMs"] is None


def test_scripted_after_tool_step_counts_the_tool_step():
    m = TurnMarks(
        user_end=T0,
        user_end_source="words",
        stt_final=T0 + 0.4,
        commit=T0 + 0.5,
        requests=[LlmRequest(start=T0 + 0.5, first_token=T0 + 0.8, end=T0 + 0.85, tool_call=True)],
        playout=T0 + 1.2,
        scripted=True,
    )
    b = breakdown(m)
    assert b["toolMs"] == 350.0 and b["ttsMs"] == 350.0
    assert b["unexplainedMs"] == 0.0
