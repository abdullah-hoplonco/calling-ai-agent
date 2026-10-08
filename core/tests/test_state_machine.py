import pytest

from omar_core import DEFAULT_LEAD, Event, IllegalEvent, Lead, LeadStatus, Stage, start, transition
from omar_core.state_machine import CallState, reportable

E = Event


def run(*events, lead=DEFAULT_LEAD, state=None):
    """Apply events in order. Each item is an Event or (Event, detail)."""
    s = state or start(lead)
    fx = None
    for item in events:
        ev, detail = item if isinstance(item, tuple) else (item, None)
        s, fx = transition(s, ev, detail)
    return s, fx


def to_info(**kw) -> CallState:
    s, _ = run(E.ANSWERED, E.CONFIRM_IDENTITY, E.GOOD_TIME, **kw)
    return s


def test_greeting_is_scripted():
    s, fx = run(E.ANSWERED)
    assert s.stage is Stage.IDENTITY
    assert fx.say == "Hi, is this Khalifa?"


def test_legal_opening_order_and_wording():
    s, fx = run(E.ANSWERED, E.CONFIRM_IDENTITY)
    assert s.stage is Stage.OPENING
    assert (
        s.opening.company_and_purpose and s.opening.recording_notice and s.opening.asked_to_continue
    )
    line = fx.say
    company = line.index("Nimra from Hoplon and Co")
    purpose = line.index("so I'm calling with the information you asked for")
    recording = line.index("this call is recorded")
    ask = line.index("Is now a good time")
    assert company < purpose < recording < ask


def test_old_lead_opening_names_the_month():
    old = Lead(name="Rhea Fernandes", topic="a website", lead_type="old", submitted_month="March")
    _, fx = run(E.ANSWERED, E.CONFIRM_IDENTITY, lead=old)
    assert "back in March about a website" in fx.say


def test_lead_without_topic_gets_generic_purpose():
    _, fx = run(E.ANSWERED, E.CONFIRM_IDENTITY, lead=Lead(name="Rhea Fernandes"))
    assert "asking about our services" in fx.say


def test_info_cannot_be_reached_before_lead_agrees():
    s, _ = run(E.ANSWERED, E.CONFIRM_IDENTITY)
    with pytest.raises(IllegalEvent):
        transition(s, E.LEAD_TURN)
    assert E.LEAD_TURN not in reportable(s)


def test_rapport_turns_before_intent_probe():
    s = to_info()
    for _ in range(s.config.min_rapport_turns - 1):
        s, fx = transition(s, E.LEAD_TURN)
        assert s.stage is Stage.INFO and fx.guide is None
    s, fx = transition(s, E.LEAD_TURN)
    assert s.stage is Stage.INTENT
    assert "move ahead" in fx.guide


def test_persona_name_is_config():
    from omar_core import CallConfig

    _, fx = run(
        E.ANSWERED, E.CONFIRM_IDENTITY, state=start(DEFAULT_LEAD, CallConfig(agent_name="Sara"))
    )
    assert "this is Sara from Hoplon and Co" in fx.say


@pytest.mark.parametrize("event", [E.ASK_PRICE, E.ASK_MANAGER, E.INTENT_YES])
def test_intent_signals_in_info_go_to_booking(event):
    s, _ = transition(to_info(), event)
    assert s.stage is Stage.BOOKING_PREF
    assert s.status is LeadStatus.QUALIFIED


def test_price_question_never_gives_a_number():
    _, fx = transition(to_info(), E.ASK_PRICE)
    assert "adjust the budget" in fx.guide
    assert "Never give a number" in fx.guide


def test_ask_manager_uses_manager_wording():
    _, fx = transition(to_info(), E.ASK_MANAGER)
    assert "connect you with my manager" in fx.guide


def test_two_objections_handled_third_parks():
    s = to_info()
    s, _ = run(*[E.LEAD_TURN] * s.config.min_rapport_turns, state=s)
    s, fx1 = transition(s, E.OBJECTION)
    s, fx2 = transition(s, E.OBJECTION)
    assert s.stage is Stage.INTENT and fx1.guide and fx2.guide
    s, fx3 = transition(s, E.OBJECTION)
    assert s.ended and s.status is LeadStatus.PARKED
    assert fx3.say and "email you the details" in fx3.say


def test_declined_recording_parks_not_opts_out():
    s, _ = run(E.ANSWERED, E.CONFIRM_IDENTITY, E.OBJECTS_RECORDING)
    assert s.status is LeadStatus.PARKED_RECORDING


def test_not_interested_opts_out():
    s, fx = transition(to_info(), E.NOT_INTERESTED)
    assert s.status is LeadStatus.OPTED_OUT and "won't call again" in fx.say


