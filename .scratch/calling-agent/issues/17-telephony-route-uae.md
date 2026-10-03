# Telephony route for a UAE-compliant caller ID

Type: grilling
Status: resolved
Blocked by: 01, 02
Map: ../map.md

## Question

Which telephony route does the MVP use, given that UAE telemarketing rules appear to require a local caller ID from a UAE-licensed carrier (e&/du) registered to the trade licence? Options from ticket 02: (a) plain Twilio with a foreign caller ID (legal and answer-rate risk), (b) Twilio BYOC with an e&/du SIP trunk, (c) an e&/du SIP trunk into a self-hosted media server in a UAE cloud region (AWS me-central-1 or Azure UAE North), (d) a UAE CPaaS (Unifonic/Infobip). This decides the hosting region, the answering-machine detection approach and the latency budget.

## Answer

Settled with the owner 2026-09-27.

- **Development:** plain Twilio with a foreign caller ID, calling only the owner's and the team's own phones (not marketing calls).
- **Production route, in order of preference:**
  1. **(B) Twilio BYOC with an e&/du SIP trunk**, registered to the trade licence.
  2. **(A) An e&/du SIP trunk into our own media server** in a UAE cloud region (AWS me-central-1 or Azure UAE North), if the carrier will not connect to Twilio.
  The choice hangs on carrier facts, gathered in ticket 22 (Ask e& and du about a business SIP trunk).
- **Hosting region follows the route:**
  - Route B: Europe (Dublin/Frankfurt), next to Twilio IE1; expect about 100-150 ms of extra one-way travel from the UAE.
  - Route A: a UAE region.
  - Development is hosted in Europe. Real latency is measured on test calls and goes into the spec.
- **Telephony port:** place call, live two-way audio stream, clear playback, hang up, call status events (ringing, answered, busy, no-answer, failed), and an **optional** answering-machine signal.
- **Voicemail detection is our own and works on any route:** a first-seconds classifier (transcript phrases, beep detection, no-speech), with Twilio AMD used as an extra hint when available.
- **Recording is done by our voice server:** both sides from the media stream, uploaded to our object storage and aligned with the transcript and trace. Carrier or Twilio recording is not used.

## Answer

Settled with the owner 2026-09-27.

**Engineering and product own the build; the legal team owns compliance.**

- **Provider:** Twilio, all the way (development and production). The self-hosted SIP/media-server route (A) is dropped.
- **Caller ID:** getting a compliant UAE caller ID is handed to the legal team. The expected mechanism is Twilio BYOC with an e&/du trunk, since that needs no engineering change. It is tracked in ticket 18, with the carrier questions (SIP trunk on the trade licence, whether e&/du will connect to Twilio, cost, lead time).
  - **Go-live risk for the C-suite:** until then, calls go out with a foreign caller ID, which appears non-compliant with Res 56/2024 Art. 4.
- **Development:** plain Twilio, calling only the owner's and the team's own phones.
- **Region:** the voice server and provider calls are hosted in Europe (Dublin/Frankfurt) next to Twilio's IE1 Media Streams. The UAE-to-EU network latency (~100-150ms each way, to be measured) is part of the latency budget.
- **Telephony port**, implemented by the Twilio adapter:
  - place a call;
  - a two-way audio stream;
  - clear playback;
  - hang up;
  - status events (ringing, answered, busy, no-answer, failed);
  - an optional answering-machine signal.
- **Voicemail detection:** we own it, running in the voice server on the first seconds after answer. It combines a transcript classifier, a beep detector and a no-speech check. Twilio async AMD is used as an extra hint.
- **Recording:** the voice server records both sides from the media stream and uploads to our object storage, aligned with the transcript and trace. Twilio recording is not used.

## Amendment (2026-10-02, owner)

- **Audio path:** Twilio Elastic SIP Trunking → LiveKit SIP (no Media Streams).
- **Voicemail detection and recording:** still ours, via the LiveKit agent and LiveKit egress.
- **v2:** an e&/du SIP trunk can replace Twilio as the LiveKit outbound trunk.
