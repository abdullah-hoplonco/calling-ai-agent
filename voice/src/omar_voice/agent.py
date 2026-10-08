"""Omar's LiveKit agent worker.

LiveKit Agents runs the voice loop (audio in and out, turn-taking, barge-in).
This file connects that loop to our call state machine:

    Lead speaks -> STT -> [turn ends] -> llm_node (code counts rapport, sets stage)
               -> LLM -> report_lead_event tool -> CallController -> core/ transition
               -> scripted line (code speaks) or guide (LLM speaks)
               -> llm_node guard checks every sentence -> TTS -> Lead hears Omar

Run locally:  uv run omar-agent dev
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
import math
import os
import re
import sys
import time
from collections.abc import AsyncIterable
from datetime import UTC, datetime
from typing import Any

import aiohttp
import numpy as np
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    ModelSettings,
    RunContext,
    cli,
    function_tool,
    llm,
    stt,
)
from livekit.plugins import cartesia, deepgram, elevenlabs, openai, silero

from omar_core import DEFAULT_LEAD, CallConfig, Lead, Stage
from omar_core.expressive import plain, render
from omar_core.fake_calendar import FakeCalendar
from omar_core.guards import check_sentence, split_complete
from omar_core.knowledge import TOPICS, lookup
from omar_core.quick_events import quick_event

from .controller import CallController, Reply
from .latency import LatencyBook
from .pricing import PRICES_SOURCE, provider_of, request_cost
from .settings import LLM_PROVIDERS, TURN_PRESETS, Settings, missing_keys, with_turn_preset
from .timing import AudioClock, LlmRequest, TurnMarks, VoiceEnd, breakdown
from .voices import (
    CARTESIA,
    ELEVEN_FREE_VOICE,
    ELEVENLABS,
    MALE_NAME,
    engine_of,
    voice_choice,
)

try:  # internal helper: lets us change the instructions for the reply already being built
    from livekit.agents.voice.generation import update_instructions as _set_ctx_instructions
except ImportError:  # pragma: no cover
    _set_ctx_instructions = None

logger = logging.getLogger("omar")

TOPIC_STATE = "omar.state"
TOPIC_LATENCY = "omar.latency"
MAX_HISTORY_ITEMS = 10  # keeps each prompt small for Groq's free tier
_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


class Bus:
    """Sends JSON messages to the web page over the LiveKit room."""

    def __init__(self, room: rtc.Room) -> None:
        self._room = room
        self._tasks: set[asyncio.Task[None]] = set()

    def send(self, topic: str, payload: dict[str, Any]) -> None:
        async def _go() -> None:
            try:
                await self._room.local_participant.publish_data(
                    json.dumps(payload), topic=topic, reliable=True
                )
            except Exception:  # the page may have left
                logger.debug("publish to %s failed", topic, exc_info=True)

        task = asyncio.create_task(_go())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)


class OmarAgent(Agent):
    def __init__(
        self,
        controller: CallController,
        settings: Settings,
        bus: Bus,
        book: LatencyBook | None = None,
    ) -> None:
        self.controller = controller
        self.settings = settings
        self.bus = bus
        self.book = book or LatencyBook()
        # timing (see omar_voice.timing): marks of the current turn, on one clock
        self.marks: TurnMarks | None = None
        self._marks_turn: int | None = None  # row number of self.marks, once shown
        self._marks_stage = ""
        self._turn_no = 0
        self._pending_user: dict[str, Any] = {}
        # LLM usage of this call, per provider (cost assumes cache miss; see pricing.py)
        self.usage: dict[str, dict[str, Any]] = {}
        self.llm_label = ""
        self.voice_label = ""
        self.tts_engine = CARTESIA  # which TTS speaks: sets the mood-tag syntax
        self.turn_stage: str = controller.stage.value
        self.tool_turn = False
        self.scripted_texts: list[str] = []
        self.guard_hits: list[dict[str, str]] = []
        self._counted_user_id: str | None = None
        # Voice calls commit each Lead turn in on_user_turn_completed, so preemptive drafts
        # (LLM calls made while the Lead may still be talking) change no call state.
        # Text mode (evals) has no such hook: llm_node commits the turn itself.
        self.turn_hook = False
        self._committed_ids: set[str] = set()  # Lead messages of committed turns
        self._early_reqs: list[LlmRequest] = []  # drafts not yet matched to a turn
        self._silent_user_id: str | None = None  # turn already answered by a scripted line
        super().__init__(instructions=controller.instructions(), tools=self._stage_tools())

    # -- tools ------------------------------------------------------------

    def _stage_tools(self) -> list[llm.Tool]:
        tools: list[llm.Tool] = [self._lookup_tool()]
        menu = self.controller.event_menu()
        if menu:
            tools.append(self._report_tool(menu))
        return tools

    def _report_tool(self, menu: list[tuple[str, str]]) -> llm.Tool:
        schema = {
            "name": "report_lead_event",
            "description": (
                "Report what the Lead just did, before you reply, with no text in the same "
                "message. Options: " + "; ".join(f"{name} = {hint}" for name, hint in menu)
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "event": {"type": "string", "enum": [name for name, _ in menu]},
                    "detail": {
                        "type": "string",
                        "description": (
                            "The Lead's words when the event needs them: time preference, "
                            "chosen time, new email or callback time. Otherwise empty."
                        ),
                    },
                },
                "required": ["event"],
            },
        }

        async def report_lead_event(
            raw_arguments: dict[str, object], context: RunContext
        ) -> str | None:
            event = str(raw_arguments.get("event") or "")
            detail = str(raw_arguments.get("detail") or "").strip() or None
            return await self._on_report(event, detail, context)

        return function_tool(report_lead_event, raw_schema=schema)

    def _lookup_tool(self) -> llm.Tool:
        schema = {
            "name": "lookup_service",
            "description": "Get facts about Hoplon and Co before you answer a question about "
            "the company or a service.",
            "parameters": {
                "type": "object",
                "properties": {"topic": {"type": "string", "enum": list(TOPICS)}},
                "required": ["topic"],
            },
        }
        path = self.settings.knowledge_path

        async def lookup_service(raw_arguments: dict[str, object]) -> str:
            self.tool_turn = True
            return lookup(str(raw_arguments.get("topic") or ""), path)

        return function_tool(lookup_service, raw_schema=schema)

    async def _on_report(self, event: str, detail: str | None, context: RunContext) -> str | None:
        self.tool_turn = True
        reply = self.controller.report(event, detail)
        logger.info("report %s (%s) -> %s", event, detail, self.controller.stage.value)
        await self._refresh()
        if reply.say and not reply.guide and not reply.error:
            # The LLM may have started talking before it called the tool. Cut that off,
            # so the Lead hears only the scripted line, not two lines one after the other.
            try:
                context.speech_handle.interrupt(force=True)
            except Exception:
                logger.debug("could not interrupt the LLM's text", exc_info=True)
            if self.marks is not None:
                self.marks.scripted = True
            self._say(reply, context.session)
            return None  # code spoke; the LLM stays silent
        return reply.tool_output()

    # -- scripted speech and call end ---------------------------------------

    def _say(self, reply: Reply, session: AgentSession) -> None:
        assert reply.say
        self.scripted_texts.append(reply.say)
        # scripted lines get a mood too, or they sound flatter than the LLM's lines
        text = f"[{self.settings.script_emotion}] {reply.say}"
        handle = session.say(render(text, self.tts_engine), allow_interruptions=not reply.ended)
        if reply.ended:
            asyncio.create_task(self._end_after(handle, session))

    async def _end_after(self, handle: Any, session: AgentSession) -> None:
        try:
            await handle.wait_for_playout()
        finally:
            await asyncio.sleep(0.8)
            self.publish_state()
            session.shutdown(drain=True)

    # -- state ------------------------------------------------------------

    async def _refresh(self) -> None:
        await self.update_instructions(self.controller.instructions())
        await self.update_tools(self._stage_tools())
        self.publish_state()

    def publish_state(self) -> None:
        snap = self.controller.snapshot()
        snap["guardHits"] = self.guard_hits[-5:]
        snap["config"] = {
            "turnMode": self.settings.turn_mode,
            "minDelay": self.settings.min_delay,
            "model": self.llm_label or self.settings.groq_model,
            "guard": self.settings.output_guard,
            "preemptive": self.settings.preemptive_generation,
            "eagerEot": self.settings.flux_eager_eot_threshold or None,
            "turnModel": self.settings.livekit_turn_model
            if self.settings.turn_mode == "livekit"
            else None,
            "hindi": self.settings.hindi,
            "voice": self.voice_label,
        }
        snap["llmUsage"] = {
            "label": self.llm_label,
            "pricing": PRICES_SOURCE,
            "byProvider": self.usage,
            "totalCostUsd": round(sum(u["costUsd"] for u in self.usage.values()), 8),
        }
        self.bus.send(TOPIC_STATE, snap)

    # -- LiveKit hooks ----------------------------------------------------

    async def on_enter(self) -> None:
        reply = self.controller.start()
        await self._refresh()
        if reply.say:
            self._say(reply, self.session)

    async def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        tools: list[llm.Tool],
        model_settings: ModelSettings,
    ) -> AsyncIterable[llm.ChatChunk | str]:
        ctx = chat_ctx.copy()
        user_id = _last_user_id(ctx)
        if self.turn_hook:
            if user_id is not None and user_id == self._silent_user_id:
                return  # code answered this turn with a scripted line; no LLM call
        else:
            start = await self._on_new_lead_message(ctx)
            if start == "spoken":
                return  # code answered this turn with a scripted line; no LLM call
            if start == "moved":
                tools = self._stage_tools()  # the stage moved: offer this stage's events
        ctx.truncate(max_items=MAX_HISTORY_ITEMS)
        req = LlmRequest(start=time.time(), user_id=user_id)
        self._track_request(req)
        stream = Agent.default.llm_node(self, ctx, tools, model_settings)
        done = False
        try:
            if not self.settings.output_guard:
                async for chunk in stream:
                    self._note_chunk(req, chunk)
                    if isinstance(chunk, str) or (
                        isinstance(chunk, llm.ChatChunk) and chunk.delta and chunk.delta.content
                    ):
                        self._note_first_out(req)
                    yield chunk
                done = True
                return

            buf = ""
            async for chunk in stream:
                self._note_chunk(req, chunk)
                text: str | None = None
                if isinstance(chunk, str):
                    text = chunk
                elif isinstance(chunk, llm.ChatChunk):
                    if chunk.delta and chunk.delta.content:
                        text = chunk.delta.content
                    if chunk.delta and chunk.delta.tool_calls:
                        yield llm.ChatChunk(
                            id=chunk.id,
                            delta=llm.ChoiceDelta(
                                role="assistant", tool_calls=chunk.delta.tool_calls
                            ),
                            usage=chunk.usage,
                        )
                    elif chunk.usage and not text:
                        yield chunk
                if text:
                    buf += text
                    buf = _THINK.sub("", buf)
                    if "<think>" in buf:
                        continue  # wait for the end of a thinking block
                    sentences, buf = split_complete(buf)
                    for sentence in sentences:
                        self._note_first_out(req)
                        yield self._guard(sentence) + " "
            buf = _THINK.sub("", buf).replace("<think>", "").strip()
            if buf:
                self._note_first_out(req)
                yield self._guard(buf)
            done = True
        finally:
            req.end = time.time()
            req.cancelled = not done

    def _track_request(self, req: LlmRequest) -> None:
        """File an LLM request under its turn. A draft for a turn that is not committed yet
        waits in _early_reqs; on_user_turn_completed adopts it if LiveKit uses it."""
        if self.turn_hook and req.user_id not in self._committed_ids:
            req.early = True
            self._early_reqs = [*self._early_reqs[-2:], req]
            return
        if self.marks is None:
            return
        # a fresh request for this turn means LiveKit dropped the adopted draft
        self.marks.requests = [
            r for r in self.marks.requests if not r.early or r.user_id == req.user_id
        ]
        if not any(r.first_out for r in self.marks.requests):
            self.marks.first_out = None
        self.marks.requests.append(req)

    async def on_user_turn_completed(
        self, turn_ctx: llm.ChatContext, new_message: llm.ChatMessage
    ) -> None:
        """Voice calls: the Lead's turn is final. Code decides what it can (quick events,
        rapport turns) here, once per turn, and never for a draft that may be dropped."""
        if not self.turn_hook:
            return
        self._committed_ids.add(new_message.id)
        self._counted_user_id = new_message.id
        draft = next((r for r in reversed(self._early_reqs) if not r.cancelled), None)
        self._early_reqs = []
        text = (new_message.text_content or "").strip()
        start, guide = await self._commit_turn(text, dict(new_message.metrics or {}))
        if start == "spoken":
            # _refresh() gave the agent new tool objects, so LiveKit drops any draft
            self._silent_user_id = new_message.id
            return
        if start == "moved":
            self._use_stage_in(turn_ctx, guide)  # the draft used the old stage: dropped
            return
        if draft is not None and self.marks is not None:
            # LiveKit uses the draft when the final words match; if not, it calls
            # llm_node again and _track_request drops this one
            self._committed_ids.add(draft.user_id or "")
            self.marks.requests.append(draft)
            self.marks.first_out = draft.first_out

    async def _on_new_lead_message(self, ctx: llm.ChatContext) -> str | None:
        """Runs once per Lead turn, before the first LLM call for it.

        Code decides what it can without the LLM:
        - a clear yes/no in the identity check or legal opening (quick events);
        - rapport turns in INFO.
        Returns "spoken" when code already answered with a scripted line, "moved" when
        the stage changed (this reply uses the new stage), else None.
        Works in voice and in text mode.
        """
        last = next(
            (
                i
                for i in reversed(ctx.items)
                if getattr(i, "type", None) == "message" and i.role == "user"
            ),
            None,
        )
        if last is None or last.id == self._counted_user_id:
            return None
        self._counted_user_id = last.id
        text = (last.text_content or "").strip()
        start, guide = await self._commit_turn(text, dict(getattr(last, "metrics", None) or {}))
        if start == "moved":
            self._use_stage_in(ctx, guide)
        return start

    async def _commit_turn(
        self, text: str, user_metrics: dict[str, Any]
    ) -> tuple[str | None, str | None]:
        """One committed Lead turn: start its timing, then let code act on it.
        Returns ("spoken", None), ("moved", guide) or (None, None)."""
        self.tool_turn = False
        self.turn_stage = self.controller.stage.value
        self._start_turn(text, user_metrics)
        if not text:
            return None, None

        # a Hindi call follows the Lead's language: scripted lines and the prompt switch too
        lang_moved = self.controller.note_language(text)
        if lang_moved:
            logger.info("lead language -> %s", self.controller.state.language)

        quick = quick_event(self.controller.state, text)
        if quick is not None:
            reply = self.controller.code_event(quick)
            logger.info("quick %s -> %s", quick.value, self.controller.stage.value)
            await self._refresh()
            if reply.say and not reply.guide:
                if self.marks is not None:
                    self.marks.scripted = True
                self._say(reply, self.session)
                return "spoken", None
            return "moved", reply.guide

        if not self.controller.lead_turn() and not lang_moved:
            return None, None
        await self._refresh()
        return "moved", None

    def _use_stage_in(self, ctx: llm.ChatContext, guide: str | None) -> None:
        """Make the reply being built use the current stage (and a one-turn instruction)."""
        if _set_ctx_instructions is not None:
            _set_ctx_instructions(
                ctx, instructions=self.controller.instructions(), add_if_missing=True
            )
        if guide:
            ctx.add_message(role="system", content=f"Instruction for this reply: {guide}")

    # -- timing ---------------------------------------------------------------

    async def stt_node(
        self, audio: AsyncIterable[rtc.AudioFrame], model_settings: ModelSettings
    ) -> AsyncIterable[stt.SpeechEvent | str]:
        """Pass-through that records when each audio frame arrived, so the end time of
        the Lead's last word (from the transcript) becomes a wall-clock time."""
        clock = AudioClock()
        voice = VoiceEnd()
        self._voice_end = voice

        async def tap() -> AsyncIterable[rtc.AudioFrame]:
            async for frame in audio:
                now = time.time()
                clock.add_frame(frame.samples_per_channel / frame.sample_rate, now)
                voice.add(_frame_dbfs(frame), now)
                yield frame

        async for ev in Agent.default.stt_node(self, tap(), model_settings):
            if (
                isinstance(ev, stt.SpeechEvent)
                and ev.type == stt.SpeechEventType.FINAL_TRANSCRIPT
                and ev.alternatives
            ):
                self._note_final_transcript(ev.alternatives[0], clock)
            elif isinstance(ev, stt.SpeechEvent) and ev.type == stt.SpeechEventType.END_OF_SPEECH:
                self._pending_user.setdefault("end_of_speech", time.time())
            yield ev

    def _note_final_transcript(self, alt: stt.SpeechData, clock: AudioClock) -> None:
        now = time.time()
        end, source = None, "none"
        voice = getattr(self, "_voice_end", None)
        if voice is not None and voice.last_voiced is not None and 0 <= now - voice.last_voiced < 8:
            # the sound itself: last frame louder than the background (most exact)
            self._pending_user = {
                "user_end": voice.last_voiced,
                "user_end_source": "audio",
                "stt_final": now,
            }
            return
        last_word = alt.words[-1] if alt.words else None
        word_end = getattr(last_word, "end_time", None)
        if isinstance(word_end, int | float) and word_end > 0:
            end = clock.wall_at(float(word_end))
            source = "words" if end is not None else source
        if end is None and alt.end_time > 0:
            end = clock.wall_at(alt.end_time)  # end of the STT window: later than the word
            source = "window" if end is not None else source
        self._pending_user = {"user_end": end, "user_end_source": source, "stt_final": now}

    def _start_turn(self, text: str, user_metrics: dict[str, Any]) -> None:
        self._finish_turn(final=True)
        pending, self._pending_user = self._pending_user, {}
        user_end = pending.get("user_end")
        source = pending.get("user_end_source", "none")
        if user_end is None and user_metrics.get("stopped_speaking_at"):
            user_end, source = float(user_metrics["stopped_speaking_at"]), "livekit"
        self.marks = TurnMarks(
            lead_text=text,
            user_end=user_end,
            user_end_source=source,
            stt_final=pending.get("stt_final"),
            commit=time.time(),
            end_of_speech=pending.get("end_of_speech"),
        )
        self._marks_turn = None
        self._marks_stage = self.controller.stage.value

    def _note_chunk(self, req: LlmRequest, chunk: Any) -> None:
        if isinstance(chunk, llm.ChatChunk) and chunk.delta:
            if chunk.delta.tool_calls:
                req.tool_call = True
            if req.first_token is None and (chunk.delta.content or chunk.delta.tool_calls):
                req.first_token = time.time()
        elif isinstance(chunk, str) and chunk and req.first_token is None:
            req.first_token = time.time()

    def _note_first_out(self, req: LlmRequest) -> None:
        now = time.time()
        if req.first_out is None:
            req.first_out = now
        if (
            self.marks is not None
            and self.marks.first_out is None
            and any(r is req for r in self.marks.requests)
        ):
            self.marks.first_out = now

    def on_assistant_message(self, item: llm.ChatMessage) -> None:
        """Omar's reply started playing (or was cut): close the timing of this turn."""
        metrics = dict(getattr(item, "metrics", None) or {})
        started = metrics.get("started_speaking_at")
        marks = self.marks
        if marks is not None and marks.playout is None and started:
            marks.playout = float(started)
            marks.interrupted = bool(getattr(item, "interrupted", False))
            self._emit(marks, item.text_content or "", final=False)
            return
        # greeting, or a second line in the same turn: shown, but not a measured reply
        self._turn_no += 1
        self._put_row(
            {
                "turn": self._turn_no,
                "stage": self.controller.stage.value,
                "at": time.time(),
                "lead_text": "",
                "omar_text": plain(item.text_content or "")[:300],
                "totalMs": None,
                "scripted": plain(item.text_content or "")
                in (s.strip() for s in self.scripted_texts),
                "interrupted": bool(getattr(item, "interrupted", False)),
            },
            final=True,
        )

    def on_llm_metrics(
        self,
        provider_host: str,
        model: str,
        ttft: float,
        duration: float,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        """One finished LLM request: who served it, its tokens and its cost (cache miss)."""
        provider = provider_of(provider_host)
        cost = request_cost(provider, model, prompt_tokens, completion_tokens, datetime.now(UTC))
        if self.marks is not None:
            req = next((r for r in self.marks.requests if r.provider is None), None)
            if req is not None:
                req.provider, req.model = provider, model
                req.prompt_tokens, req.completion_tokens = prompt_tokens, completion_tokens
                req.cost_usd, req.price_band = cost.usd, cost.band
        u = self.usage.setdefault(
            provider,
            {
                "model": model,
                "requests": 0,
                "promptTokens": 0,
                "completionTokens": 0,
                "costUsd": 0.0,
                "ttftMs": [],
            },
        )
        u["model"] = model
        u["requests"] += 1
        u["promptTokens"] += prompt_tokens
        u["completionTokens"] += completion_tokens
        u["costUsd"] = round(u["costUsd"] + cost.usd, 8)
        if ttft > 0:
            u["ttftMs"].append(round(ttft * 1000, 1))
        logger.info(
            "llm_request provider=%s model=%s ttft_ms=%.1f duration_ms=%.1f prompt_tokens=%d "
            "completion_tokens=%d cost_usd=%.8f band=%s",
            provider,
            model,
            ttft * 1000,
            duration * 1000,
            prompt_tokens,
            completion_tokens,
            cost.usd,
            cost.band,
        )
        self.publish_state()

    def on_tts_metrics(self, ttfb: float, duration: float, audio_duration: float) -> None:
        if self.marks is None:
            return
        if ttfb > 0:
            self.marks.tts_ttfb.append(ttfb)
        self.marks.tts_gen_s += max(duration, 0.0)
        self.marks.tts_audio_s += max(audio_duration, 0.0)

    def _finish_turn(self, *, final: bool) -> None:
        if self.marks is not None and self._marks_turn is not None:
            self._emit(self.marks, None, final=final)
        if final:
            self.marks, self._marks_turn = None, None

    def finish(self) -> None:
        """Call end: write the last turn with its complete TTS numbers."""
        self._finish_turn(final=True)

    def _emit(self, marks: TurnMarks, omar_text: str | None, *, final: bool) -> None:
        if self._marks_turn is None:
            self._turn_no += 1
            self._marks_turn = self._turn_no
        previous = self.book.rows.get(self._marks_turn, {})
        row = {
            "turn": self._marks_turn,
            "stage": self._marks_stage,
            "at": previous.get("at", time.time()),
            "lead_text": marks.lead_text[:200],
            "omar_text": plain(
                omar_text if omar_text is not None else previous.get("omar_text", "")
            )[:300],
            **breakdown(marks),
        }
        self._put_row(row, final=final)
        if final:
            logger.info(
                "turn %d %s total=%s detect=%s commit=%s tool=%s llm=%s guard=%s tts=%s "
                "tts_ttfb=%s tts_rtf=%s unexplained=%s src=%s scripted=%s interrupted=%s",
                row["turn"],
                row["stage"],
                row["totalMs"],
                row["turnDetectMs"],
                row["commitMs"],
                row["toolMs"],
                row["llmMs"],
                row["guardMs"],
                row["ttsMs"],
                row["ttsTtfbMs"],
                row["ttsRealtimeFactor"],
                row["unexplainedMs"],
                row["userEndSource"],
                row["scripted"],
                row["interrupted"],
            )

    def _put_row(self, row: dict[str, Any], *, final: bool) -> None:
        self.book.put(row, final=final)
        self.bus.send(TOPIC_LATENCY, {"turn": row, "summary": self.book.summary()})

    def _guard(self, sentence: str) -> str:
        """Check the words; pass the allowed emotion tags on to TTS."""
        state = self.controller.state
        violation = check_sentence(
            plain(sentence),
            booking_confirmed=state.booking_confirmed,
            lang=state.language,
            female=state.config.agent_female,
        )
        if violation is None:
            return render(sentence, self.tts_engine)
        logger.warning("guard %s replaced: %r", violation.rule, sentence)
        self.guard_hits.append({"rule": violation.rule, "said": sentence, "at": str(time.time())})
        self.publish_state()
        return violation.replacement


# -- session wiring ---------------------------------------------------------


def _last_user_id(ctx: llm.ChatContext) -> str | None:
    return next(
        (
            i.id
            for i in reversed(ctx.items)
            if getattr(i, "type", None) == "message" and i.role == "user"
        ),
        None,
    )


def _frame_dbfs(frame: rtc.AudioFrame) -> float:
    samples = np.frombuffer(frame.data, dtype=np.int16)
    if samples.size == 0:
        return -120.0
    rms = float(np.sqrt(np.mean(np.square(samples.astype(np.float32))))) / 32768.0
    return 20 * math.log10(max(rms, 1e-6))


def _groq_llm(settings: Settings) -> llm.LLM:
    groq_extra: dict[str, Any] = {}
    if settings.llm_reasoning_effort:
        # Groq's switch for Qwen thinking; "none" turns it off
        groq_extra["extra_body"] = {"reasoning_effort": settings.llm_reasoning_effort}
    return openai.LLM(
        model=settings.groq_model,
        base_url=settings.groq_base_url,
        api_key=_require("GROQ_API_KEY"),
        temperature=0.6,
        # Groq's free tier allows 1,000 output tokens a minute and rejects a request whose
        # possible output is larger. The agent speaks 2-3 sentences, so a small cap is enough.
        max_completion_tokens=settings.llm_max_tokens,
        _strict_tool_schema=False,
        **groq_extra,
    )


def _deepseek_llm(settings: Settings, api_key: str | None = None) -> llm.LLM:
    # deepseek-flash (V4.1-Flash) thinks by default; disable it to keep replies low-latency.
    # with_deepseek() cannot pass extra_body, so build the LLM directly.
    return openai.LLM(
        model=settings.deepseek_model,
        api_key=api_key or settings.deepseek_api_key,
        base_url="https://api.deepseek.com/v1",
        temperature=0.6,
        max_completion_tokens=settings.llm_max_tokens,
        extra_body={"thinking": {"type": "disabled"}},
    )


CEREBRAS_QWEN = "qwen-3.8-27b"


def _cerebras_llm(settings: Settings, qwen: bool = False) -> llm.LLM:
    if qwen:
        # the same Qwen as on Groq, thinking off
        return openai.LLM(
            model=CEREBRAS_QWEN,
            api_key=settings.cerebras_api_key,
            base_url="https://api.cerebras.ai/v1",
            temperature=0.6,
            max_completion_tokens=settings.llm_max_tokens,
            _strict_tool_schema=False,
            reasoning_effort="none",
        )
    return openai.LLM(
        model=settings.cerebras_model,
        api_key=settings.cerebras_api_key,
        base_url="https://api.cerebras.ai/v1",
        temperature=0.6,
        max_completion_tokens=settings.cerebras_max_tokens,
        _strict_tool_schema=False,
        **(
            {"reasoning_effort": settings.cerebras_reasoning_effort}
            if settings.cerebras_reasoning_effort
            else {}
        ),
    )


def resolve_provider(settings: Settings, choice: str | None, has_key: bool = False) -> str:
    """The provider for this call: the page's choice, else LLM_PROVIDER.

    DeepSeek needs a key: from DEEPSEEK_API_KEY, or pasted on the page for this call
    (has_key). Without one, the call uses Groq.
    """
    provider = choice if choice in LLM_PROVIDERS else settings.llm_provider
    if provider in ("deepseek", "auto") and not (settings.deepseek_api_key or has_key):
        if provider == "deepseek":
            logger.warning("DeepSeek chosen but no DeepSeek key yet; using Groq")
        return "groq"
    if provider.startswith("cerebras") and not settings.cerebras_api_key:
        logger.warning("Cerebras chosen but no CEREBRAS_API_KEY; using Groq")
        return "groq"
    return provider


def llm_label(settings: Settings, provider: str) -> str:
    return {
        "groq": f"Groq · {settings.groq_model}",
        "deepseek": f"DeepSeek · {settings.deepseek_model}",
        "cerebras": f"Cerebras · {settings.cerebras_model}",
        "cerebras-qwen": f"Cerebras · {CEREBRAS_QWEN}",
        "auto": f"DeepSeek · {settings.deepseek_model}, Groq on errors",
    }[provider]


def build_llm(
    settings: Settings, provider: str | None = None, deepseek_key: str | None = None
) -> llm.LLM:
    """The LLM for one call. provider: "groq", "deepseek" or "auto" (see resolve_provider)."""
    provider = resolve_provider(settings, provider, has_key=bool(deepseek_key))
    if provider == "deepseek":
        return _deepseek_llm(settings, deepseek_key)
    if provider in ("cerebras", "cerebras-qwen"):
        return _cerebras_llm(settings, qwen=provider == "cerebras-qwen")
    if provider == "auto":
        # DeepSeek is the main LLM (paid, no per-minute limit); Groq's free tier is the backup
        return llm.FallbackAdapter(
            [_deepseek_llm(settings, deepseek_key), _groq_llm(settings)], attempt_timeout=4.0
        )
    return _groq_llm(settings)


_DEEPSEEK_KEY = re.compile(r"sk-[A-Za-z0-9_-]{16,}")


async def check_deepseek_key(key: str) -> str | None:
    """None if DeepSeek accepts the key, else a short reason. Never logs the key."""
    if not _DEEPSEEK_KEY.fullmatch(key):
        return "That does not look like a DeepSeek key (it starts with sk-)."
    try:
        async with (
            aiohttp.ClientSession() as http,
            http.get(
                "https://api.deepseek.com/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=aiohttp.ClientTimeout(total=6),
            ) as r,
        ):
            if r.status == 200:
                return None
            if r.status in (401, 403):
                return "DeepSeek rejected this key."
            return f"DeepSeek answered {r.status}; the key was not checked."
    except (TimeoutError, aiohttp.ClientError):
        return "Could not reach DeepSeek to check the key."


DEEPGRAM = "deepgram"  # TTS_ENGINE=deepgram: turn-taking tests without ElevenLabs credits
DEEPGRAM_TEST_VOICE = "aura-2-thalia-en"

_ELEVEN_CHECKS: dict[str, tuple[float, int]] = {}  # voice id -> (checked at, HTTP status)
_ELEVEN_CHECK_TTL = 600.0


async def eleven_voice_status(settings: Settings, voice_id: str) -> int:
    """Can this key speak with this voice? One tiny request ("Hi.", ~0.7 s), cached 10 min.

    Needed because a blocked voice fails silently in the plugin ("no audio frames"):
    the free plan answers 402 for library voices. Network trouble counts as OK (200),
    so a slow check never blocks a call.
    """
    cached = _ELEVEN_CHECKS.get(voice_id)
    if cached and time.time() - cached[0] < _ELEVEN_CHECK_TTL:
        return cached[1]
    try:
        async with (
            aiohttp.ClientSession() as http,
            http.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                params={"output_format": "pcm_16000"},
                headers={"xi-api-key": settings.eleven_api_key},
                json={"text": "Hi.", "model_id": "eleven_flash_v2_5"},
                timeout=aiohttp.ClientTimeout(total=4),
            ) as resp,
        ):
            status = resp.status
    except (TimeoutError, aiohttp.ClientError):
        return 200
    _ELEVEN_CHECKS[voice_id] = (time.time(), status)
    return status


