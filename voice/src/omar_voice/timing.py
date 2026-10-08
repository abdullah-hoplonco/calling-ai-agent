"""Per-turn timing on one clock: from the end of the Lead's last word to Omar's audio.

Why our own marks and not only LiveKit's metrics: with Deepgram Flux, LiveKit anchors
"the Lead stopped speaking" at the end of Flux's audio window, which already includes
Flux's end-of-turn wait. That wait then disappears from every number. Here the anchor
is the end time of the Lead's LAST WORD (from the transcript's word timestamps), and
every later step is a wall-clock mark, so the parts add up exactly to the total.

    user_end ──flux── stt_final ──commit── commit ──tool── reply_start ──llm── first_token
             ──guard── first_out ──tts── playout

No LiveKit imports: the agent feeds marks in, tests feed synthetic marks.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, field
from typing import Any


class AudioClock:
    """Maps "seconds of audio sent to STT" to the wall time that audio arrived.

    STT word times count seconds of audio from the start of the STT input stream.
    The agent records every frame it forwards to STT, so a word's end time can be
    turned into the wall time when that sound reached the worker.
    """

    def __init__(self, keep_seconds: float = 120.0) -> None:
        self._starts: list[float] = []  # stream time at the start of each frame
        self._walls: list[float] = []  # wall time when that frame arrived
        self._durations: list[float] = []
        self._stream_pos = 0.0
        self._keep = keep_seconds

    def add_frame(self, duration_s: float, wall: float) -> None:
        self._starts.append(self._stream_pos)
        self._walls.append(wall)
        self._durations.append(duration_s)
        self._stream_pos += duration_s
        while self._starts and self._stream_pos - self._starts[0] > self._keep:
            self._starts.pop(0)
            self._walls.pop(0)
            self._durations.pop(0)

    @property
    def stream_pos(self) -> float:
        return self._stream_pos

    def wall_at(self, stream_s: float) -> float | None:
        """Wall time when the audio at `stream_s` arrived, or None if unknown."""
        if not self._starts or stream_s < self._starts[0] or stream_s > self._stream_pos:
            return None
        i = bisect.bisect_right(self._starts, stream_s) - 1
        return self._walls[i] + (stream_s - self._starts[i])


@dataclass
class LlmRequest:
    start: float
    first_token: float | None = None  # first text or tool-call chunk from the model
    end: float | None = None
    tool_call: bool = False
    # preemptive draft: started before the turn was final (see OmarAgent.llm_node)
    early: bool = False
    user_id: str | None = None  # the Lead message this request answers
    first_out: float | None = None  # first guarded sentence of this request
    cancelled: bool = False  # stopped before its stream ended
    # from LiveKit's LLM metrics for this request (set when the request finishes)
    provider: str | None = None  # "groq" | "deepseek"
    model: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    price_band: str | None = None


@dataclass
class TurnMarks:
    """Wall-clock marks for one Lead turn and Omar's reply (time.time() seconds)."""

    lead_text: str = ""
    user_end: float | None = None  # end of the Lead's last word
    user_end_source: str = "none"  # "words" | "livekit" | "none"
    stt_final: float | None = None  # final transcript reached the worker
    commit: float | None = None  # turn committed: on_user_turn_completed (voice) or llm_node
    end_of_speech: float | None = None  # STT's END_OF_SPEECH reached the worker (diagnostic)
    requests: list[LlmRequest] = field(default_factory=list)
    first_out: float | None = None  # first guarded sentence handed to TTS
    playout: float | None = None  # Omar's first audio frame sent to the room
    scripted: bool = False  # code spoke a scripted line, no LLM reply
    tts_ttfb: list[float] = field(default_factory=list)  # per TTS segment (s)
    tts_gen_s: float = 0.0  # TTS generation time, summed over segments
    tts_audio_s: float = 0.0  # audio produced, summed over segments
    interrupted: bool = False


