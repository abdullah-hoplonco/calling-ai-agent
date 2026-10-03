# UAE rules for outbound AI sales calls

Type: research
Status: resolved
Map: ../map.md

## Question

What do UAE regulations require of an outbound AI calling agent contacting Leads who submitted a web form with their phone number? Cover: TDRA telemarketing rules (permitted calling hours/days, licensed or registered numbers, caller identification, max attempts, DNC registry); whether AI/automated callers must disclose they are AI; call-recording consent; UAE PDPL implications for storing Lead PII, recordings and transcripts; whether form submission counts as sufficient consent; and penalties. Cite primary sources (TDRA, UAE Cabinet resolutions, official gazette).

## Answer

- **Governing text**: Cabinet Resolution 56/2024 (rules) and 57/2024 (fines), in force since 27 Aug 2024. They apply to all UAE-licensed companies, free zones included. Calls "at the request of the Consumer" are excluded from "Unwanted" calls, but the Art. 4 and Art. 5 controls should still be treated as applying.
- **Call rules**: calls only between 09:00 and 18:00, with no day-of-week rule. After no answer or a hang-up, at most 1 retry per day and 2 per week. Never call again after a first-call rejection. No DNCR numbers; the text has no carve-out for form leads.
- **Opening of every call**: name the company and the purpose. Say the call is recorded. Ask whether the Lead wants to continue before any pitch.
- **Numbers and approval**: the caller ID must be a UAE-operator number registered to the agency's trade licence. Twilio UAE geographic numbers are banned from outbound calling, so a UAE operator number via BYOC or SIP is likely needed. Prior approval from the "Competent Authority" (the licensing body, e.g. DET) is required. Staff training, a call register and periodic reports are also required.
- **AI disclosure**: no binding onshore UAE rule requires volunteering that the caller is an AI. Res 56 expressly permits automated systems. Denying being an AI when asked risks the "deception" fine (AED 25k–75k), so "answer honestly if asked" must be a hard guardrail. Exception: DIFC entities (Reg 10 notice).
- **Recording**: recording is *mandatory* (Art. 4(7)), with notice at the start of the call. Recording without consent is also a crime (Penal Code Art. 431, Cybercrime Law Art. 44), so announce it and get consent in the form too.
- **PDPL**: the default basis is consent, which must be a clear positive action, provable and withdrawable. Vendors abroad mean cross-border processing, so get explicit consent and sign DPAs. Needed: a privacy notice, a set retention limit, and handling for direct-marketing objection, access and erasure. Executive Regulations and fines were still not issued as of June 2026.
- **Form consent**: a web form fits the Res 56 "interested consumers channel" model. Make it an unticked checkbox covering the call, recording, cross-border processors and (recommended) the AI assistant. Store evidence: timestamp, IP address and form wording.
- **Penalties (Res 57)**: AED 10k–150k per violation, escalating over three tiers. The top tier covers no approval, DNCR calls and data trading. Other sanctions are suspension for 7–90 days, licence cancellation and number removal. A repeat within 6 months allows the maximum penalty.
- **Open questions**: the approval procedure, DNCR checking mechanics, the call-register form and retention period, and whether a newer AI rule has been issued. See the findings file.

[findings](../research/01-uae-calling-regulations.md)