async def usable_voice(settings: Settings, voice_id: str | None) -> tuple[str | None, str]:
    """The voice to use and a note for the page. A blocked ElevenLabs voice -> free voice."""
    voice_id = voice_id or default_voice(settings)
    if tts_engine(settings, voice_id) != ELEVENLABS or voice_id == ELEVEN_FREE_VOICE:
        return voice_id, ""
    status = await eleven_voice_status(settings, voice_id or "")
    if status == 200:
        return voice_id, ""
    logger.warning("ElevenLabs refused voice %s (HTTP %s): using Jessica (free)", voice_id, status)
    why = "needs a paid ElevenLabs plan" if status == 402 else f"ElevenLabs HTTP {status}"
    return ELEVEN_FREE_VOICE, f" ({why}: Jessica speaks instead)"


def default_voice(settings: Settings) -> str | None:
    """The voice when the page sends none: ELEVEN_VOICE_ID (with a key), else Cartesia's."""
    if settings.eleven_api_key and settings.eleven_voice:
        return settings.eleven_voice
    return settings.cartesia_voice or None


def tts_engine(settings: Settings, voice_id: str | None) -> str:
    """The engine that will speak: ElevenLabs only for its voices and with a key."""
    if settings.tts_override == DEEPGRAM:
        return DEEPGRAM
    voice_id = voice_id or default_voice(settings)
    if settings.eleven_api_key and (
        engine_of(voice_id) == ELEVENLABS or voice_id in (settings.eleven_voice, ELEVEN_FREE_VOICE)
    ):
        return ELEVENLABS
    return CARTESIA


