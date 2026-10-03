# Twilio outbound calling into the UAE

Type: research
Status: resolved
Map: ../map.md

## Question

Can Twilio place reliable outbound calls to UAE mobile and landline numbers, and on what terms? Cover: availability of UAE caller IDs/numbers (or which foreign numbers are used and whether UAE carriers block/flag them), regulatory bundles required, pricing per minute to UAE mobiles, answering-machine detection (AMD) capabilities and latency, Media Streams (bidirectional WebSocket audio) specs, and alternatives if Twilio is unsuitable (local SIP trunks, other CPaaS with UAE presence).

## Answer

- Twilio can terminate calls to UAE mobiles and landlines, but only with a **foreign (+E164) caller ID**. Twilio publishes no guaranteed caller ID and no UAE best practices, and foreign-CLI answer and block rates are unknown.
- Twilio sells only **UAE toll-free (+971 800)** numbers, and they are inbound-only in practice. Its terms **prohibit outbound calls from UAE geographic numbers**.
- **Decisive constraint:** UAE Cabinet Resolution 56/2024 requires marketing calls to use **local numbers from UAE-licensed telcos registered under the company's trade licence** (Art. 4(3), 4(13)). It also sets a 09:00–18:00 window, at most 1 retry a day and 2 a week, no re-calls after a rejection, DNCR checks, recording with a disclosure, and identifying the company and purpose up front. Automated systems are explicitly allowed (Art. 5(6)).
- So plain Twilio outbound is likely non-compliant for Connected Calls. The paths are **Twilio BYOC + an e&/du trunk** (the carrier agreeing to this is unverified), or an **e&/du SIP trunk into a self-hosted media server in the UAE**. UAE legal advice is needed on warm-lead exemptions.
- Price: **$0.2995/min to UAE mobile**, $0.3635/min to landline, Media Streams $0.0044/min, AMD $0.0075/call. That is roughly $0.93 of Twilio cost per 3-minute call.
- AMD takes about 4 s with defaults. Synchronous AMD makes the callee sit in silence, so use **Async AMD**. Accuracy is tuned for the US and is lower internationally, so expect tuning plus a detector in the voice server.
- Media Streams: `<Connect><Stream>` gives bidirectional audio over `wss`, **8 kHz μ-law mono base64**, with `mark` and `clear` for barge-in. It is available in the **IE1 (Ireland)** region. Twilio has no Middle East edge.
- Other options: e&/du SIP trunks, Unifonic, Infobip. Telnyx, Vonage and Plivo share Twilio's foreign-CLI problem. Some hosted AI platforms (Retell) block AE outright.

[findings](../research/02-twilio-uae-outbound.md)
