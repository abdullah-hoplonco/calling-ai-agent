"""The Connected Call state machine (ADR 0001).

Code owns the call: this module decides the stage, counts objections and rapport
turns, and says which lines are scripted. The LLM only writes words inside the
current stage and reports what the Lead did.

Pure: no I/O, no vendor imports. Ported from the `CallFlow` module in
`.scratch/calling-agent/prototypes/PROTOTYPE-call-flow.html` (ticket 08).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

from .config import CallConfig
from .lang import LINES_HI, Lang, gendered
from .lead import Lead


class Stage(StrEnum):
    DIALING = "DIALING"
    IDENTITY = "IDENTITY"
    OPENING = "OPENING"
    INFO = "INFO"
    INTENT = "INTENT"
    ARABIC_CHECK = "ARABIC_CHECK"
    BOOKING_PREF = "BOOKING_PREF"
    BOOKING_OFFER = "BOOKING_OFFER"
    EMAIL_CONFIRM = "EMAIL_CONFIRM"
    BOOKING_PENDING = "BOOKING_PENDING"
    CALLBACK = "CALLBACK"
    ENDED = "ENDED"


STAGE_LABEL: dict[Stage, str] = {
    Stage.DIALING: "Dialing",
    Stage.IDENTITY: "Checking it is the right person",
    Stage.OPENING: "Legal opening given, waiting for 'is now a good time?'",
    Stage.INFO: "Giving the information they asked for",
    Stage.INTENT: "Probing Intent to Buy",
    Stage.ARABIC_CHECK: "Checking that English is OK",
    Stage.BOOKING_PREF: "Asking for a time preference",
    Stage.BOOKING_OFFER: "Offering 2 slots",
    Stage.EMAIL_CONFIRM: "Confirming the invite email",
    Stage.BOOKING_PENDING: "Booking on the calendar",
    Stage.CALLBACK: "Agreeing a callback time",
    Stage.ENDED: "Call ended",
}

LIVE_STAGES = frozenset(
    {
        Stage.IDENTITY,
        Stage.OPENING,
        Stage.INFO,
        Stage.INTENT,
        Stage.ARABIC_CHECK,
        Stage.BOOKING_PREF,
        Stage.BOOKING_OFFER,
        Stage.EMAIL_CONFIRM,
        Stage.CALLBACK,
    }
)


class Event(StrEnum):
    # call setup (system)
    ANSWERED = "answered"
    NO_ANSWER = "no_answer"
    VOICEMAIL = "voicemail"
    HANG_UP_SILENT = "hang_up_silent"
    IDENTITY_UNCLEAR = (
        "identity_unclear"  # code: the reply to "is this X?" was not a clear yes or no
    )
    LINE_DROPS = "line_drops"
    # identity and opening
    CONFIRM_IDENTITY = "confirm_identity"
    WRONG_PERSON = "wrong_person"
    GOOD_TIME = "good_time"
    OBJECTS_RECORDING = "objects_recording"
    SPEAKS_ARABIC = "speaks_arabic"
    ENGLISH_OK = "english_ok"
    ENGLISH_NO = "english_no"
    # conversation
    LEAD_TURN = "lead_turn"  # code-generated: one engaged Lead turn in INFO (rapport)
    INTENT_YES = "intent_yes"
    OBJECTION = "objection"
    NO_INTENT = "no_intent"
    ASK_MANAGER = "ask_manager"
    ASK_PRICE = "ask_price"
    ASK_TIMELINE = "ask_timeline"
    ASK_BOT = "ask_bot"
    NOT_NOW = "not_now"
    NOT_INTERESTED = "not_interested"
    HANG_UP_NEGATIVE = "hang_up_negative"
    # callback
    CALLBACK_IN_WINDOW = "callback_in_window"
    CALLBACK_OUTSIDE = "callback_outside"
    # booking
    GIVE_PREFERENCE = "give_preference"
    SLOTS_FOUND = "slots_found"  # system: the calendar returned slots
    ACCEPT_SLOT = "accept_slot"
    NEITHER_SLOT = "neither_slot"
    EMAIL_OK = "email_ok"
    NEW_EMAIL = "new_email"
    CALENDAR_CONFIRMS = "calendar_confirms"
    CALENDAR_SLOT_TAKEN = "calendar_slot_taken"
    CALENDAR_ERROR = "calendar_error"


_TALK = (Stage.OPENING, Stage.INFO, Stage.INTENT)
_BOOKING = (Stage.BOOKING_PREF, Stage.BOOKING_OFFER)

EVENT_STAGES: dict[Event, tuple[Stage, ...]] = {
    Event.ANSWERED: (Stage.DIALING,),
    Event.NO_ANSWER: (Stage.DIALING,),
    Event.VOICEMAIL: (Stage.DIALING,),
    Event.HANG_UP_SILENT: (Stage.IDENTITY,),
    Event.IDENTITY_UNCLEAR: (Stage.IDENTITY,),
    Event.LINE_DROPS: (*_TALK, *_BOOKING, Stage.EMAIL_CONFIRM, Stage.BOOKING_PENDING),
    Event.CONFIRM_IDENTITY: (Stage.IDENTITY,),
    Event.WRONG_PERSON: (Stage.IDENTITY,),
    Event.GOOD_TIME: (Stage.OPENING,),
    Event.OBJECTS_RECORDING: _TALK,
    Event.SPEAKS_ARABIC: (Stage.OPENING, Stage.INFO),
    Event.ENGLISH_OK: (Stage.ARABIC_CHECK,),
    Event.ENGLISH_NO: (Stage.ARABIC_CHECK,),
    Event.LEAD_TURN: (Stage.INFO,),
    Event.INTENT_YES: (Stage.INFO, Stage.INTENT),
    Event.OBJECTION: (Stage.INTENT,),
    Event.NO_INTENT: (Stage.INFO, Stage.INTENT),
    Event.ASK_MANAGER: (Stage.INFO, Stage.INTENT),
    Event.ASK_PRICE: (Stage.INFO, Stage.INTENT, *_BOOKING),
    Event.ASK_TIMELINE: (Stage.INFO, Stage.INTENT, Stage.BOOKING_PREF),
    Event.ASK_BOT: (*_TALK, *_BOOKING, Stage.EMAIL_CONFIRM),
    Event.NOT_NOW: _TALK,
    Event.NOT_INTERESTED: (*_TALK, *_BOOKING),
    Event.HANG_UP_NEGATIVE: (*_TALK, *_BOOKING),
    Event.CALLBACK_IN_WINDOW: (Stage.CALLBACK,),
    Event.CALLBACK_OUTSIDE: (Stage.CALLBACK,),
    Event.GIVE_PREFERENCE: (Stage.BOOKING_PREF,),
    Event.SLOTS_FOUND: (Stage.BOOKING_PREF, Stage.BOOKING_OFFER),
    Event.ACCEPT_SLOT: (Stage.BOOKING_OFFER,),
    Event.NEITHER_SLOT: (Stage.BOOKING_OFFER,),
    Event.EMAIL_OK: (Stage.EMAIL_CONFIRM,),
    Event.NEW_EMAIL: (Stage.EMAIL_CONFIRM,),
    Event.CALENDAR_CONFIRMS: (Stage.BOOKING_PENDING,),
    Event.CALENDAR_SLOT_TAKEN: (Stage.BOOKING_PENDING,),
    Event.CALENDAR_ERROR: (Stage.BOOKING_PENDING,),
}

# Events that only code may raise. The LLM never reports these.
SYSTEM_EVENTS = frozenset(
    {
        Event.ANSWERED,
        Event.NO_ANSWER,
        Event.VOICEMAIL,
        Event.HANG_UP_SILENT,
        Event.IDENTITY_UNCLEAR,
        Event.LINE_DROPS,
        Event.LEAD_TURN,
        Event.SLOTS_FOUND,
        Event.CALENDAR_CONFIRMS,
        Event.CALENDAR_SLOT_TAKEN,
        Event.CALENDAR_ERROR,
    }
)


class LeadStatus(StrEnum):
    CALLING = "Lead (calling)"
    RETRY = "Lead (retry scheduled)"
    CALLBACK = "Lead (callback scheduled)"
    WRONG_NUMBER = "Wrong number"
    QUALIFIED = "Qualified Lead"
    BOOKED = "Qualified Lead (Discovery Call booked)"
    LINK_SENT = "Qualified Lead (booking link sent)"
    PARKED = "Parked Lead"
    PARKED_RECORDING = "Parked Lead (declined recording)"
    PARKED_ARABIC = "Parked Lead (needs Arabic)"
    OPTED_OUT = "Opted-out Lead"


@dataclass
class OpeningChecks:
    """The three legal opening elements, in the order the law fixes."""

    company_and_purpose: bool = False
    recording_notice: bool = False
    asked_to_continue: bool = False


@dataclass
class CallState:
    lead: Lead
    config: CallConfig = field(default_factory=CallConfig)
    stage: Stage = Stage.DIALING
    prev_stage: Stage | None = None
    status: LeadStatus = LeadStatus.CALLING
    outcome: str | None = None
    opening: OpeningChecks = field(default_factory=OpeningChecks)
    rapport_turns: int = 0
    objections: int = 0
    slot_round: int = 0
    offered: list[str] = field(default_factory=list)
    chosen: str | None = None
    email: str | None = None
    callbacks_used: int = 0
    identity_asks: int = 0
    callback_time: str | None = None
    ai_disclosed: bool = False
    booking_confirmed: bool = False
    price_deflections: int = 0
    language: Lang = "en"  # the language the Lead speaks now (changes only with config.hindi)

    @property
    def ended(self) -> bool:
        return self.stage is Stage.ENDED

    @property
    def is_qualified(self) -> bool:
        return self.status in (LeadStatus.QUALIFIED, LeadStatus.BOOKED, LeadStatus.LINK_SENT)


Action = Literal["find_slots", "book"]


@dataclass
class Effects:
    """What the voice layer must do after a transition.

    say:    a scripted line. Code speaks it word for word; the LLM stays silent.
    guide:  an instruction for the LLM's next reply (the LLM chooses the words).
    action: work for the voice layer (calendar), which answers with a system event.
    """

    say: str | None = None
    guide: str | None = None
    action: Action | None = None
    action_arg: str | None = None

    def merge(self, other: Effects) -> Effects:
        joined_say = " ".join(s for s in (self.say, other.say) if s) or None
        joined_guide = " ".join(g for g in (self.guide, other.guide) if g) or None
        return Effects(
            say=joined_say,
            guide=joined_guide,
            action=other.action,
            action_arg=other.action_arg,
        )


class IllegalEvent(ValueError):
    def __init__(self, stage: Stage, event: Event) -> None:
        super().__init__(f"event {event.value!r} is not allowed in stage {stage.value}")
        self.stage = stage
        self.event = event


def allowed(state: CallState) -> list[Event]:
    return [e for e, stages in EVENT_STAGES.items() if state.stage in stages]


def reportable(state: CallState) -> list[Event]:
    """Events the LLM may report in the current stage."""
    return [e for e in allowed(state) if e not in SYSTEM_EVENTS]


NO_BUDGET_LINE = (
    "It really depends on what you need, and we can adjust the budget to fit. "
    "My manager will go through that with you."
)
NO_TIMELINE_LINE = (
    "We can adjust the timeline to your needs. My manager will map that out with you."
)


# Scripted lines, by key. Hindi versions: lang.LINES_HI. {first_name} and {agent} are filled
# for every line; other fields are passed to line().
LINES_EN: dict[str, str] = {
    "identity": "Hi, is this {first_name}?",
    "identity_unclear_1": "This is {agent} from Hoplon and Co. Am I speaking with {first_name}?",
    "identity_unclear_2": "Sorry, just to check, am I speaking with {first_name}?",
    "wrong_number": "Sorry about that, I must have the wrong number. Have a good day!",
    "objects_recording": (
        "Totally understand. I can't continue without recording, but I'll email you "
        "the information instead. Thanks for your time!"
    ),
    "parked_objections": (
        "Completely fair. I'll email you the details, and you can reach us whenever "
        "the timing's right. Thanks, {first_name}!"
    ),
    "no_intent": (
        "No problem. I'll send you some information by email so you have it when "
        "you're ready. Thanks!"
    ),
    "max_callbacks": "No problem. I'll email you the details instead. Thanks!",
    "callback_booked": "Perfect, I'll call you {time}. Speak then!",
    "not_interested": "Understood, I won't call again. Have a great day!",
    "no_slots": (
        "I can't see a good time right now, so I'll email you a link to pick any "
        "time that suits you. Thanks, {first_name}!"
    ),
    "no_slot_agreed": (
        "No worries. I'll email you a link so you can pick any time that suits you. "
        "Thanks, {first_name}!"
    ),
    "lock_in": "One moment while I lock that in.",
    "booked": (
        "You're booked for {slot} with my manager. The invite with the Google Meet "
        "link is on its way. Thanks, {first_name}!"
    ),
    "slot_taken": "Ah, it looks like that time was just taken, sorry about that.",
    "calendar_error": (
        "I'm having trouble with the calendar right now, so I'll email you a link to "
        "pick a time. Sorry about that!"
    ),
    "no_budget": NO_BUDGET_LINE,
    "no_timeline": NO_TIMELINE_LINE,
}


def line(key: str, state: CallState, **fields: str) -> str:
    """A scripted line in the Lead's language: Hindi only when the call allows it."""
    cfg = state.config
    hindi = cfg.hindi and state.language == "hi" and key in LINES_HI
    template = gendered(LINES_HI[key], cfg.agent_female) if hindi else LINES_EN[key]
    return template.format(first_name=state.lead.first_name, agent=cfg.agent_name, **fields)