class WarmElevenLabsTTS(elevenlabs.TTS):
    """ElevenLabs TTS that opens its websocket when the session starts (LiveKit calls
    prewarm()), so the greeting does not wait for the TLS and websocket handshake.
    The plugin keeps the socket for 300 s of silence, so later lines reuse it."""

    def prewarm(self) -> None:
        async def _open() -> None:
            try:
                await self._current_connection()
            except Exception:  # the first line will connect and report the error
                logger.debug("ElevenLabs prewarm failed", exc_info=True)

        task = asyncio.ensure_future(_open())
        self._prewarm_task = task  # keep a reference until it is done


def build_tts(settings: Settings, voice_id: str | None) -> Any:
    voice_id = voice_id or default_voice(settings)
    if settings.tts_override == DEEPGRAM:
        return deepgram.TTS(model=DEEPGRAM_TEST_VOICE)
    if tts_engine(settings, voice_id) == ELEVENLABS:
        return WarmElevenLabsTTS(
            api_key=settings.eleven_api_key,
            voice_id=voice_id,
            model=settings.eleven_model,
            # text-to-dialogue models (v3, v4) read only stability
            voice_settings=elevenlabs.VoiceSettings(
                stability=settings.eleven_stability, similarity_boost=0.75
            ),
        )
    if engine_of(voice_id) == ELEVENLABS:
        logger.warning("ElevenLabs voice chosen but ELEVEN_API_KEY is not set: using Cartesia")
        voice_id = None
    voice = (voice_id if engine_of(voice_id) == CARTESIA else None) or settings.cartesia_voice
    return cartesia.TTS(
        model=settings.cartesia_model,
        base_url=settings.cartesia_base_url,
        emotion=settings.tts_emotion or None,
        speed=settings.tts_speed if settings.tts_speed != 1.0 else None,
        **({"voice": voice} if voice else {}),
    )


