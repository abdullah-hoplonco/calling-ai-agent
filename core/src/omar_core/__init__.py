"""Omar's pure domain: call state machine, guards, prompts, knowledge, fake calendar."""

from .config import CallConfig
from .lead import DEFAULT_LEAD, Lead
from .state_machine import (
    STAGE_LABEL,
    CallState,
    Effects,
    Event,
    IllegalEvent,
    LeadStatus,
    Stage,
    allowed,
    reportable,
    start,
    transition,
)

__all__ = [
    "DEFAULT_LEAD",
    "STAGE_LABEL",
    "CallConfig",
    "CallState",
    "Effects",
    "Event",
    "IllegalEvent",
    "Lead",
    "LeadStatus",
    "Stage",
    "allowed",
    "reportable",
    "start",
    "transition",
]
