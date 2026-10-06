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
import json
import logging
import math
import os
import re
import sys
import time
from collections.abc import AsyncIterable
from typing import Any

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
from livekit.plugins import cartesia, deepgram, openai, silero

from omar_core import DEFAULT_LEAD, Lead, Stage
from omar_core.fake_calendar import FakeCalendar
from omar_core.guards import check_sentence, split_complete
from omar_core.knowledge import TOPICS, lookup
from omar_core.quick_events import quick_event

from .controller import CallController, Reply
from .latency import LatencyBook
from .settings import Settings, missing_keys
from .timing import AudioClock, LlmRequest, TurnMarks, VoiceEnd, breakdown

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
        self.turn_stage: str = controller.stage.value
        self.tool_turn = False
        self.scripted_texts: list[str] = []
        self.guard_hits: list[dict[str, str]] = []
        self._counted_user_id: str | None = None
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
        handle = session.say(reply.say, allow_interruptions=not reply.ended)
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
            "model": self.settings.groq_model,
            "guard": self.settings.output_guard,
            "preemptive": self.settings.preemptive_generation,
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
        start = await self._on_new_lead_message(ctx)
        if start == "spoken":
            return  # code answered this turn with a scripted line; no LLM call
        if start == "moved":
            tools = self._stage_tools()  # the stage moved: offer this stage's events
        ctx.truncate(max_items=MAX_HISTORY_ITEMS)
        req = LlmRequest(start=time.time())
        if self.marks is not None:
            self.marks.requests.append(req)
        stream = Agent.default.llm_node(self, ctx, tools, model_settings)
        try:
            if not self.settings.output_guard:
                async for chunk in stream:
                    self._note_chunk(req, chunk)
                    if isinstance(chunk, str) or (
                        isinstance(chunk, llm.ChatChunk) and chunk.delta and chunk.delta.content
                    ):
                        self._note_first_out()
                    yield chunk
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
                        self._note_first_out()
                        yield self._guard(sentence) + " "
            buf = _THINK.sub("", buf).replace("<think>", "").strip()
            if buf:
                self._note_first_out()
                yield self._guard(buf)
        finally:
            req.end = time.time()

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
        self.tool_turn = False
        self.turn_stage = self.controller.stage.value
        text = (last.text_content or "").strip()
        self._start_turn(text, dict(getattr(last, "metrics", None) or {}))
        if not text:
            return None

        quick = quick_event(self.controller.state, text)
        if quick is not None:
            reply = self.controller.code_event(quick)
            logger.info("quick %s -> %s", quick.value, self.controller.stage.value)
            await self._refresh()
            if reply.say and not reply.guide:
                if self.marks is not None:
                    self.marks.scripted = True
                self._say(reply, self.session)
                return "spoken"
            self._use_stage_in(ctx, reply.guide)
            return "moved"

        if not self.controller.lead_turn():
            return None
        await self._refresh()
        self._use_stage_in(ctx, None)
        return "moved"

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

    def _note_first_out(self) -> None:
        if self.marks is not None and self.marks.first_out is None:
            self.marks.first_out = time.time()

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
                "omar_text": (item.text_content or "")[:300],
                "totalMs": None,
                "scripted": (item.text_content or "").strip()
                in (s.strip() for s in self.scripted_texts),
                "interrupted": bool(getattr(item, "interrupted", False)),
            },
            final=True,
        )

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
            "omar_text": (omar_text if omar_text is not None else previous.get("omar_text", ""))[
                :300
            ],
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
        violation = check_sentence(
            sentence, booking_confirmed=self.controller.state.booking_confirmed
        )
        if violation is None:
            return sentence
        logger.warning("guard %s replaced: %r", violation.rule, sentence)
        self.guard_hits.append({"rule": violation.rule, "said": sentence, "at": str(time.time())})
        self.publish_state()
        return violation.replacement


# -- session wiring ---------------------------------------------------------


def _frame_dbfs(frame: rtc.AudioFrame) -> float:
    samples = np.frombuffer(frame.data, dtype=np.int16)
    if samples.size == 0:
        return -120.0
    rms = float(np.sqrt(np.mean(np.square(samples.astype(np.float32))))) / 32768.0
    return 20 * math.log10(max(rms, 1e-6))


def build_llm(settings: Settings) -> llm.LLM:
    """Groq + Qwen. With DEEPSEEK_API_KEY set, DeepSeek takes over on errors (D4)."""
    groq_extra: dict[str, Any] = {}
    if settings.llm_reasoning_effort:
        # Groq's switch for Qwen thinking; "none" turns it off
        groq_extra["extra_body"] = {"reasoning_effort": settings.llm_reasoning_effort}
    groq = openai.LLM(
        model=settings.groq_model,
        base_url=settings.groq_base_url,
        api_key=_require("GROQ_API_KEY"),
        temperature=0.6,
        # Groq's free tier allows 1,000 output tokens a minute and rejects a request whose
        # possible output is larger. Omar speaks 2-3 sentences, so a small cap is enough.
        max_completion_tokens=settings.llm_max_tokens,
        _strict_tool_schema=False,
        **groq_extra,
    )
    model: llm.LLM = groq
    if settings.deepseek_api_key:
        backup = openai.LLM.with_deepseek(model=settings.deepseek_model, temperature=0.6)
        model = llm.FallbackAdapter([groq, backup], attempt_timeout=4.0)

    return model


def build_session(settings: Settings, vad: Any) -> AgentSession:
    if settings.turn_mode == "flux":
        # Flux decides the turn end from the audio and the words.
        stt: Any = deepgram.STTv2(
            model="flux-general-en",
            eot_threshold=settings.flux_eot_threshold,
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
            language="en",
            **({"base_url": settings.deepgram_stt_url} if settings.deepgram_stt_url else {}),
        )
        turn_detection = TurnDetector(version=settings.livekit_turn_model)

    model = build_llm(settings)

    tts = cartesia.TTS(
        model=settings.cartesia_model,
        base_url=settings.cartesia_base_url,
        **({"voice": settings.cartesia_voice} if settings.cartesia_voice else {}),
    )

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
            # off on the free tier: drafting while the Lead speaks doubles Groq tokens
            "preemptive_generation": {"enabled": settings.preemptive_generation},
        },
    )


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is not set. Put it in .env (see .env.example).")
    return value


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
    controller = CallController(lead=lead, calendar=calendar)
    bus = Bus(ctx.room)
    book = LatencyBook(
        log_path=settings.latency_log_dir
        / f"{time.strftime('%Y%m%d-%H%M%S')}-{ctx.room.name}.jsonl"
    )

    session = build_session(settings, ctx.proc.userdata.get("vad") or silero.VAD.load())
    agent = OmarAgent(controller, settings, bus, book)
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
        "starting call: lead=%s turn_mode=%s min_delay=%.2fs model=%s",
        lead.name,
        settings.turn_mode,
        settings.min_delay,
        settings.groq_model,
    )
    # join the room first: the greeting and the first state message need a connected room
    await ctx.connect()
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