def build_session(
    settings: Settings, vad: Any, provider: str | None = None, voice_id: str | None = None
) -> AgentSession:
    if settings.turn_mode == "flux":
        # Flux decides the turn end from the audio and the words.
        stt: Any = deepgram.STTv2(
            model="flux-general-multi" if settings.hindi else "flux-general-en",
            **({"language_hint": ["en", "hi"]} if settings.hindi else {}),
            eot_threshold=settings.flux_eot_threshold,
            # EagerEndOfTurn -> LiveKit starts a preemptive draft before the final turn end
            **(
                {
                    "eager_eot_threshold": min(
                        settings.flux_eager_eot_threshold, settings.flux_eot_threshold
                    )
                }
                if settings.flux_eager_eot_threshold > 0
                else {}
            ),
            **({"base_url": settings.deepgram_stt_url} if settings.deepgram_stt_url else {}),
        )
        turn_detection: Any = "stt"
    else:
        # LiveKit's turn detector decides. It listens to the audio (v1-mini runs on the
        # worker, free; v1 runs in LiveKit Cloud). Flux only gives text at its own turn
        # end, so this mode uses Nova-3, which streams text while the Lead speaks.
        from livekit.agents.inference import TurnDetector

        stt = deepgram.STT(
            model="nova-3",
            language="multi" if settings.hindi else "en",
            **({"base_url": settings.deepgram_stt_url} if settings.deepgram_stt_url else {}),
        )
        turn_detection = TurnDetector(version=settings.livekit_turn_model)

    model = build_llm(settings, provider)

    tts = build_tts(settings, voice_id)

    return AgentSession(
        stt=stt,
        llm=model,
        tts=tts,
        vad=vad,
        aec_warmup_duration=settings.aec_warmup_s,
        turn_handling={
            "turn_detection": turn_detection,
            "endpointing": {"min_delay": settings.min_delay},
            # a cough, "mm" or a one-word backchannel must not stop Omar mid-sentence
            "interruption": {
                "min_words": settings.interrupt_min_words,
                "min_duration": settings.interrupt_min_duration,
            },
            # off by default on the free tier: drafting while the Lead speaks costs extra
            # Groq tokens. The drafts change no call state (see on_user_turn_completed).
            "preemptive_generation": {
                "enabled": settings.preemptive_generation,
                "preemptive_tts": settings.preemptive_tts,
            },
        },
    )


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is not set. Put it in .env (see .env.example).")
    return value


