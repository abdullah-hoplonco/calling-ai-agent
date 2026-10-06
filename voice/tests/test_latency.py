import json

from omar_voice.latency import LatencyBook, percentile


def row(turn, total, stage="INFO", tool=False, scripted=False, tts_rtf=0.3):
    return {
        "turn": turn,
        "stage": stage,
        "totalMs": total,
        "turnDetectMs": 400.0,
        "commitMs": 200.0,
        "toolMs": 300.0 if tool else None,
        "llmMs": 250.0,
        "guardMs": 100.0,
        "ttsMs": 200.0,
        "ttsTtfbMs": 150.0,
        "ttsRealtimeFactor": tts_rtf,
        "toolTurn": tool,
        "scripted": scripted,
    }


def test_percentile():
    assert percentile([], 50) is None
    assert percentile([1, 2, 3, 4], 50) == 2
    assert percentile(list(range(1, 101)), 95) == 95


def test_put_replaces_preliminary_row_and_logs_final_only(tmp_path):
    log = tmp_path / "lat.jsonl"
    book = LatencyBook(log_path=log)
    book.put(row(1, 1100.0, tts_rtf=None), final=False)
    book.put(row(1, 1100.0, tts_rtf=0.4), final=True)
    assert len(book.rows) == 1 and book.rows[1]["ttsRealtimeFactor"] == 0.4
    lines = log.read_text().splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["ttsRealtimeFactor"] == 0.4


def test_summary_groups_and_pass():
    book = LatencyBook()
    for i, (total, stage, tool, scripted) in enumerate(
        [
            (700.0, "INFO", False, False),
            (800.0, "INFO", False, False),
            (1400.0, "BOOKING_PREF", True, False),
            (600.0, "OPENING", False, True),
        ]
    ):
        book.put(row(i, total, stage, tool, scripted), final=True)
    book.put({"turn": 9, "stage": "IDENTITY", "totalMs": None}, final=True)  # greeting
    s = book.summary()
    assert s["overall"]["n"] == 4
    assert s["overall"]["totalMs"]["p50"] == 700.0
    assert s["byStage"]["BOOKING_PREF"]["totalMs"]["p50"] == 1400.0
    assert s["toolTurns"]["n"] == 1 and s["plainTurns"]["n"] == 2 and s["scriptedTurns"]["n"] == 1
    assert s["pass"] is True