def _ms(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return round(max(b - a, 0.0) * 1000, 1)


def _not_before(t: float | None, floor: float | None) -> float | None:
    if t is None or floor is None:
        return t
    return max(t, floor)


def breakdown(m: TurnMarks) -> dict[str, Any]:
    """The named parts of one turn, in ms. Parts are consecutive, so they sum to the total.

    Parts that do not apply are None (e.g. no tool step, scripted line).
    """
    reply = next((r for r in reversed(m.requests) if not r.tool_call), None)
    if reply is None and m.requests:
        reply = m.requests[-1]
    tool_steps = [r for r in m.requests if r is not reply]
    # a preemptive draft may have produced text before the commit: the Lead could not hear
    # it earlier than the commit, so later marks are clamped to it and the parts still add up
    floor = m.commit
    first_token = _not_before(reply.first_token, floor) if reply else None
    first_out = _not_before(m.first_out, first_token or floor)

    out: dict[str, Any] = {
        "userEndSource": m.user_end_source,
        "turnDetectMs": _ms(m.user_end, m.stt_final),
        "commitMs": _ms(m.stt_final, m.commit),
        "toolMs": None,
        "llmMs": None,
        "guardMs": None,
        "ttsMs": None,
        "totalMs": _ms(m.user_end, m.playout),
        "serverTotalMs": _ms(m.stt_final or m.commit, m.playout),
        "ttsTtfbMs": round(m.tts_ttfb[0] * 1000, 1) if m.tts_ttfb else None,
        "ttsRealtimeFactor": round(m.tts_gen_s / m.tts_audio_s, 2) if m.tts_audio_s else None,
        "llmRequests": len(m.requests),
        "llmProvider": (reply or (m.requests[-1] if m.requests else None)).provider
        if (reply or m.requests)
        else None,
        "llmModel": (reply or (m.requests[-1] if m.requests else None)).model
        if (reply or m.requests)
        else None,
        "promptTokens": sum(r.prompt_tokens for r in m.requests),
        "completionTokens": sum(r.completion_tokens for r in m.requests),
        "llmCostUsd": round(sum(r.cost_usd for r in m.requests), 8),
        "toolTurn": bool(tool_steps),
        "preemptive": bool(reply and reply.early),
        # how long before the commit the reply's LLM request started (preemptive head start)
        "headStartMs": _ms(reply.start, m.commit) if reply and reply.early else None,
        # diagnostics for the commit step: STT end of speech -> commit; commit -> LLM request
        "eouWaitMs": _ms(m.end_of_speech, m.commit),
        "llmStartMs": _ms(m.commit, reply.start) if reply and not reply.early else None,
        "scripted": m.scripted,
        "interrupted": m.interrupted,
    }
    if m.scripted:
        # code spoke a scripted line. With an LLM tool step first (e.g. the LLM reported
        # an event and code answered), the tool step is its own part.
        if m.requests:
            last_end = m.requests[-1].end
            out["toolMs"] = _ms(m.commit, last_end)
            out["ttsMs"] = _ms(last_end, m.playout)
        else:
            out["ttsMs"] = _ms(m.commit, m.playout)
        return _check(out)
    if reply is None:
        return _check(out)
    if tool_steps:
        out["toolMs"] = _ms(m.commit, reply.start)
        out["llmMs"] = _ms(_not_before(reply.start, floor), first_token)
    else:
        out["llmMs"] = _ms(m.commit, first_token)
    out["guardMs"] = _ms(first_token, first_out)
    out["ttsMs"] = _ms(first_out, m.playout)
    return _check(out)


def _check(out: dict[str, Any]) -> dict[str, Any]:
    """unexplainedMs = total - sum of parts. Near 0 when every mark is present and in order."""
    total = out["totalMs"]
    out["unexplainedMs"] = None if total is None else round(total - parts_sum_ms(out), 1)
    return out


PARTS = ("turnDetectMs", "commitMs", "toolMs", "llmMs", "guardMs", "ttsMs")


def parts_sum_ms(b: dict[str, Any]) -> float:
    return round(sum(b[p] or 0.0 for p in PARTS), 1)


class VoiceEnd:
    """When the Lead's voice was last louder than the background, from the audio itself.

    Provider timestamps are not exact enough for a start mark: in a ground-truth test,
    Deepgram Flux word end times were off by up to 0.38 s. The worker sees every audio
    frame, so it can mark the last voiced frame directly. The background level is
    tracked continuously (fast down, slow up), so a noisy room does not count as voice.
    """

    def __init__(self, min_dbfs: float = -45.0, margin_db: float = 12.0) -> None:
        self.min_dbfs = min_dbfs
        self.margin_db = margin_db
        self.floor_dbfs = -70.0
        self.last_voiced: float | None = None

    def add(self, level_dbfs: float, wall_end: float) -> None:
        if level_dbfs < self.floor_dbfs:
            self.floor_dbfs = level_dbfs
        else:
            self.floor_dbfs += 0.002 * (level_dbfs - self.floor_dbfs)
        if level_dbfs > max(self.min_dbfs, self.floor_dbfs + self.margin_db):
            self.last_voiced = wall_end