def parse_stability(metadata: str | None) -> float | None:
    """ElevenLabs stability from the page's slider (0..1), if valid."""
    try:
        data = json.loads(metadata or "")
    except json.JSONDecodeError:
        return None
    value = data.get("stability") if isinstance(data, dict) else None
    if isinstance(value, int | float) and not isinstance(value, bool) and 0 <= value <= 1:
        return float(value)
    return None


def parse_hindi_choice(metadata: str | None) -> bool | None:
    """True when the page chose English + Hindi for this call ("lang": "hi"), False for
    English only ("lang": "en"), None when it did not say."""
    try:
        data = json.loads(metadata or "")
    except json.JSONDecodeError:
        return None
    lang = data.get("lang") if isinstance(data, dict) else None
    return {"hi": True, "en": False}.get(lang) if isinstance(lang, str) else None


def parse_turn_choice(metadata: str | None) -> str | None:
    """The turn-taking preset the page (or the turn test) chose, if any."""
    try:
        data = json.loads(metadata or "")
    except json.JSONDecodeError:
        return None
    choice = data.get("turn") if isinstance(data, dict) else None
    return choice if choice in TURN_PRESETS else None


def parse_voice_choice(metadata: str | None) -> tuple[str, str, str, str] | None:
    """The voice the page chose (id, label, agent name, engine), if it is an allowed one."""
    try:
        data = json.loads(metadata or "")
    except json.JSONDecodeError:
        return None
    return voice_choice(data.get("voice")) if isinstance(data, dict) else None


