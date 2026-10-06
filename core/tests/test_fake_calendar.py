from datetime import datetime

from omar_core.fake_calendar import DUBAI, FakeCalendar, speak

MONDAY_9AM = datetime(2026, 10, 5, 9, 0, tzinfo=DUBAI)


def cal(**kw):
    return FakeCalendar(now=MONDAY_9AM, **kw)


def test_speak():
    assert speak(datetime(2026, 10, 6, 11, 0, tzinfo=DUBAI)) == "Tuesday at 11am"
    assert speak(datetime(2026, 10, 7, 15, 45, tzinfo=DUBAI)) == "Wednesday at 3:45pm"


def test_two_slots_inside_working_hours_and_lead_time():
    c = cal(busy_ratio=0)
    slots = c.free_slots()
    assert len(slots) == 2
    for s in c._offered.values():
        assert s.weekday() < 5 and 10 <= s.hour < 18
        assert (s - MONDAY_9AM).total_seconds() >= 2 * 3600


def test_preference_afternoon_later_this_week():
    c = cal(busy_ratio=0)
    c.free_slots("later this week, afternoon")
    for s in c._offered.values():
        assert s.hour >= 12 and s.weekday() >= 2


def test_second_round_gives_new_times():
    c = cal()
    first = c.free_slots("morning")
    second = c.free_slots("morning")
    assert not set(first) & set(second)


def test_book_confirms_then_slot_is_busy():
    c = cal(busy_ratio=0)
    slot = c.free_slots()[0]
    assert c.book(slot) == "confirmed"
    assert slot in c.bookings


def test_taken_and_error_rates():
    c = cal(busy_ratio=0, taken_rate=1.0)
    assert c.book(c.free_slots()[0]) == "taken"
    c = cal(busy_ratio=0, error_rate=1.0)
    assert c.book(c.free_slots()[0]) == "error"
    assert cal().book("Someday at noon") == "error"
