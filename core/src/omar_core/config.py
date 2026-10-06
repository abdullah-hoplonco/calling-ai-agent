"""Call rules that are expected to change. Kept as data, not code (ticket 08)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CallConfig:
    min_rapport_turns: int = 2
    max_objections: int = 2
    max_slot_rounds: int = 2
    max_callbacks: int = 2
    window_text: str = "between 10 and 5:30"