def parse_llm_choice(metadata: str | None) -> str | None:
    """The LLM the page chose for this call ("groq", "deepseek", "auto"), if any."""
    try:
        data = json.loads(metadata or "")
    except json.JSONDecodeError:
        return None
    choice = data.get("llm") if isinstance(data, dict) else None
    return choice if choice in LLM_PROVIDERS else None


def parse_lead(metadata: str | None) -> Lead:
    if not metadata:
        return DEFAULT_LEAD
    try:
        data = json.loads(metadata)
    except json.JSONDecodeError:
        logger.warning("job metadata is not JSON; using the default Lead")
        return DEFAULT_LEAD
    return Lead.from_dict(data.get("lead", data)) if isinstance(data, dict) else DEFAULT_LEAD


def wire_latency(session: AgentSession, agent: OmarAgent) -> None:
    """Feed LiveKit events into the agent's turn timing."""

    @session.on("conversation_item_added")
    def _on_item(ev: Any) -> None:
        item = ev.item
        if getattr(item, "type", None) == "message" and item.role == "assistant":
            agent.on_assistant_message(item)

    @session.on("metrics_collected")
    def _on_metrics(ev: Any) -> None:
        m = ev.metrics
        if getattr(m, "type", None) == "tts_metrics" and not getattr(m, "cancelled", False):
            agent.on_tts_metrics(m.ttfb, m.duration, m.audio_duration)
        elif getattr(m, "type", None) == "llm_metrics":
            meta = getattr(m, "metadata", None)
            agent.on_llm_metrics(
                getattr(meta, "model_provider", None) or "",
                getattr(meta, "model_name", None) or "",
                float(getattr(m, "ttft", 0.0) or 0.0),
                float(getattr(m, "duration", 0.0) or 0.0),
                int(getattr(m, "prompt_tokens", 0) or 0),
                int(getattr(m, "completion_tokens", 0) or 0),
            )