def opening_line(state: CallState) -> str:
    lead = state.lead
    if state.config.hindi and state.language == "hi":
        old = lead.lead_type == "old" and lead.submitted_month
        key = "opening_old" if old else "opening_new"
        template = gendered(LINES_HI[key], state.config.agent_female)
        return template.format(
            first_name=lead.first_name,
            agent=state.config.agent_name,
            topic=lead.topic_phrase,
            month=lead.submitted_month or "",
        )
    if state.lead.lead_type == "old" and lead.submitted_month:
        why = (
            f"You reached out to us back in {lead.submitted_month} about {lead.topic_phrase}, "
            "so I'm following up with the information you asked for."
        )
    else:
        why = (
            f"You filled in a form on our website {lead.topic_clause}, "
            "so I'm calling with the information you asked for."
        )
    return (
        f"Hi {lead.first_name}, this is {state.config.agent_name} from Hoplon and Co. {why} "
        "Just so you know, this call is recorded. Is now a good time for two minutes?"
    )


def _end(s: CallState, status: LeadStatus, outcome: str) -> None:
    s.stage = Stage.ENDED
    s.status = status
    s.outcome = outcome


def transition(
    prev: CallState, event: Event, detail: str | None = None
) -> tuple[CallState, Effects]:
    """Apply one event. Returns the new state and what the voice layer must do.

    `detail` carries event data: the slot list for SLOTS_FOUND (joined by '|'),
    the chosen slot for ACCEPT_SLOT, the email for NEW_EMAIL, the time for
    CALLBACK_IN_WINDOW, and the preference for GIVE_PREFERENCE.
    """
    if event not in allowed(prev):
        raise IllegalEvent(prev.stage, event)

    s = copy.deepcopy(prev)
    cfg = s.config
    lead = s.lead
    fx = Effects()

    match event:
        case Event.ANSWERED:
            s.stage = Stage.IDENTITY
            fx.say = line("identity", s)
        case Event.NO_ANSWER:
            _end(s, LeadStatus.RETRY, "No answer. Next attempt tomorrow at the opposite time.")
        case Event.VOICEMAIL:
            _end(s, LeadStatus.RETRY, "Voicemail left (attempt 1 only) and booking link emailed.")
            fx.say = (
                f"Hi {lead.first_name}, {cfg.agent_name} from Hoplon and Co, following up on the form you "
                f"sent us {lead.topic_clause}. I'll try you again tomorrow, or you can reply "
                "to our email."
            )
        case Event.WRONG_PERSON:
            _end(s, LeadStatus.WRONG_NUMBER, "Wrong person. Apologised and ended.")
            fx.say = line("wrong_number", s)
        case Event.IDENTITY_UNCLEAR:
            s.identity_asks += 1
            fx.say = line("identity_unclear_1" if s.identity_asks == 1 else "identity_unclear_2", s)
        case Event.HANG_UP_SILENT:
            _end(s, LeadStatus.RETRY, "Hung up before speaking. Counts as no answer.")
        case Event.LINE_DROPS:
            _end(s, LeadStatus.CALLBACK, "Line dropped. One callback attempt (counts as a retry).")

        case Event.CONFIRM_IDENTITY:
            s.stage = Stage.OPENING
            s.opening = OpeningChecks(True, True, True)
            fx.say = opening_line(s)
        case Event.GOOD_TIME:
            s.stage = Stage.INFO
            fx.guide = (
                f"The Lead agreed to talk. Thank them briefly, then give the information about "
                f"{lead.topic_phrase} and ask one friendly question about their project."
            )
        case Event.OBJECTS_RECORDING:
            _end(s, LeadStatus.PARKED_RECORDING, "Declined recording. Information sent by email.")
            fx.say = line("objects_recording", s)

        case Event.SPEAKS_ARABIC:
            s.prev_stage = s.stage
            s.stage = Stage.ARABIC_CHECK
            fx.say = (
                "Wa alaikum assalam! I'm sorry, I can only continue in English or Hindi. "
                "Would one of those work for you?"
                if cfg.hindi
                else "Wa alaikum assalam! I'm sorry, I can only continue in English. "
                "My manager speaks English too. Would that work for you?"
            )
        case Event.ENGLISH_OK:
            s.stage = Stage.INFO if s.prev_stage in (Stage.OPENING, None) else s.prev_stage
            fx.guide = (
                f"English is fine for the Lead. Thank them and continue about {lead.topic_phrase}."
            )
        case Event.ENGLISH_NO:
            _end(s, LeadStatus.PARKED_ARABIC, "Needs Arabic (v2). Information sent by email.")
            fx.say = "No problem at all. I'll send you the details by email. Thank you!"

        case Event.LEAD_TURN:
            s.rapport_turns += 1
            if s.rapport_turns >= cfg.min_rapport_turns:
                s.stage = Stage.INTENT
                fx.guide = (
                    "React warmly to what the Lead said, then ask if this is something they "
                    "want to move ahead with soon."
                )
        case Event.INTENT_YES | Event.ASK_MANAGER:
            s.stage = Stage.BOOKING_PREF
            s.status = LeadStatus.QUALIFIED
            if event is Event.ASK_MANAGER:
                fx.guide = (
                    "Say: 'Of course, let me connect you with my manager.' Then ask whether "
                    "earlier or later this week works better, morning or afternoon."
                )
            else:
                fx.guide = (
                    "Suggest a 30-minute call with your manager as the next step. Say budget and "
                    "timeline can be adjusted to their needs and the manager goes through that. "
                    "Ask whether earlier or later this week works better, morning or afternoon."
                )
        case Event.OBJECTION:
            s.objections += 1
            if s.objections > cfg.max_objections:
                _end(s, LeadStatus.PARKED, f"Parked after {cfg.max_objections} objection attempts.")
                fx.say = line("parked_objections", s)
            elif s.objections == 1:
                fx.guide = (
                    "Agree to send the email, then explain gently that a short call with your "
                    "manager saves back-and-forth because it is tailored to them. Ask if 30 "
                    "minutes this week works. Never sound needy."
                )
            else:
                fx.guide = (
                    "No pressure. Offer to pencil in a time that they can move later. "
                    "Keep it light and short."
                )
        case Event.NO_INTENT:
            _end(
                s, LeadStatus.PARKED, "No Intent to Buy. Did not reject contact. Re-nurture later."
            )
            fx.say = line("no_intent", s)
        case Event.ASK_PRICE:
            s.price_deflections += 1
            if s.stage in (Stage.INFO, Stage.INTENT):
                s.stage = Stage.BOOKING_PREF
                s.status = LeadStatus.QUALIFIED
                fx.guide = (
                    f"Say: '{line('no_budget', s)}' Then offer a quick 30-minute call with your "
                    "manager and ask whether earlier or later this week works, morning or "
                    "afternoon. Never give a number."
                )
            else:
                fx.guide = f"Say: '{line('no_budget', s)}' Then continue with the booking."
        case Event.ASK_TIMELINE:
            fx.guide = f"Say: '{line('no_timeline', s)}' Never give a duration. Then continue."
        case Event.ASK_BOT:
            s.ai_disclosed = True
            fx.guide = (
                "Answer honestly: yes, you are Hoplon's AI assistant, and you can answer "
                "questions and book them in with your manager. Then continue where you were."
            )
        case Event.NOT_NOW:
            if s.callbacks_used >= cfg.max_callbacks:
                _end(s, LeadStatus.PARKED, "Maximum callbacks reached. Parked.")
                fx.say = line("max_callbacks", s)
            else:
                s.prev_stage = s.stage
                s.stage = Stage.CALLBACK
                fx.guide = (
                    f"Say no problem and ask when is a good time to call back. You can only "
                    f"call {cfg.window_text}."
                )
        case Event.CALLBACK_OUTSIDE:
            fx.guide = (
                f"Explain that you can only call {cfg.window_text}, and suggest tomorrow at 4pm."
            )
        case Event.CALLBACK_IN_WINDOW:
            s.callbacks_used += 1
            s.callback_time = detail or "the agreed time"
            _end(
                s,
                LeadStatus.CALLBACK,
                f"Callback booked for {s.callback_time} "
                f"({s.callbacks_used}/{cfg.max_callbacks}; not a retry).",
            )
            fx.say = line("callback_booked", s, time=s.callback_time)
        case Event.NOT_INTERESTED:
            _end(s, LeadStatus.OPTED_OUT, "Opted out. Never called again.")
            fx.say = line("not_interested", s)
        case Event.HANG_UP_NEGATIVE:
            _end(s, LeadStatus.OPTED_OUT, "Negative statement, then hang-up. Opted out.")

        case Event.GIVE_PREFERENCE:
            s.slot_round = 1
            fx.action = "find_slots"
            fx.action_arg = detail or ""
        case Event.SLOTS_FOUND:
            s.stage = Stage.BOOKING_OFFER
            s.offered = [x for x in (detail or "").split("|") if x][:2]
            if len(s.offered) < 2:
                _end(s, LeadStatus.LINK_SENT, "No free slots found. Booking link emailed.")
                fx.say = line("no_slots", s)
            else:
                fx.guide = (
                    f"Offer exactly these two times: {s.offered[0]} or {s.offered[1]}. "
                    "Ask which suits them better. Do not offer other times."
                )
        case Event.NEITHER_SLOT:
            if s.slot_round >= cfg.max_slot_rounds:
                _end(
                    s, LeadStatus.LINK_SENT, "No slot agreed after 2 rounds. Booking link emailed."
                )
                fx.say = line("no_slot_agreed", s)
            else:
                s.slot_round += 1
                fx.action = "find_slots"
                fx.action_arg = detail or ""
        case Event.ACCEPT_SLOT:
            s.chosen = _match_slot(s.offered, detail)
            s.stage = Stage.EMAIL_CONFIRM
            fx.guide = (
                f"Confirm {s.chosen}. Say you will send the invite to the email they used on the "
                f"form, the one at {lead.email_domain}, and ask if that is still best."
            )
        case Event.NEW_EMAIL:
            s.email = (detail or "").strip() or s.email
            fx.guide = (
                f"Spell the new email back slowly, letter by letter: {s.email}. "
                "Ask if that is right."
            )
        case Event.EMAIL_OK:
            s.stage = Stage.BOOKING_PENDING
            s.email = s.email or lead.email
            fx.say = line("lock_in", s)
            fx.action = "book"
            fx.action_arg = s.chosen
        case Event.CALENDAR_CONFIRMS:
            s.booking_confirmed = True
            _end(s, LeadStatus.BOOKED, f"Discovery Call booked: {s.chosen}. Invite sent.")
            fx.say = line("booked", s, slot=s.chosen or "")
        case Event.CALENDAR_SLOT_TAKEN:
            s.stage = Stage.BOOKING_OFFER
            s.slot_round = min(s.slot_round + 1, cfg.max_slot_rounds)
            fx.say = line("slot_taken", s)
            fx.action = "find_slots"
            fx.action_arg = ""
        case Event.CALENDAR_ERROR:
            _end(
                s,
                LeadStatus.LINK_SENT,
                "Calendar failed. Booking link emailed. Never claimed booked.",
            )
            fx.say = line("calendar_error", s)

    return s, fx


def _match_slot(offered: list[str], detail: str | None) -> str | None:
    if not offered:
        return detail
    if detail:
        d = detail.lower()
        for slot in offered:
            if slot.lower() in d or d in slot.lower():
                return slot
        for slot in offered:
            day, _, time = slot.lower().partition(" at ")
            if day in d or (time and time in d.replace(" ", "")):
                return slot
        if any(w in d for w in ("second", "2nd", "latter", "last", "other")):
            return offered[-1]
    return offered[0]


def start(lead: Lead, config: CallConfig | None = None) -> CallState:
    return CallState(lead=lead, config=config or CallConfig())
