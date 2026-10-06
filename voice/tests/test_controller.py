from datetime import datetime

from omar_core import DEFAULT_LEAD, LeadStatus, Stage
from omar_core.fake_calendar import DUBAI, FakeCalendar
from omar_voice.controller import CallController

NOW = datetime(2026, 10, 5, 9, 0, tzinfo=DUBAI)


def ctl(**kw) -> CallController:
    c = CallController(lead=DEFAULT_LEAD, calendar=FakeCalendar(now=NOW, busy_ratio=0, **kw))
    c.start()
    return c


def to_booking(c: CallController) -> None:
    c.report("confirm_identity")
    c.report("good_time")
    c.report("intent_yes")


def test_start_greets_by_first_name():
    c = CallController(lead=DEFAULT_LEAD)
    assert c.start().say == "Hi, is this Khalifa?"


def test_report_rejects_events_from_other_stages():
    c = ctl()
    r = c.report("intent_yes")
    assert r.error and "does not apply" in r.error
    assert c.stage is Stage.IDENTITY


def test_report_rejects_system_events_and_unknown_names():
    c = ctl()
    assert c.report("calendar_confirms").error
    assert c.report("make_coffee").error


def test_opening_is_scripted_and_llm_stays_silent():
    c = ctl()
    r = c.report("confirm_identity")
    assert r.say and "this call is recorded" in r.say
    assert r.tool_output() is None


def test_rapport_counted_by_code():
    c = ctl()
    c.report("confirm_identity")
    c.report("good_time")
    assert c.lead_turn() is False
    assert c.lead_turn() is True
    assert c.stage is Stage.INTENT


def test_preference_runs_the_calendar_and_offers_two_slots():
    c = ctl()
    to_booking(c)
    r = c.report("give_preference", "later this week, afternoon")
    assert c.stage is Stage.BOOKING_OFFER and len(c.state.offered) == 2
    assert c.state.offered[0] in r.guide and c.state.offered[1] in r.guide
    assert [s.event for s in c.steps][-2:] == ["give_preference", "slots_found"]


def test_full_booking_says_booked_only_from_code():
    c = ctl()
    to_booking(c)
    c.report("give_preference", "morning")
    c.report("accept_slot", c.state.offered[0])
    r = c.report("email_ok")
    assert c.state.status is LeadStatus.BOOKED and r.ended
    assert r.say.startswith("One moment while I lock that in. You're booked for")
    assert r.tool_output() is None  # code speaks it all; the LLM adds nothing


def test_slot_taken_gives_say_plus_guide_to_llm():
    c = ctl(taken_rate=1.0)
    to_booking(c)
    c.report("give_preference", "morning")
    c.report("accept_slot")
    r = c.report("email_ok")
    assert c.stage is Stage.BOOKING_OFFER and not c.state.booking_confirmed
    out = r.tool_output()
    assert out.startswith("Say this first, word for word:") and "taken" in out
    assert "booked for" not in out.lower()


def test_line_drop_ends_live_call():
    c = ctl()
    c.report("confirm_identity")
    c.line_dropped()
    assert c.state.ended and c.state.status is LeadStatus.CALLBACK


def test_snapshot_shape():
    snap = ctl().snapshot()
    assert snap["stage"] == "IDENTITY" and snap["steps"][0]["event"] == "answered"
