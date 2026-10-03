# Code owns the call state machine; the LLM speaks inside each stage

A Connected Call is driven by an explicit, hand-written call state machine in `core/`: Opening → Consent to continue → Info → Intent probe → Booking → Close, plus Parked, Callback and Voicemail. The LLM generates the words within the current stage and calls tools. It never decides on its own which stage comes next when a rule is at stake.

We chose this over a single large prompt because UAE telemarketing law (Cabinet Resolution 56/2024) and our own rules demand behaviour that must hold on every call, and a prompt only makes it likely. Those rules are:
- the fixed opening order: company and purpose, then the recording notice, then asking to continue;
- no budget or timeline talk;
- never claiming a Discovery Call is booked before the calendar confirms it;
- never denying being an AI.

A rigid decision tree was also rejected, because the Calling Agent must sound natural and become conversational once the Lead is at ease.

## Consequences

- Compliance rules are enforced and unit-tested in pure code, independent of the model or prompt in use.
- Changing conversation behaviour can mean editing the state machine, not only a prompt.
