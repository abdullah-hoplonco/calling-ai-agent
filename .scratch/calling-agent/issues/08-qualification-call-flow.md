# Connected Call flow and objection playbook

Type: prototype
Status: resolved
Blocked by: 01, 07
Map: ../map.md

## Question

How should a Connected Call behave, stage by stage? Produce a rough, reactable call flow (state diagram + sample dialogue): opening, confirming the form context, delivering requested info, probing for Intent to Buy, handling objections ("just send me an email", "not now", "how much?", "are you a bot?", "who is this?"), pushing to a Discovery Call, parking, "call me later", and closing. Settles what Intent to Buy signals look like and when to Park.

Also: how the agent captures and confirms the Lead's email address on the call (the calendar invite goes there; see ticket 04).

Also: must build in the legally required opening elements found in tickets 01/02: company name and purpose up front, recording disclosure, and asking whether the Lead wants to continue before pitching.

## Answer

Settled with the owner 2026-09-30, using the prototype [PROTOTYPE-call-flow.html](../prototypes/PROTOTYPE-call-flow.html). The pure `CallFlow` module inside it is the reference for `core/`'s call state machine (ADR 0001). The HTML shell is throwaway. There is no git repo yet, so the prototype stays in `prototypes/` as the primary source.

**Stages**
- Dialing → Identity check → Opening → Info → Intent probe → Booking. Booking runs: preference → 2-slot offer → email confirm → calendar pending.
- End states: Booked, Qualified with booking link, Callback, Parked, Opted-out, No-answer/voicemail, Wrong person.
- Side paths: Arabic check, and callback negotiation.

**Legal opening**
- Code delivers it as one scripted turn, in the fixed order: company and purpose, recording notice, "is now a good time?".
- The Info stage can't be reached until the Lead agrees to continue.

**Rapport before commitment (owner)**
- Omar stays in Info and is talkative for at least 2 Lead-engaged turns (config `minRapportTurns: 2`) before the Intent probe.

**Intent to Buy signals, each of which moves to booking**
- An explicit "yes, we want to do this".
- **Asking about price or cost (owner)**. Omar still never gives numbers; he defers to the Manager.
- **Asking to talk to someone (owner)**. This goes straight to booking with "let me connect you with my manager".

**Objections**
- Omar handles "just send me an email"-type objections **twice** (owner); on the third, he Parks politely and emails the info.

**Recording**
- If the Lead declines recording, the call ends, the info goes by email, and the Lead becomes a **Parked Lead** ("declined recording") (owner), not Opted-out.

**Honesty and guards**
- The AI question is answered honestly at any live stage.
- Price and timeline questions are deflected with the "we can adjust it to your needs, my manager will go through it" line.
- "Booked" is spoken only after the calendar confirms.
- If the slot is taken at booking time, Omar re-offers.
- If the calendar errors, the booking link is emailed.

**Callbacks, opt-outs, Arabic, voicemail**
- As in tickets 09, 10 and 13.
- Old backlog Leads get the "back in {month}" opening.

**Implementation note**
- Omar's lines in the prototype are samples. The real agent generates language within each stage; the stages, guards and counters are code.

