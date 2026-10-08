"""Emotion tags for the voice: the LLM marks how a sentence should sound, the TTS acts it.

The LLM writes one short, engine-neutral form:  [excited] Oh, that's brilliant! [laughs]
Code turns it into what each voice engine reads:

    engine       emotion                         laugh
    cartesia     <emotion value="excited"/>      [laughter]
    elevenlabs   [excited]                       [laughs]

Short tags also cost fewer LLM tokens before the first word (about 3 instead of 8).
Only the moods below are allowed; any other tag is removed before TTS, and all tags
are removed from text shown to people.
"""

from __future__ import annotations

import re

from .lang import fix_brand

# moods the LLM may use: they suit a friendly call and both engines act them well
EMOTIONS = (
    "happy",
    "excited",
    "curious",
    "warm",
    "calm",
    "surprised",
    "grateful",
    "sympathetic",
    "apologetic",
)
LAUGH = "laughs"

# Cartesia Sonic-3 has a fixed emotion list; map our words onto it
_CARTESIA_EMOTION = {"warm": "content"}

_EMOTION_TAG = re.compile(r"""<\s*emotion\s+value\s*=\s*["']?([a-zA-Z/_-]+)["']?\s*/?\s*>""")
_ANY_TAG = re.compile(r"<[^<>]*>")
_BRACKET = re.compile(r"\[\s*([^\[\]]*?)\s*\]")
_LAUGH_WORDS = {"laughs", "laugh", "laughter", "laughing", "chuckles", "chuckle"}
_SPACES = re.compile(r"\s{2,}")


def _cue(word: str, engine: str) -> str:
    word = word.lower().strip()
    if word in _LAUGH_WORDS:
        return "[laughter]" if engine == "cartesia" else f"[{LAUGH}]"
    if word == "content":
        word = "warm"
    if word not in EMOTIONS:
        return ""
    if engine == "cartesia":
        return f'<emotion value="{_CARTESIA_EMOTION.get(word, word)}"/>'
    return f"[{word}]"


def render(text: str, engine: str) -> str:
    """Text for one TTS engine ("cartesia" | "elevenlabs"): allowed cues only, in its syntax.
    Any other engine reads no cues: it gets the words only."""
    text = fix_brand(text)  # the company name always reaches TTS in English letters
    if engine not in ("cartesia", "elevenlabs"):
        return plain(text)
    out = _EMOTION_TAG.sub(lambda m: f"[{m.group(1)}]", text)  # accept Cartesia-style too
    out = _ANY_TAG.sub("", out)
    out = _BRACKET.sub(lambda m: _cue(m.group(1), engine) + " ", out)
    return _SPACES.sub(" ", out).strip()


def plain(text: str) -> str:
    """The words only: no tags, no cues. For guards, transcripts and logs."""
    out = _ANY_TAG.sub("", text)
    out = _BRACKET.sub("", out)
    return _SPACES.sub(" ", out).strip()
