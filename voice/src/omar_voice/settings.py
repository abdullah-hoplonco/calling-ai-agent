"""All settings come from environment variables (see `.env.example`)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env")

TurnMode = Literal["flux", "livekit"]

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
    # 0.8: Flux must be surer that the Lead finished (0.7 cut Leads off mid-sentence)
    flux_eot_threshold: float = field(default_factory=lambda: _float("FLUX_EOT_THRESHOLD", 0.8))
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
    deepseek_api_key: str = field(default_factory=lambda: _env("DEEPSEEK_API_KEY"))
    deepseek_model: str = field(default_factory=lambda: _env("DEEPSEEK_MODEL", "deepseek-chat"))

    cartesia_model: str = field(default_factory=lambda: _env("CARTESIA_MODEL", "sonic-3"))
    cartesia_voice: str = field(default_factory=lambda: _env("OMAR_VOICE_ID"))
    cartesia_base_url: str = field(
        default_factory=lambda: _env("CARTESIA_BASE_URL", "https://api.cartesia.ai")
    )

    preemptive_generation: bool = field(
        default_factory=lambda: _env("PREEMPTIVE_GENERATION", "off").lower() in ("1", "on", "true")
    )
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
        """Silence to wait after the turn-end signal. Flux already waits, so default low."""
        if self.endpointing_min_delay >= 0:
            return self.endpointing_min_delay
        return 0.2 if self.turn_mode == "flux" else 0.3


def missing_keys() -> list[str]:
    return [k for k in REQUIRED_KEYS if not _env(k)]
