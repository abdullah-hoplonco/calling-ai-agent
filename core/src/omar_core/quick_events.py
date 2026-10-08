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

# Hindi (Devanagari, as Deepgram writes it, plus common Roman spellings). Matched with
# letter lookarounds: Python's \b breaks inside Devanagari words at vowel signs.


def _hi(pattern: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?<![\u0900-\u0963\u0966-\u097F\w])(?:{pattern})(?![\u0900-\u0963\u0966-\u097F\w])",
        re.IGNORECASE,
    )


_YES_HI_WORDS = (
    r"हाँ|हां|हाँजी|जी(?!\s*नहीं)|जी\s+हाँ|बोल\s+रहा|बोल\s+रही|बोलिए|बोलिये|बताइए|बताइये|"
    r"ठीक\s+है|बिल्कुल|बिलकुल|ज़रूर|जरूर|मैं\s+ही\s+(?:हूँ|हूं)|चलेगा|हाँ\s+बोलो|"
    r"haan|haanji|bilkul|zaroor|theek\s+hai|thik\s+hai|bol\s+raha|bol\s+rahi|boliye|bataiye"
)
_YES_HI = _hi(_YES_HI_WORDS)
_NEG_HI = _hi(r"नहीं|नही|ना|मत|nahi|nahin|mat")
_WRONG_HI = _hi(
    r"(?:गलत|ग़लत|रॉन्ग|galat)\s*(?:नंबर|number)|"
    r"(?:यहाँ|यहां)\s+(?:कोई|ऐसा\s+कोई)\s+.{0,20}\s*नहीं|मैं\s+वो\s+नहीं"
)
_NOT_INTERESTED_HI = _hi(
    r"(?:इंटरेस्ट|interest|interested|दिलचस्पी)\s*नहीं|(?:कॉल|call|फ़ोन|फोन)\s*(?:मत|ना)\s*(?:करें|करो|कीजिए|करना)|"
    r"नंबर\s+हटा"
)
_BUSY_HI = _hi(
    r"बिज़ी|बिजी|अभी\s+(?:नहीं|टाइम\s+नहीं|बात\s+नहीं)|बाद\s+में|ड्राइव\s+कर|गाड़ी\s+चला|"
    r"(?:मीटिंग|meeting)\s+में|(?:टाइम|time)\s+नहीं"
)
_NO_RECORDING_HI = _hi(r"(?:रिकॉर्ड|record|रिकॉर्डिंग|recording)\s*(?:मत|नहीं|ना)")
_QUESTION_HI = _hi(r"कौन|क्या|क्यों|कैसे|कहाँ|कहां|किसने|kaun|kya|kyun|kaise")
_LEADING_YES_HI = re.compile(
    rf"^[\W_]*(?:{_YES_HI_WORDS})(?![\u0900-\u0963\u0966-\u097F\w])", re.IGNORECASE
)


def _any(text: str, *patterns: re.Pattern[str]) -> bool:
    return any(p.search(text) for p in patterns)


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
    wrong = _any(words, _WRONG, _WRONG_HI)
    leading_yes = _any(words, _LEADING_YES, _LEADING_YES_HI) and not wrong

    candidates: list[Event] = []
    if short and _any(words, _NOT_INTERESTED, _NOT_INTERESTED_HI):
        candidates.append(Event.NOT_INTERESTED)
    elif short and _any(words, _NO_RECORDING, _NO_RECORDING_HI):
        candidates.append(Event.OBJECTS_RECORDING)
    elif wrong:
        candidates.append(Event.WRONG_PERSON)
    elif short and _any(words, _BUSY, _BUSY_HI):
        candidates.append(Event.NOT_NOW)
    elif leading_yes or (
        short
        and _any(words, _YES, _YES_HI)
        and not _any(words, _NEG, _NEG_HI)
        and not _any(words, _QUESTION, _QUESTION_HI)
    ):
        candidates.append(
            Event.CONFIRM_IDENTITY if state.stage is Stage.IDENTITY else Event.GOOD_TIME
        )
    elif state.stage is Stage.IDENTITY and state.identity_asks < MAX_IDENTITY_ASKS:
        candidates.append(Event.IDENTITY_UNCLEAR)

    ok = allowed(state)
    return next((e for e in candidates if e in ok), None)