# -- worker ------------------------------------------------------------------

SETTINGS = Settings()
server = AgentServer()


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name=SETTINGS.agent_name)
async def entrypoint(ctx: JobContext) -> None:
    settings = Settings()
    lead = parse_lead(ctx.job.metadata)
    calendar = FakeCalendar(
        taken_rate=settings.calendar_taken_rate, error_rate=settings.calendar_error_rate
    )
    voice = parse_voice_choice(ctx.job.metadata)  # (id, label, agent name, engine) or None
    hindi = parse_hindi_choice(ctx.job.metadata)
    if hindi is not None:
        settings = dataclasses.replace(settings, hindi=hindi)
    agent_name = voice[2] if voice else settings.agent_persona
    controller = CallController(
        lead=lead,
        calendar=calendar,
        config=CallConfig(
            agent_name=agent_name, agent_female=agent_name != MALE_NAME, hindi=settings.hindi
        ),
    )
    bus = Bus(ctx.room)
    book = LatencyBook(
        log_path=settings.latency_log_dir
        / f"{time.strftime('%Y%m%d-%H%M%S')}-{ctx.room.name}.jsonl"
    )

    settings = with_turn_preset(settings, parse_turn_choice(ctx.job.metadata))
    stability = parse_stability(ctx.job.metadata)
    if stability is not None:
        settings = dataclasses.replace(settings, eleven_stability=stability)
    provider = resolve_provider(settings, parse_llm_choice(ctx.job.metadata))
    voice_id, voice_note = await usable_voice(settings, voice[0] if voice else None)
    session = build_session(
        settings,
        ctx.proc.userdata.get("vad") or silero.VAD.load(),
        provider,
        voice_id=voice_id,
    )
    agent = OmarAgent(controller, settings, bus, book)
    agent.turn_hook = True
    agent.llm_label = llm_label(settings, provider)
    agent.voice_label = (voice[1] if voice else "default voice") + voice_note
    agent.tts_engine = tts_engine(settings, voice_id)
    if agent.tts_engine == ELEVENLABS:
        agent.voice_label += f" · stability {settings.eleven_stability:.2f}"
    if voice and voice[3] != agent.tts_engine:
        agent.voice_label += " (no ElevenLabs key: default Cartesia voice)"
    choice = parse_llm_choice(ctx.job.metadata)

    async def set_deepseek_key(data: rtc.RpcInvocationData) -> str:
        """The page sends a pasted DeepSeek key after Nimra joins. Used for this call only;
        it is not stored and never logged."""
        try:
            key = str(json.loads(data.payload or "{}").get("key", "")).strip()
        except json.JSONDecodeError:
            key = ""
        problem = await check_deepseek_key(key)
        if problem:
            logger.info("deepseek key from the page refused: %s", problem)
            return json.dumps({"ok": False, "error": problem})
        wanted = resolve_provider(settings, choice, has_key=True)
        if wanted not in ("deepseek", "auto"):
            return json.dumps(
                {"ok": True, "llm": agent.llm_label, "note": "Groq chosen; key not used."}
            )
        agent.update_options(llm=build_llm(settings, wanted, deepseek_key=key))
        agent.llm_label = llm_label(settings, wanted)
        agent.publish_state()
        logger.info("llm switched for this call: %s (key from the page)", agent.llm_label)
        return json.dumps({"ok": True, "llm": agent.llm_label})

    wire_latency(session, agent)

    @ctx.room.on("participant_disconnected")
    def _left(_: rtc.RemoteParticipant) -> None:
        if controller.stage is not Stage.ENDED:
            controller.line_dropped()
            logger.info("Lead left the room: %s", controller.state.outcome)

    async def _on_shutdown() -> None:
        agent.finish()
        logger.info(
            "call over: %s | %s | latency %s",
            controller.state.status.value,
            controller.state.outcome,
            json.dumps(book.summary()["overall"]["totalMs"]),
        )

    ctx.add_shutdown_callback(_on_shutdown)

    logger.info(
        "starting call: lead=%s turn_mode=%s eager=%.2f preemptive=%s min_delay=%.2fs llm=%s",
        lead.name,
        settings.turn_mode,
        settings.flux_eager_eot_threshold,
        settings.preemptive_generation,
        settings.min_delay,
        llm_label(settings, provider),
    )
    # join the room first: the greeting and the first state message need a connected room
    await ctx.connect()
    ctx.room.local_participant.register_rpc_method("omar.set_deepseek_key", set_deepseek_key)
    await session.start(agent=agent, room=ctx.room)


def main() -> None:
    needs_keys = any(cmd in sys.argv[1:2] for cmd in ("dev", "start", "console", "connect"))
    missing = missing_keys() if needs_keys else []
    if sys.argv[1:2] == ["start"]:
        # LiveKit Cloud agent hosting supplies the LIVEKIT_* values itself
        missing = [k for k in missing if not k.startswith("LIVEKIT_")]
    if missing:
        raise SystemExit(
            "Missing keys in .env: "
            + ", ".join(missing)
            + "\nCopy .env.example to .env and fill them in."
        )
    cli.run_app(server)


if __name__ == "__main__":
    main()
