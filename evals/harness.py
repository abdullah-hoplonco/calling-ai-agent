"""Run Omar in text mode: typed Lead lines in, Omar's text out. No audio, no TTS credits."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from livekit.agents import AgentSession, llm

from omar_core import DEFAULT_LEAD, Lead
from omar_core.fake_calendar import DUBAI, FakeCalendar
from omar_voice.agent import OmarAgent
from omar_voice.controller import CallController
from omar_voice.settings import Settings

NOW = datetime(2026, 10, 5, 9, 0, tzinfo=DUBAI)  # a Monday morning in Dubai


@dataclass
class RecordingBus:
    messages: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def send(self, topic: str, payload: dict[str, Any]) -> None:
        self.messages.append((topic, payload))


@dataclass
class Transcript:
    controller: CallController
    agent: OmarAgent
    omar: list[str]

    @property
    def text(self) -> str:
        return " ".join(self.omar)


async def converse(
    model: llm.LLM,
    lead_lines: list[str],
    *,
    lead: Lead = DEFAULT_LEAD,
    taken_rate: float = 0.0,
    turn_pause_s: float = 0.0,
) -> Transcript:
    controller = CallController(
        lead=lead, calendar=FakeCalendar(now=NOW, busy_ratio=0.3, taken_rate=taken_rate)
    )
    agent = OmarAgent(controller, Settings(), RecordingBus())  # type: ignore[arg-type]
    omar: list[str] = []
    async with AgentSession(llm=model) as session:
        await session.start(agent)
        for i, line in enumerate(lead_lines):
            if controller.state.ended:
                break
            if i and turn_pause_s:
                await asyncio.sleep(turn_pause_s)  # stay under the provider's per-minute limits
            result = await session.run(user_input=line)
            for ev in result.events:
                item = getattr(ev, "item", None)
                if getattr(item, "type", None) == "message" and item.role == "assistant":
                    omar.append(item.text_content or "")
        # scripted lines spoken by code (opening, goodbyes) are in the session history
        omar = [
            i.text_content or ""
            for i in session.history.items
            if getattr(i, "type", None) == "message" and i.role == "assistant"
        ]
    return Transcript(controller, agent, omar)