def test_ask_bot_is_honest_and_keeps_stage():
    s, fx = transition(to_info(), E.ASK_BOT)
    assert s.stage is Stage.INFO and s.ai_disclosed
    assert "AI assistant" in fx.guide


def test_callback_inside_window():
    s, fx = run(E.NOT_NOW, (E.CALLBACK_OUTSIDE, None), state=to_info())
    assert s.stage is Stage.CALLBACK and "only call" in fx.guide
    s, fx = transition(s, E.CALLBACK_IN_WINDOW, "tomorrow at 4pm")
    assert s.status is LeadStatus.CALLBACK and s.callback_time == "tomorrow at 4pm"
    assert fx.say == "Perfect, I'll call you tomorrow at 4pm. Speak then!"


def test_max_callbacks_parks():
    s = to_info()
    s.callbacks_used = 2
    s, _ = transition(s, E.NOT_NOW)
    assert s.status is LeadStatus.PARKED


def test_arabic_check_paths():
    s, fx = run(E.ANSWERED, E.CONFIRM_IDENTITY, E.SPEAKS_ARABIC)
    assert s.stage is Stage.ARABIC_CHECK and "English" in fx.say
    ok, _ = transition(s, E.ENGLISH_OK)
    assert ok.stage is Stage.INFO
    no, _ = transition(s, E.ENGLISH_NO)
    assert no.status is LeadStatus.PARKED_ARABIC


def booking_offer(state=None):
    s, _ = run(E.INTENT_YES, state=state or to_info())
    s, fx = transition(s, E.GIVE_PREFERENCE, "later this week, afternoon")
    assert fx.action == "find_slots" and fx.action_arg == "later this week, afternoon"
    s, fx = transition(s, E.SLOTS_FOUND, "Wednesday at 3pm|Thursday at 4pm")
    return s, fx


def test_slots_are_offered_exactly():
    s, fx = booking_offer()
    assert s.stage is Stage.BOOKING_OFFER
    assert "Wednesday at 3pm or Thursday at 4pm" in fx.guide


def test_happy_path_booked_only_after_calendar():
    s, _ = booking_offer()
    s, fx = transition(s, E.ACCEPT_SLOT, "the thursday one")
    assert s.chosen == "Thursday at 4pm" and s.stage is Stage.EMAIL_CONFIRM
    assert "example.com" in fx.guide
    s, fx = transition(s, E.EMAIL_OK)
    assert s.stage is Stage.BOOKING_PENDING and fx.action == "book"
    assert "booked" not in (fx.say or "").lower()
    assert not s.booking_confirmed
    s, fx = transition(s, E.CALENDAR_CONFIRMS)
    assert s.status is LeadStatus.BOOKED and s.booking_confirmed
    assert fx.say.startswith("You're booked for Thursday at 4pm")


def test_slot_taken_reoffers_without_booked_claim():
    s, _ = booking_offer()
    s, _ = run(E.ACCEPT_SLOT, E.EMAIL_OK, state=s)
    s, fx = transition(s, E.CALENDAR_SLOT_TAKEN)
    assert s.stage is Stage.BOOKING_OFFER and fx.action == "find_slots"
    assert "taken" in fx.say and "booked" not in fx.say


def test_calendar_error_sends_link():
    s, _ = booking_offer()
    s, _ = run(E.ACCEPT_SLOT, E.EMAIL_OK, E.CALENDAR_ERROR, state=s)
    assert s.status is LeadStatus.LINK_SENT and not s.booking_confirmed


def test_two_rounds_of_neither_sends_link():
    s, _ = booking_offer()
    s, fx = transition(s, E.NEITHER_SLOT, "next week")
    assert fx.action == "find_slots" and s.slot_round == 2
    s, _ = transition(s, E.SLOTS_FOUND, "Monday at 2pm|Tuesday at 4pm")
    s, fx = transition(s, E.NEITHER_SLOT)
    assert s.status is LeadStatus.LINK_SENT


def test_new_email_is_spelled_back():
    s, _ = booking_offer()
    s, _ = transition(s, E.ACCEPT_SLOT)
    s, fx = transition(s, E.NEW_EMAIL, "khalifa@laundry.ae")
    assert s.email == "khalifa@laundry.ae" and "letter by letter" in fx.guide


def test_llm_never_sees_system_events():
    s = to_info()
    names = {e.value for e in reportable(s)}
    assert "lead_turn" not in names and "calendar_confirms" not in names


def test_transition_does_not_mutate_input():
    s = to_info()
    transition(s, E.LEAD_TURN)
    assert s.rapport_turns == 0
