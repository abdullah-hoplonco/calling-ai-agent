# Call attempt, callback and voicemail policy

Type: grilling
Status: resolved
Blocked by: 01, 02, 17
Map: ../map.md

## Question

What is the dialing policy: calling hours/days, number of attempts, spacing, which attempt leaves a voicemail and what it says, how "call me later" callbacks are scheduled, and how answering machines are detected; within the legal limits from ticket 01 and Twilio capabilities from ticket 02?

## Answer

Settled with the owner 2026-09-28. Every value below is config.

**Calling window** (inside the legal 09:00-18:00)
- Monday-Thursday 10:00-17:30.
- Friday 10:00-12:00 (avoids Friday prayers).
- No calls on public holidays; reduced hours in Ramadan.
- Saturday and Sunday are the UAE weekend: no calls.

**No-answer sequence**
- Attempt 1: within minutes of the form submission, or at the next window opening if outside hours.
- Attempt 2: the next calling day, at the opposite time of day (morning ↔ afternoon).
- Attempt 3: 2 days later.
- Then stop and mark the Lead Unreachable. This fits the legal maximum of 1 retry a day and 2 a week.

**Voicemail**
- On attempt 1 only. Short and warm, mentions the form topic, and says "I'll try you again tomorrow, or you can reply to our email".
- The same day, send an email with the booking link.
- If the Lead calls the Twilio number back: forward to the Manager's mobile during working hours, and play a short recorded message otherwise. This is a Twilio routing setting, not inbound AI.

**Callbacks ("call me later")**
- Omar asks for a specific time and only agrees to times inside the calling window.
- A requested callback does not count as a no-answer retry.
- At most 2 callbacks per Lead, then Park.

**Rejections and hang-ups**
- A rejection ("not interested", "don't call me", "remove my number") makes the Lead an Opted-out Lead: never called again, and blocked from every future campaign.
- No Intent to Buy without a rejection ("just browsing", "maybe next year") makes the Lead a Parked Lead.
- Lead hangs up before saying anything: no answer.
- Lead hangs up after a negative statement: Opted-out.
- Line drop mid-conversation: one callback attempt, counted as a retry.
- A "don't call" or call-timing instruction written in the form message is honoured at ingestion.
