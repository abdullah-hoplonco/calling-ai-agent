"""Voices the page may choose for the agent. Only these IDs are accepted.

Each voice belongs to one TTS engine; choosing the voice chooses the engine.
"""

from __future__ import annotations

FEMALE_NAME = "Nimra"
MALE_NAME = "Hamza"
CARTESIA = "cartesia"
ELEVENLABS = "elevenlabs"
# ElevenLabs premade voice (Jessica: playful, bright, warm female). Premade voices work on
# the free plan; library voices (like Maya) need a paid plan. Used when the chosen one fails.
ELEVEN_FREE_VOICE = "cgSgspJ2msm6clMCkdW9"

# id -> (label, agent name the Lead hears, engine)
VOICES: dict[str, tuple[str, str, str]] = {
    # ElevenLabs. Jessica is premade: works on the free plan (the default).
    ELEVEN_FREE_VOICE: ("Jessica · playful, warm female (ElevenLabs)", FEMALE_NAME, ELEVENLABS),
    # chosen by the owner after listening; library voices need a paid plan
    "4O1sYUnmtThcBoSBrri7": (
        "Maya · Indian female (ElevenLabs, paid plan)",
        FEMALE_NAME,
        ELEVENLABS,
    ),
    "56AoDkrOh6qfVPDXZ7Pt": (
        "Cassidy · American female (ElevenLabs, paid plan)",
        FEMALE_NAME,
        ELEVENLABS,
    ),
    "1qEiC6qsybMkmnNdVMbK": (
        "Monika · Indian female (ElevenLabs, paid plan)",
        FEMALE_NAME,
        ELEVENLABS,
    ),
    # Cartesia: the first four are its "emotive" voices (follow emotion tags most strongly)
    "6ccbfb76-1fc6-48f7-b71d-91ac6298247b": ("Tessa · warm female, emotive", FEMALE_NAME, CARTESIA),
    "cbaf8084-f009-4838-a096-07ee2e6612b1": (
        "Maya · easygoing female, emotive",
        FEMALE_NAME,
        CARTESIA,
    ),
    "0834f3df-e650-4766-a20c-5a93a43aa6e3": ("Leo · warm male, emotive", MALE_NAME, CARTESIA),
    "c961b81c-a935-4c17-bfb3-ba2239de8c2f": ("Kyle · friendly male, emotive", MALE_NAME, CARTESIA),
    "f8f5f1b2-f02d-4d8e-a40d-fd850a487b3d": (
        "Kiara · Indian female, upbeat",
        FEMALE_NAME,
        CARTESIA,
    ),
    "db408a93-859c-4a0a-b6a2-220c074cc90d": (
        "Hana · neutral female, easygoing",
        FEMALE_NAME,
        CARTESIA,
    ),
    "8d8ce8c9-44a4-46c4-b10f-9a927b99a853": (
        "Connie · neutral female, cheery",
        FEMALE_NAME,
        CARTESIA,
    ),
    "f6141af3-5f94-418c-80ed-a45d450e7e2e": ("Priya · Indian female", FEMALE_NAME, CARTESIA),
    "1259b7e3-cb8a-43df-9446-30971a46b8b0": ("Devansh · Indian male", MALE_NAME, CARTESIA),
    "62ae83ad-4f6a-430b-af41-a9bede9286ca": ("Gemma · British female", FEMALE_NAME, CARTESIA),
    "ef191366-f52f-447a-a398-ed8c0f2943a1": ("Archie · British male", MALE_NAME, CARTESIA),
}


def voice_choice(voice_id: str | None) -> tuple[str, str, str, str] | None:
    """(id, label, agent name, engine) for an allowed voice, else None."""
    if voice_id in VOICES:
        label, name, engine = VOICES[voice_id]
        return voice_id, label, name, engine
    return None


def engine_of(voice_id: str | None) -> str:
    choice = voice_choice(voice_id)
    return choice[3] if choice else CARTESIA
