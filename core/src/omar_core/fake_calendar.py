"""A fake Manager calendar for the demo (decision D1).

Same rules as the real one (ticket 11): Asia/Dubai (UTC+4, no DST), 30-minute
Discovery Calls, Mon-Fri 10:00-18:00, 15-minute buffers, 2 hours to 7 days
out. Some blocks are busy. The real Google Calendar replaces this in M2.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Literal

DUBAI = timezone(timedelta(hours=4), "GST")
CALL = timedelta(minutes=30)
BUFFER = timedelta(minutes=15)
STEP = CALL + BUFFER
DAY_START, DAY_END = 10, 18
MIN_LEAD, MAX_LEAD = timedelta(hours=2), timedelta(days=7)

BookResult = Literal["confirmed", "taken", "error"]


def speak(dt: datetime) -> str:
    """'Tuesday at 11am', 'Wednesday at 3:45pm'."""
    hour = dt.hour % 12 or 12
    minute = f":{dt.minute:02d}" if dt.minute else ""
    return f"{dt:%A} at {hour}{minute}{'am' if dt.hour < 12 else 'pm'}"


@dataclass
class FakeCalendar:
    seed: int = 7
    busy_ratio: float = 0.4
    taken_rate: float = 0.0  # chance that a booking finds the slot just taken
    error_rate: float = 0.0  # chance that the calendar fails
    now: datetime | None = None
    _busy: set[datetime] = field(default_factory=set)
    _booked: dict[str, datetime] = field(default_factory=dict)
    _offered: dict[str, datetime] = field(default_factory=dict)
    _shown: set[datetime] = field(default_factory=set)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)
        for slot in self._all_slots():
            if self._rng.random() < self.busy_ratio:
                self._busy.add(slot)

    def _now(self) -> datetime:
        return (self.now or datetime.now(DUBAI)).astimezone(DUBAI)

    def _all_slots(self) -> list[datetime]:
        now = self._now()
        out: list[datetime] = []
        day = now.replace(hour=DAY_START, minute=0, second=0, microsecond=0)
        while day <= now + MAX_LEAD:
            if day.weekday() < 5:
                t = day
                while t + CALL <= day.replace(hour=DAY_END):
                    if now + MIN_LEAD <= t <= now + MAX_LEAD:
                        out.append(t)
                    t += STEP
            day += timedelta(days=1)
        return out

    def free_slots(self, preference: str = "", count: int = 2) -> list[str]:
        """Up to `count` free slots that match the preference, spoken style.

        Slots already offered on this call are skipped, so a second round
        gives new times.
        """
        free = [s for s in self._all_slots() if s not in self._busy and s not in self._shown]
        picked = _filter(free, preference, self._now()) or free
        # spread the two offers: first match, then one on a different day if possible
        chosen: list[datetime] = []
        for slot in picked:
            if not chosen or slot.date() != chosen[0].date() or len(picked) < 4:
                chosen.append(slot)
            if len(chosen) == count:
                break
        for slot in chosen:
            self._shown.add(slot)
            self._offered[speak(slot)] = slot
        return [speak(s) for s in chosen]

    def book(self, spoken_slot: str) -> BookResult:
        slot = self._offered.get(spoken_slot)
        if slot is None:
            return "error"
        if self._rng.random() < self.error_rate:
            return "error"
        if slot in self._busy or self._rng.random() < self.taken_rate:
            self._busy.add(slot)
            return "taken"
        self._busy.add(slot)
        self._booked[spoken_slot] = slot
        return "confirmed"

    @property
    def bookings(self) -> dict[str, datetime]:
        return dict(self._booked)


_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"]


def _filter(slots: list[datetime], preference: str, now: datetime) -> list[datetime]:
    p = preference.lower()
    out = slots
    if "morning" in p:
        out = [s for s in out if s.hour < 12]
    elif "afternoon" in p or "evening" in p:
        out = [s for s in out if s.hour >= 12]
    named = [i for i, d in enumerate(_DAYS) if d in p]
    if named:
        out = [s for s in out if s.weekday() in named]
    elif "tomorrow" in p:
        out = [s for s in out if s.date() == (now + timedelta(days=1)).date()]
    elif "next week" in p:
        out = [s for s in out if s.isocalendar().week != now.isocalendar().week]
    elif "early" in p or "earlier" in p:
        out = [s for s in out if s.weekday() <= 2]
    elif "later" in p or "late" in p or "end of" in p:
        out = [s for s in out if s.weekday() >= 2]
    return out
