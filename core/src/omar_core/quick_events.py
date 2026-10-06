"""Code-detected Lead events for the scripted stages (identity check and legal opening).

A small LLM does not always call the report tool, and then the call stays stuck in
IDENTITY and the legal opening is never said. These stages need only yes, no, busy
or "not interested", so code decides them from the words, before the LLM runs.
Anything unclear returns None and the LLM handles it as usual.
"""

from __future__ import annotations

import re

from .state_machine import CallState, Event, Stage, allowed

_NEG = re.compile(r"\b(no|nope|not|don'?t|wrong|isn'?t|never)\b", re.IGNORECASE)
_YES = re.compile(
    r"\b(yes|yeah|yea|yep|yup|ya|sure|speaking|correct|right|okay|ok|go ahead|"
    r"of course|absolutely|fine|sounds good|that'?s me|it'?s me|this is (?:he|she|him|her|me)|"
    r"i am|i'?m listening)\b",
    re.IGNORECASE,
)
_WRONG = re.compile(
    r"\bwrong (?:number|person)\b|\bno one (?:here )?(?:by|with) that name\b|"
    r"\b(?:this is|i'?m) not (?:him|her|them)\b|\byou have the wrong\b",
    re.IGNORECASE,
)
_NOT_INTERESTED = re.compile(
    r"\bnot interested\b|\bdon'?t call\b|\bstop calling\b|\bremove (?:me|my number)\b",
    re.IGNORECASE,
)
_BUSY = re.compile(
    r"\bbusy\b|\bcall (?:me )?(?:back|later)\b|\bnot (?:a good time|now|right now)\b|"
    r"\bdriving\b|\bin a meeting\b|\bcan'?t talk\b",
    re.IGNORECASE,
)
_NO_RECORDING = re.compile(
    r"\b(?:don'?t|do not|no) (?:want to be )?record|\bnot be recorded\b|\bno recording\b",
    re.IGNORECASE,
)
_QUESTION = re.compile(r"\?|\b(who|what|why|which|how)\b", re.IGNORECASE)

MAX_WORDS = 10  # longer replies carry more than yes/no: leave them to the LLM
MAX_IDENTITY_ASKS = 2  # after two unclear replies, the LLM takes over the identity check
_LEADING_YES = re.compile(r"^\W*(?:" + _YES.pattern + r")", re.IGNORECASE)


def quick_event(state: CallState, text: str) -> Event | None:
    """The event the Lead's words clearly show in IDENTITY or OPENING, else None.

    IDENTITY is owned by code: a reply that starts with yes confirms the Lead even
    when a question follows ("Yes. Who is this?"), because the legal opening that
    follows answers it. An unclear reply gets a scripted re-ask (IDENTITY_UNCLEAR).
    """
    if state.stage not in (Stage.IDENTITY, Stage.OPENING):
        return None
    words = text.strip()
    if not words:
        return None
    short = len(words.split()) <= MAX_WORDS
    leading_yes = bool(_LEADING_YES.search(words)) and not _WRONG.search(words)

    candidates: list[Event] = []
    if short and _NOT_INTERESTED.search(words):
        candidates.append(Event.NOT_INTERESTED)
    elif short and _NO_RECORDING.search(words):
        candidates.append(Event.OBJECTS_RECORDING)
    elif _WRONG.search(words):
        candidates.append(Event.WRONG_PERSON)
    elif short and _BUSY.search(words):
        candidates.append(Event.NOT_NOW)
    elif leading_yes or (
        short and _YES.search(words) and not _NEG.search(words) and not _QUESTION.search(words)
    ):
        candidates.append(
            Event.CONFIRM_IDENTITY if state.stage is Stage.IDENTITY else Event.GOOD_TIME
        )
    elif state.stage is Stage.IDENTITY and state.identity_asks < MAX_IDENTITY_ASKS:
        candidates.append(Event.IDENTITY_UNCLEAR)

    ok = allowed(state)
    return next((e for e in candidates if e in ok), None)
