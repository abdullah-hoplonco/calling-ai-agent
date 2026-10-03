# Mid-call failure handling

Type: grilling
Status: resolved
Map: ../map.md

## Question

What does Omar do when the LLM, the GPU, STT, TTS or the calendar fails or is slow during a Connected Call? Covers what the Lead hears, how it counts against retry limits, and how the Manager is alerted.

## Answer

Settled with the owner 2026-10-03.

**Failover per component**
- LLM/GPU: same-turn failover to the backup LLM, with a natural "one sec…" if needed.
- TTS: failover to ElevenLabs.
- Calendar: the booking link is emailed.
- STT: "Sorry, the line is bad. I'll call you right back"; the call ends and a callback is scheduled, counted as a retry (same as a dropped line).
- Total failure: the call ends, a callback is scheduled, and the dialer pauses itself until the system is healthy.

**Alerts**
- Every failover is logged.
- Email/Slack alerts for GPU down, repeated failovers, or a dialer self-pause.
