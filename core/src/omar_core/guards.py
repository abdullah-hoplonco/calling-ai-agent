"""Output guards: rules checked on every sentence Omar is about to say.

A prompt makes good behaviour likely; these checks make it hold (ADR 0001).
Each rule finds a forbidden sentence and gives the safe line that replaces it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .state_machine import NO_BUDGET_LINE, NO_TIMELINE_LINE

_NUM = r"(?:\d[\d,.]*|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|a few|a couple of)"

_MONEY = re.compile(
    r"(?:\b(?:aed|usd|dhs?|dirhams?|dollars?|pounds?|gbp|eur|euros?)\b"
    r"|[$£€]\s?\d"
    r"|\b\d[\d,.]*\s?(?:k|grand)\b"
    r"|\b\d[\d,.]*\s?(?:thousand|hundred|million)\b)",
    re.IGNORECASE,
)
_TIMELINE = re.compile(
    rf"\b{_NUM}\s*(?:-|to)?\s*(?:{_NUM}\s*)?(?:days?|weeks?|months?)\b", re.IGNORECASE
)
_BOOKED = re.compile(
    r"\b(?:you'?re|you are|you'?ve been|it'?s|that'?s|we'?re|all)\s+(?:now\s+|all\s+)?"
    r"(?:booked|confirmed|locked in|scheduled)\b"
    r"|\bi'?ve\s+(?:booked|scheduled|confirmed)\b"
    r"|\bbooking is confirmed\b",
    re.IGNORECASE,
)
_DENIES_AI = re.compile(
    r"\b(?:i'?m|i am)\s+(?:a\s+)?(?:real\s+)?(?:human|person)\b"
    r"|\b(?:i'?m|i am)\s+not\s+(?:an?\s+)?(?:ai|bot|robot|machine)\b"
    r"|\bnot\s+a\s+(?:bot|robot)\b",
    re.IGNORECASE,
)
_HUMAN_WORDING = re.compile(r"\ba human\b|\brefer you\b|\breal person\b", re.IGNORECASE)

AI_LINE = "To be honest with you, I'm Hoplon's AI assistant."
MANAGER_LINE = "I can connect you with my manager."
BOOKING_HOLD_LINE = "Let me just confirm that on the calendar."


@dataclass(frozen=True)
class Violation:
    rule: str
    replacement: str


def check_sentence(text: str, *, booking_confirmed: bool) -> Violation | None:
    """Return the first rule this sentence breaks, or None if it is safe."""
    if _DENIES_AI.search(text):
        return Violation("never_deny_ai", AI_LINE)
    if _MONEY.search(text):
        return Violation("no_budget", NO_BUDGET_LINE)
    if _TIMELINE.search(text):
        return Violation("no_timeline", NO_TIMELINE_LINE)
    if not booking_confirmed and _BOOKED.search(text):
        return Violation("no_booked_before_calendar", BOOKING_HOLD_LINE)
    if _HUMAN_WORDING.search(text):
        return Violation("say_my_manager", MANAGER_LINE)
    return None


_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def split_complete(buffer: str) -> tuple[list[str], str]:
    """Split a text buffer into complete sentences and the unfinished rest."""
    parts = _SENTENCE_END.split(buffer)
    if len(parts) == 1:
        return [], buffer
    return [p for p in parts[:-1] if p.strip()], parts[-1]
