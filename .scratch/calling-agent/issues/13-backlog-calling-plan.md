# Backlog calling plan

Type: grilling
Status: resolved
Blocked by: 01, 06, 10, 20
Map: ../map.md

## Question

How and when should the existing backlog be called: ordering (recency, service interest), daily pacing/concurrency, whether very old Leads get a different opening, and a soft-launch plan (e.g. a small first batch reviewed by the Manager before scaling)?

## Answer

Settled with the owner 2026-09-29. Every value below is config.

**Order**
- Newest first: Leads from the last 3 months, then 3-12 months, then older than 12 months (called last).
- New Leads always go before the backlog, so speed-to-lead never waits.

**Old-Lead opening**
- For Leads older than about 30 days, Omar says when they reached out and about what: "You reached out to us back in March about an app. Is that still something you're thinking about?"

**Cleaning before dialing**
- Ingestion dedupes and drops spam and invalid numbers.
- "Don't call" notes in the message make the Lead Opted-out.
- Non-UAE numbers are skipped and flagged for the Manager.
- Arabic-only Leads are called, using the amended persona rule: "My manager speaks English, would that work for you?", then Park as "needs Arabic" if they decline. (The agent chose this to stay consistent with the owner's Arabic decision; the owner can override.)

**Soft launch, run as a dashboard campaign the Manager starts**
1. Batch of 10 Leads; the Manager reviews every recording and transcript.
2. Batch of 25 Leads; spot-checked.
3. Full pace.

Each stage opens only if the previous batch had zero rule breaches (legal opening, budget talk, false booking) and the Manager approves the tone.

**Pace**
- At most 30 backlog dials a day and at most 2 concurrent calls.
- Pause automatically when the Manager's next 7 days have fewer than 5 free Discovery Call slots.

