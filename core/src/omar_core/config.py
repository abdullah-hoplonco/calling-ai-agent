"""Call rules that are expected to change. Kept as data, not code (ticket 08)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CallConfig:
    agent_name: str = "Nimra"  # the persona the Lead hears
    agent_female: bool = True  # Hindi verbs agree with the speaker (Nimra: female, Hamza: male)
    hindi: bool = False  # the Lead may speak Hindi; the agent then answers in Hindi
    min_rapport_turns: int = 4  # get to know the Lead before any intent question
    max_objections: int = 2
    max_slot_rounds: int = 2
    max_callbacks: int = 2
    window_text: str = "between 10 and 5:30"
