"""All settings come from environment variables (see `.env.example`)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env")

TurnMode = Literal["flux", "livekit"]
LLM_PROVIDERS = ("groq", "deepseek", "cerebras", "cerebras-qwen", "auto")

REQUIRED_KEYS = (
    "LIVEKIT_URL",
    "LIVEKIT_API_KEY",
    "LIVEKIT_API_SECRET",
    "DEEPGRAM_API_KEY",
    "GROQ_API_KEY",
    "CARTESIA_API_KEY",
)


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _float(name: str, default: float) -> float:
    raw = _env(name)
    return float(raw) if raw else default


@dataclass(frozen=True)
class Settings:
    agent_name: str = field(default_factory=lambda: _env("OMAR_AGENT_NAME", "omar"))

    # turn detection: one decider at a time (see docs/demo-plan.md, "Turn detection")
    turn_mode: TurnMode = field(
        default_factory=lambda: "livekit" if _env("TURN_MODE", "flux") == "livekit" else "flux"
    )
    endpointing_min_delay: float = field(
        default_factory=lambda: _float("ENDPOINTING_MIN_DELAY", -1)
    )
    # LiveKit turn detector version when TURN_MODE=livekit: "v1-mini" (local, free) or "v1" (cloud)
    livekit_turn_model: str = field(
        default_factory=lambda: "v1" if _env("LIVEKIT_TURN_MODEL", "v1-mini") == "v1" else "v1-mini"
    )
    # 0.7 (Flux default). 0.8 was tried to cut fewer Leads off, but measured waits of up to 2.8 s.
    flux_eot_threshold: float = field(default_factory=lambda: _float("FLUX_EOT_THRESHOLD", 0.7))
    # Flux "probably done" signal (EagerEndOfTurn), 0.3-0.9; 0 = off. With preemptive
    # generation on, the LLM starts at this signal instead of at the final end of turn.
    flux_eager_eot_threshold: float = field(
        default_factory=lambda: _float("FLUX_EAGER_EOT_THRESHOLD", 0.0)
    )
    # The Lead may speak Hindi (or mix it with English), and the agent answers in it.
    # STT becomes Flux multilingual (hints en, hi). The page can choose per call.
    hindi: bool = field(default_factory=lambda: _env("HINDI", "off").lower() in ("on", "1", "true"))
    interrupt_min_words: int = field(default_factory=lambda: int(_float("INTERRUPT_MIN_WORDS", 2)))
    # LiveKit ignores the Lead's audio for this long after Omar starts a line (echo guard).
    # The default 3 s dropped quick answers like "yes, speaking"; a headset needs little.
    aec_warmup_s: float = field(default_factory=lambda: _float("AEC_WARMUP_S", 1.0))
    interrupt_min_duration: float = field(
        default_factory=lambda: _float("INTERRUPT_MIN_DURATION", 0.6)
    )

    deepgram_stt_url: str = field(default_factory=lambda: _env("DEEPGRAM_STT_URL"))

    groq_model: str = field(default_factory=lambda: _env("GROQ_MODEL", "qwen/qwen3.8-27b"))
    groq_base_url: str = field(
        default_factory=lambda: _env("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    )
    # Groq's switch to turn Qwen thinking off. Empty = do not send it.
    llm_reasoning_effort: str = field(default_factory=lambda: _env("LLM_REASONING_EFFORT", "none"))
    llm_max_tokens: int = field(default_factory=lambda: int(_float("LLM_MAX_TOKENS", 120)))
    # Which LLM speaks: "groq" (Qwen on Groq), "deepseek" (DeepSeek API), or "auto"
    # (DeepSeek first, Groq when DeepSeek fails). The page can choose per call.
    llm_provider: str = field(
        default_factory=lambda: (
            _env("LLM_PROVIDER", "auto").lower()
            if _env("LLM_PROVIDER", "auto").lower() in LLM_PROVIDERS
            else "auto"
        )
    )
    deepseek_api_key: str = field(default_factory=lambda: _env("DEEPSEEK_API_KEY"))
    deepseek_model: str = field(default_factory=lambda: _env("DEEPSEEK_MODEL", "deepseek-flash"))
    # Cerebras (OpenAI-compatible). gpt-oss always reasons; "low" keeps that short.
    cerebras_api_key: str = field(default_factory=lambda: _env("CEREBRAS_API_KEY"))
    cerebras_model: str = field(default_factory=lambda: _env("CEREBRAS_MODEL", "gpt-oss-120b"))
    cerebras_reasoning_effort: str = field(
        default_factory=lambda: _env("CEREBRAS_REASONING_EFFORT", "low")
    )
    # reasoning tokens count against the cap, so it is larger than LLM_MAX_TOKENS
    cerebras_max_tokens: int = field(
        default_factory=lambda: int(_float("CEREBRAS_MAX_TOKENS", 600))
    )

    cartesia_model: str = field(default_factory=lambda: _env("CARTESIA_MODEL", "sonic-3"))
    # the persona the Lead hears, and its Cartesia voice (OMAR_VOICE_ID is the old name)
    agent_persona: str = field(default_factory=lambda: _env("AGENT_NAME", "Nimra"))
    cartesia_voice: str = field(
        default_factory=lambda: _env("AGENT_VOICE_ID") or _env("OMAR_VOICE_ID")
    )
    # The voice's base mood for every line (Cartesia generation_config). The LLM's inline
    # emotion tags change it per sentence. Empty = Cartesia's neutral read.
    tts_emotion: str = field(default_factory=lambda: _env("TTS_EMOTION", "content"))
    # 1.0 = Cartesia's normal pace. Sonic-3 accepts 0.6 to 1.5.
    tts_speed: float = field(default_factory=lambda: _float("TTS_SPEED", 1.05))
    # mood for code's scripted lines (opening, goodbyes), which have no LLM tags
    script_emotion: str = field(default_factory=lambda: _env("SCRIPT_EMOTION", "happy"))
    # ElevenLabs (used when the chosen voice is an ElevenLabs voice). eleven_v4_turbo is
    # ElevenLabs' expressive real-time model and reads [mood] tags.
    eleven_api_key: str = field(default_factory=lambda: _env("ELEVEN_API_KEY"))
    # the ElevenLabs voice used when the page sends no voice
    eleven_voice: str = field(default_factory=lambda: _env("ELEVEN_VOICE_ID"))
    eleven_model: str = field(default_factory=lambda: _env("ELEVEN_MODEL", "eleven_v4_turbo"))
    # lower = more emotion, higher = steadier. ElevenLabs: 0.3-0.5 is lively; 0.0 can wander.
    eleven_stability: float = field(default_factory=lambda: _float("ELEVEN_STABILITY", 0.3))
    cartesia_base_url: str = field(
        default_factory=lambda: _env("CARTESIA_BASE_URL", "https://api.cartesia.ai")
    )

    preemptive_generation: bool = field(
        default_factory=lambda: _env("PREEMPTIVE_GENERATION", "off").lower() in ("1", "on", "true")
    )
    # also start the voice before the turn is final (costs TTS characters for dropped drafts)
    preemptive_tts: bool = field(
        default_factory=lambda: _env("PREEMPTIVE_TTS", "off").lower() in ("1", "on", "true")
    )
    # "deepgram" = every line in a Deepgram Aura voice (turn-taking tests; no ElevenLabs credits)
    tts_override: str = field(default_factory=lambda: _env("TTS_ENGINE").lower())
    output_guard: bool = field(
        default_factory=lambda: _env("OUTPUT_GUARD", "on").lower() not in ("0", "off", "false")
    )

    calendar_taken_rate: float = field(
        default_factory=lambda: _float("FAKE_CALENDAR_TAKEN_RATE", 0.0)
    )
    calendar_error_rate: float = field(
        default_factory=lambda: _float("FAKE_CALENDAR_ERROR_RATE", 0.0)
    )

    knowledge_path: str | None = field(default_factory=lambda: _env("KNOWLEDGE_PATH") or None)
    latency_log_dir: Path = field(
        default_factory=lambda: Path(_env("LATENCY_LOG_DIR") or REPO_ROOT / "voice" / "logs")
    )

    @property
    def min_delay(self) -> float:
        """Extra silence to wait after the turn-end signal. Flux already waited for its own
        end-of-turn decision, so in Flux mode this is 0 (0.2 s measured as pure added delay)."""
        if self.endpointing_min_delay >= 0:
            return self.endpointing_min_delay
        return 0.0 if self.turn_mode == "flux" else 0.3


# Turn-taking setups the page (or the turn test) may choose per call
TURN_PRESETS: dict[str, dict[str, object]] = {
    "flux": {"turn_mode": "flux", "flux_eager_eot_threshold": 0.0, "preemptive_generation": False},
    "flux-eager": {
        "turn_mode": "flux",
        "flux_eager_eot_threshold": 0.4,
        "preemptive_generation": True,
    },
    "livekit-v1": {
        "turn_mode": "livekit",
        "livekit_turn_model": "v1",
        "preemptive_generation": True,
    },
}


def with_turn_preset(settings: Settings, name: object) -> Settings:
    """Settings with one of TURN_PRESETS applied; unknown names change nothing."""
    preset = TURN_PRESETS.get(name) if isinstance(name, str) else None
    return replace(settings, **preset) if preset else settings  # type: ignore[arg-type]


def missing_keys() -> list[str]:
    return [k for k in REQUIRED_KEYS if not _env(k)]
