# Lead lifecycle and data model

Type: grilling
Status: resolved
Blocked by: 06, 08
Map: ../map.md

## Question

What states does a Lead move through (e.g. New, Calling, Callback, Qualified, Booked, Parked, Do-Not-Call), what triggers each transition, and what data is stored per Lead and per Connected Call (transcript, recording, outcome, Intent to Buy evidence, cost)?

## Answer

Settled with the owner 2026-09-30.

**Lead statuses** (the Lead's lifecycle across all calls; separate from the per-call state machine)
- New, Queued, In call, Retry scheduled, Callback scheduled.
- Qualified: Booked, or Link sent.
- Parked (reason: no intent / declined recording / needs Arabic / max callbacks).
- Opted-out, Unreachable.
- Invalid (spam / bad number / wrong person / non-UAE). Invalid Leads are kept out of funnel metrics.

**Identity**
- One Lead per normalised E.164 phone number.
- Every form fill is a **Submission** linked to its Lead. The newest Submission's message drives the opening.

**Calls**
- Every dial is a **Call Attempt**: Twilio call SID, result (no answer / voicemail / connected / failed), cost, trace ID.
- A **Connected Call** (the owner renamed the term from "Qualification Call") is a Call Attempt with a live conversation. It adds the recording, transcript, per-turn timings, outcome, Intent to Buy evidence and judge scores.

**Discovery Call outcome**
- After each Discovery Call, the Manager marks it in one click: Attended / No-show / Won / Lost. This measures booking quality, not just volume.

**Parked Leads**
- No automatic re-calls in the MVP. A "Re-queue" button is available to the Manager.

**Event log**
- Append-only: every status change, Call Attempt and manual edit, with timestamp, actor (Omar / Manager / system) and reason.
- The legal call register is generated from it.

**Retention**
- Recordings and transcripts are kept for a configurable period (default 12 months; the legal team sets the real value), enforced by a scheduled cleanup job.
- "Erase this Lead" removes personal data and keeps an anonymous record that the calls happened.

**Manual control**
- The Manager can change status, mark "do not call", fix email or phone, and add notes. Everything is logged.
