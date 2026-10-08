"""The glue between the LLM and the call state machine. No LiveKit imports.

The LLM reports what the Lead did. The controller asks `core/` for the next
stage, runs any calendar work, and returns what must happen next: a scripted
line for code to speak, an instruction for the LLM, or both.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from omar_core import (
    STAGE_LABEL,
    CallConfig,
    CallState,
    Effects,
    Event,
    IllegalEvent,
    Lead,
    Stage,
    allowed,
    transition,
)
from omar_core import start as start_call
from omar_core.fake_calendar import FakeCalendar
from omar_core.lang import detect
from omar_core.prompts import event_menu, instructions


@dataclass
class Step:
    """One applied event, for the UI timeline and the logs."""

    at: float
    event: str
    detail: str | None
    by: str  # "llm" or "code"
    stage_after: str


@dataclass
class Reply:
    """What the voice layer does after a report.

    say:     code speaks this line word for word.
    guide:   instruction for the LLM's next reply.
    ended:   the call is over after `say` plays.
    error:   the report was rejected (wrong stage); the text goes back to the LLM.
    """

    say: str | None = None
    guide: str | None = None
    ended: bool = False
    error: str | None = None

    def tool_output(self) -> str | None:
        """Text returned to the LLM as the tool result. None = the LLM stays silent."""
        if self.error:
            return self.error
        if self.say and self.guide:
            return f'Say this first, word for word: "{self.say}" Then: {self.guide}'
        if self.guide:
            return self.guide
        return None


@dataclass
class CallController:
    lead: Lead
    calendar: FakeCalendar = field(default_factory=FakeCalendar)
    config: CallConfig = field(default_factory=CallConfig)
    state: CallState = field(init=False)
    steps: list[Step] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.state = start_call(self.lead, self.config)

    # -- queries ----------------------------------------------------------

    @property
    def stage(self) -> Stage:
        return self.state.stage

    def instructions(self) -> str:
        return instructions(self.state)

    def event_menu(self) -> list[tuple[str, str]]:
        return event_menu(self.state)

    def snapshot(self) -> dict[str, Any]:
        s = self.state
        return {
            "stage": s.stage.value,
            "stageLabel": STAGE_LABEL[s.stage],
            "status": s.status.value,
            "outcome": s.outcome,
            "ended": s.ended,
            "rapportTurns": s.rapport_turns,
            "minRapportTurns": s.config.min_rapport_turns,
            "objections": s.objections,
            "maxObjections": s.config.max_objections,
            "offered": s.offered,
            "chosen": s.chosen,
            "bookingConfirmed": s.booking_confirmed,
            "aiDisclosed": s.ai_disclosed,
            "language": s.language,
            "opening": {
                "companyAndPurpose": s.opening.company_and_purpose,
                "recordingNotice": s.opening.recording_notice,
                "askedToContinue": s.opening.asked_to_continue,
            },
            "steps": [step.__dict__ for step in self.steps[-12:]],
        }

    # -- commands ---------------------------------------------------------

    def start(self) -> Reply:
        """The Lead picked up (in the demo: joined the room)."""
        return self._apply(Event.ANSWERED, None, by="code")

    def lead_turn(self) -> bool:
        """Count one engaged Lead turn in INFO (rapport). True if the stage changed."""
        if self.state.stage is not Stage.INFO:
            return False
        before = self.state.stage
        self._apply(Event.LEAD_TURN, None, by="code")
        return self.state.stage is not before

    def report(self, event_name: str, detail: str | None = None, *, by: str = "llm") -> Reply:
        """The LLM (or the code's quick check) reports what the Lead did."""
        try:
            event = Event(event_name)
        except ValueError:
            return Reply(error=f"Unknown event '{event_name}'. Just reply to the Lead.")
        menu = [name for name, _ in self.event_menu()]
        if event.value not in menu:
            return Reply(
                error=(
                    f"'{event_name}' does not apply in stage {self.state.stage.value}. "
                    "Just reply to the Lead."
                )
            )
        return self._apply(event, detail, by=by)

    def code_event(self, event: Event) -> Reply:
        """Apply an event that code detected (quick events). System events are allowed."""
        if event not in allowed(self.state):
            return Reply(error=f"'{event.value}' does not apply in stage {self.state.stage.value}.")
        return self._apply(event, None, by="code")

    def note_language(self, text: str) -> bool:
        """Follow the Lead's language (Hindi calls only). True if it changed."""
        if not self.state.config.hindi:
            return False
        lang = detect(text)
        if lang is None or lang == self.state.language:
            return False
        self.state.language = lang
        return True

    def line_dropped(self) -> None:
        if Event.LINE_DROPS in allowed(self.state):
            self._apply(Event.LINE_DROPS, None, by="code")

    # -- internals --------------------------------------------------------

    def _apply(self, event: Event, detail: str | None, *, by: str) -> Reply:
        try:
            self.state, fx = transition(self.state, event, detail)
        except IllegalEvent as e:
            return Reply(error=f"{e}. Just reply to the Lead.")
        self._log(event, detail, by)
        fx = self._run_actions(fx)
        return Reply(say=fx.say, guide=fx.guide, ended=self.state.ended)

    def _run_actions(self, fx: Effects) -> Effects:
        """Run calendar work and feed the result back as system events."""
        for _ in range(4):  # a slot can be taken, which asks for new slots once more
            if fx.action == "find_slots":
                slots = self.calendar.free_slots(fx.action_arg or "")
                fx = self._chain(fx, Event.SLOTS_FOUND, "|".join(slots))
            elif fx.action == "book":
                result = self.calendar.book(fx.action_arg or "")
                event = {
                    "confirmed": Event.CALENDAR_CONFIRMS,
                    "taken": Event.CALENDAR_SLOT_TAKEN,
                }.get(result, Event.CALENDAR_ERROR)
                fx = self._chain(fx, event, None)
            else:
                break
        return fx

    def _chain(self, fx: Effects, event: Event, detail: str | None) -> Effects:
        self.state, nxt = transition(self.state, event, detail)
        self._log(event, detail, "code")
        return Effects(say=fx.say, guide=fx.guide).merge(nxt)

    def _log(self, event: Event, detail: str | None, by: str) -> None:
        self.steps.append(Step(time.time(), event.value, detail, by, self.state.stage.value))
