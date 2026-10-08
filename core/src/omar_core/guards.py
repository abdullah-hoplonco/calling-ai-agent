"""Output guards: rules checked on every sentence Omar is about to say.

A prompt makes good behaviour likely; these checks make it hold (ADR 0001).
Each rule finds a forbidden sentence and gives the safe line that replaces it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .lang import LINES_HI, Lang, gendered
from .state_machine import NO_BUDGET_LINE, NO_TIMELINE_LINE

# Hindi words are matched with letter lookarounds, not \b: Python's \b breaks inside
# Devanagari words at vowel signs.
_B = r"(?<![\u0900-\u0963\u0966-\u097F])"
_E = r"(?![\u0900-\u0963\u0966-\u097F])"


def _hi(pattern: str) -> re.Pattern[str]:
    return re.compile(f"{_B}(?:{pattern}){_E}", re.IGNORECASE)


_NUM = r"(?:\d[\d,.]*|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|a few|a couple of)"

_MONEY = re.compile(
    r"(?:\b(?:aed|usd|dhs?|dirhams?|dollars?|pounds?|gbp|eur|euros?)\b"
    r"|[$£€]\s?\d"
    r"|\b\d[\d,.]*\s?(?:k|grand)\b"
    r"|\b\d[\d,.]*\s?(?:thousand|hundred|million)\b"
    r"|\b(?:rupees?|rs\.?|inr|lakhs?|crores?|hazaa?r)\b)",
    re.IGNORECASE,
)
_MONEY_HI = _hi(r"रुपये|रुपए|रुपया|रुपयों|डॉलर|दिरहम|हज़ार|हजार|लाख|करोड़|करोड")
_NUM_HI = (
    r"(?:[0-9०-९]+|एक|दो|तीन|चार|पाँच|पांच|छह|छः|सात|आठ|नौ|दस|बारह|कुछ|one|two|three|four|five|six)"
)
_UNIT_HI = r"(?:दिन|दिनों|हफ़्ते|हफ्ते|हफ़्ता|हफ्ता|हफ़्तों|हफ्तों|सप्ताह|महीने|महीना|महीनों|days?|weeks?|months?)"
_TIMELINE_HI = _hi(rf"{_NUM_HI}(?:\s*(?:-|से|या|to)\s*{_NUM_HI})?\s*{_UNIT_HI}")
_BOOKED_HI = _hi(
    r"(?:बुक|book|booked|कन्फर्म|confirm|confirmed|शेड्यूल|schedule|fix|पक्की|पक्का)\s*"
    r"(?:हो\s*(?:गई|गया|गयी|चुकी|चुका|गए)|कर\s*(?:दी|दिया|ली|लिया|दिए))"
)
_DENIES_AI_HI = _hi(
    r"मैं\s+(?:एक\s+)?(?:असली\s+)?(?:इंसान|human|person|आदमी|औरत)\s+(?:हूँ|हूं)"
    r"|मैं\s+(?:कोई\s+|एक\s+)?(?:AI|ai|bot|बॉट|robot|रोबोट|मशीन|machine)\s+नहीं"
)
_HUMAN_WORDING_HI = _hi(r"किसी\s+इंसान|असली\s+इंसान|इंसान\s+से|refer\s+कर")
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


def check_sentence(
    text: str, *, booking_confirmed: bool, lang: Lang = "en", female: bool = True
) -> Violation | None:
    """Return the first rule this sentence breaks, or None if it is safe.

    English and Hindi rules both run on every sentence; `lang` picks the language of
    the safe line that replaces it.
    """

    def safe(key: str, english: str) -> str:
        return gendered(LINES_HI[key], female) if lang == "hi" else english

    if _DENIES_AI.search(text) or _DENIES_AI_HI.search(text):
        return Violation("never_deny_ai", safe("ai", AI_LINE))
    if _MONEY.search(text) or _MONEY_HI.search(text):
        return Violation("no_budget", safe("no_budget", NO_BUDGET_LINE))
    if _TIMELINE.search(text) or _TIMELINE_HI.search(text):
        return Violation("no_timeline", safe("no_timeline", NO_TIMELINE_LINE))
    if not booking_confirmed and (_BOOKED.search(text) or _BOOKED_HI.search(text)):
        return Violation("no_booked_before_calendar", safe("booking_hold", BOOKING_HOLD_LINE))
    if _HUMAN_WORDING.search(text) or _HUMAN_WORDING_HI.search(text):
        return Violation("say_my_manager", safe("manager", MANAGER_LINE))
    return None


_SENTENCE_END = re.compile(r"(?<=[.!?।॥])\s+")  # । ends a Hindi sentence


def split_complete(buffer: str) -> tuple[list[str], str]:
    """Split a text buffer into complete sentences and the unfinished rest."""
    parts = _SENTENCE_END.split(buffer)
    if len(parts) == 1:
        return [], buffer
    return [p for p in parts[:-1] if p.strip()], parts[-1]
