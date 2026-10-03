# Twilio outbound calling into the UAE — findings

Ticket: [02-twilio-uae-outbound](../issues/02-twilio-uae-outbound.md)
Researched: 2026-09-25. Prices and guidelines change without notice; re-check before committing.

## TL;DR

Twilio can **technically** terminate calls into UAE mobiles and landlines. But it can only do it with a **foreign (non-UAE) caller ID**, and it **cannot sell a UAE number that is allowed to call out**. UAE law (Cabinet Resolution No. 56 of 2024) requires marketing calls to go out on **local numbers issued by a UAE-licensed telco and registered under the company's trade licence**. So plain Twilio outbound is very likely **non-compliant** for Qualification Calls, which count as telemarketing (see caveats below). Everything else on the Twilio side fits the architecture well: Media Streams, AMD, pricing, and an Ireland (IE1) media region. The realistic paths are (a) a UAE-licensed carrier (e& or du) number or SIP trunk connected to Twilio through **BYOC**, if the carrier allows it, or (b) a UAE-licensed carrier or CPaaS that offers real-time media streaming directly.

---

## 1. Can Twilio reach UAE mobile and landline numbers?

- Yes. Twilio's UAE voice guidelines list outbound **International** reachability as **"Yes"**, meaning calls from Twilio to UAE PSTN numbers. Domestic (in-UAE) outbound is "N/A". Source: https://www.twilio.com/en-us/guidelines/ae/voice
- Outbound caller ID: "Outbound call preserves sent Caller-ID", in **+E164** format for international calls. Domestic caller ID is "N/A". Source: https://www.twilio.com/en-us/guidelines/ae/voice
- Twilio does not guarantee caller ID. Per its support article, Twilio guarantees local caller ID only for +1 destinations and "cannot guarantee local Caller ID in other countries". Some countries require the caller ID to be changed so the call gets delivered. Source: https://support.twilio.com/hc/en-us/articles/223132227-Local-Caller-ID-CLI-international-compatibility (seen via search snippet; the page returned 403 to direct fetch).
- **No UAE-specific "outbound requirements" or "best practices"** are published. Both show "N/A". Source: https://www.twilio.com/en-us/guidelines/ae/voice
- Emergency calls over Twilio are not allowed in the UAE. Source: same page.

**Reliability (not documented by Twilio, so uncertain):** The UAE guideline page does not describe how e& or du treat international-CLI calls that hit a mobile. Industry sources say regulators worldwide increasingly block in-country CLIs that originate abroad, and third-party CLIs too. Telnyx, for example, warns that "calls with a matching foreign CLI are the most likely to be blocked": https://support.telnyx.com/en/articles/3546251-caller-id-number-policy. **Do not present a UAE number as caller ID on an international route.** Use a genuine non-UAE Twilio number, such as a US or UK number. Expect answer rates for foreign numbers to be lower in general. Anecdotally, UAE recipients distrust foreign numbers, but no primary data was found.

## 2. UAE caller IDs and numbers on Twilio

- The only number type Twilio lists as available for the UAE is **toll-free (+971 800)**. Source: https://www.twilio.com/en-us/guidelines/ae/regulatory
- Twilio's UAE number terms say:
  - "(c) A UAE Geographic Number will only be used to receive inbound voice calls. Customer is strictly prohibited from placing or attempting to place any outbound voice calls from a UAE Geographic Number via the Services or through any other means, such as a SIP Trunk."
  - Toll-free numbers may not be resold or passed to third parties, and "Voice calls placed by Customer to a UAE Toll-Free Number must terminate in the United Arab Emirates."
  - Sources: https://www.twilio.com/en-us/legal/service-country-specific-terms/uae-phone-numbers and https://www.twilio.com/en-us/guidelines/ae/voice
- The guideline table shows only inbound use for UAE toll-free numbers. Nothing says a UAE toll-free number can be used as the outbound caller ID. Treat UAE Twilio numbers as **inbound-only** (for example, a callback line).
- For the `From` of an outbound call, Twilio requires "a Twilio number or a Verified outgoing caller id for your account." Source: https://www.twilio.com/docs/voice/api/call-resource. A verified e& or du mobile or landline could in theory be set as caller ID. But Twilio would carry it over an international route, which is exactly the "in-country CLI from abroad" pattern that carriers block. Its legal status under Resolution 56 is also doubtful (see section 3). **Not recommended; unverified.**

## 3. Regulatory requirements (Twilio bundle and UAE law)

### Twilio regulatory bundle
- UAE toll-free: individual or business name plus an address (anywhere in the world), and either an executed Letter of Authorization or no documents, as listed. Source: https://www.twilio.com/en-us/guidelines/ae/regulatory
- **No bundle is needed just to call UAE numbers** from a non-UAE Twilio number. The bundle requirements for that number's own country apply. For example, a US local number needs no bundle, while a UK number needs one (not researched here).

### UAE telemarketing law — the constraint that decides the design
Primary source: Cabinet Resolution No. (56) of 2024 on the Telemarketing Regulations, official English text on the Ministry of Economy site: https://www.moet.gov.ae/documents/20121/0/English+%D9%82%D8%B1%D8%A7%D8%B1+%D9%85%D8%AC%D9%84%D8%B3+%D8%A7%D9%84%D9%88%D8%B2%D8%B1%D8%A7%D8%A1+%D8%B1%D9%82%D9%85+56+%D9%84%D8%B3%D9%86%D8%A9+2024+%D8%A8%D8%B4%D8%A7%D9%94%D9%86+%D8%AA%D9%86%D8%B8%D9%8A%D9%85+%D8%A7%D9%84%D8%AA%D8%B3%D9%88%D9%8A%D9%82+%D8%B9%D8%A8%D8%B1+%D8%A7%D9%84%D9%85%D9%83%D8%A7%D9%84%D9%85%D8%A7%D8%AA+%D8%A7%D9%84%D9%87%D8%A7%D8%AA%D9%81%D9%8A%D8%A9.pdf/8a81f5d0-ab74-b8a2-653b-657bf9b2544f?t=1725007365303 (also on https://uaelegislation.gov.ae/en/legislations/2519). Issued 10 June 2024, in force 60 days after publication (27 Aug 2024 per https://www.clydeco.com/en/insights/2024/07/uae-tightens-telemarketing-regulations-what-you-ne).

- **Art. 1, definition:** Telemarketing means "Phone Calls made by a company … to a Consumer for marketing, advertising or promoting the products or services they provide". "Unwanted Marketing Phone Calls … do not include Marketing Phone Calls made at the request of the Consumer." A Consumer is a natural person.
- **Art. 3, scope:** "all companies licensed in the State, including those located in free zones".
- **Art. 4, obligations** (the ones that matter here):
  - (1) prior approval from the Competent Authority to carry out phone marketing
  - (3) "Use local Phone numbers issued by telecommunications companies licensed in the State, and these numbers shall be registered under the commercial license of the Company"
  - (13) "Do not use Phone numbers that are not registered or owned by the Company licensed in the State to make Marketing Phone Calls"
  - (5) do not call numbers on the DNCR (Do Not Call Register)
  - (6) keep a record of all marketing calls
  - (7) "Record Marketing Phone Calls, with the necessity of informing the Consumer of this recording when the call begins"
  - (11) identify the company and the purpose of the call at the start
- **Art. 5, controls:**
  - (3) calls only between **9:00 am and 6:00 pm**
  - (4) do not call back after a rejection on the first call
  - (5) after no answer or a hang-up, call back no more than **once a day and twice a week**
  - (6) "**Automated communication systems may be used**" in line with the resolution
  - (7) ask whether the consumer wants to continue before starting to market
- **Penalties** (Cabinet Resolution No. 57 of 2024, per a law-firm summary): AED 50k, then 75k, then 150k for repeated violations, plus possible suspension or licence cancellation. Source: https://www.clydeco.com/en/insights/2024/07/uae-tightens-telemarketing-regulations-what-you-ne (secondary; primary text of Res. 57 not read).

### UAE VoIP licensing (TDRA)
- TDRA FAQ: "Licensees are allowed to provide VoIP Services in the UAE… Third parties can also provide VoIP services in the UAE (1) in collaboration with the licensees or (2) by obtaining an approval from TDRA". Also: "international telecom providers are not licensed in the UAE to provide VoIP Services, thus they have to work in collaboration with a Licensee to terminate any VoIP traffic to the UAE." Source: https://tdra.gov.ae/en/FAQs
- Twilio terminating over international interconnects with e& and du fits that model. What it does **not** give you is a UAE-licensed caller ID, which Art. 4(3) requires.

## 4. Pricing to the UAE (Twilio pay-as-you-go list prices)

Source: https://www.twilio.com/en-us/voice/pricing/ae

| Item | Price |
|---|---|
| Outbound to UAE **mobile** | **$0.2995/min** |
| Outbound to UAE local (landline) | $0.3635/min |
| Media Streams | $0.0044/min |
| Answering Machine Detection | $0.0075/call |
| Call recording | $0.0025/min (plus storage) |
| Voice Insights advanced | $0.0024/min |
| UAE numbers | "from $1.00/mo" (toll-free only; inbound) |

The same AMD and Media Streams prices appear on the US page, where a US local number (usable as a foreign CLI) is $1.15/mo: https://www.twilio.com/en-us/voice/pricing/us

**Rough cost of a 3-minute Qualification Call to a mobile:** 3 × ($0.2995 + $0.0044 + $0.0025) + $0.0075 ≈ **$0.93**, before STT, LLM and TTS costs. The UAE termination rate makes up about 97% of the Twilio cost, so BYOC through a local carrier could change the economics a lot.

## 5. Answering machine detection (AMD)

Source: https://www.twilio.com/docs/voice/answering-machine-detection

- Modes:
  - `MachineDetection=Enable` returns `human`, `machine_start`, `fax` or `unknown` as soon as it knows.
  - `DetectMessageEnd` waits for the greeting to end and returns `machine_end_beep`, `machine_end_silence`, `machine_end_other`, `human`, `fax` or `unknown`.
- Tuning parameters (default in brackets):
  - `MachineDetectionTimeout` 3–59 s (30)
  - `MachineDetectionSpeechThreshold` 1000–6000 ms (2400)
  - `MachineDetectionSpeechEndThreshold` 500–5000 ms (1200)
  - `MachineDetectionSilenceTimeout` 2000–10000 ms (5000)
- `AsyncAmd=true` lets the call run while AMD works in the background, with the result posted to `AsyncAmdStatusCallback`. Async AMD is only for Calls API outbound calls. Source: https://www.twilio.com/docs/voice/answering-machine-detection-faq-best-practices
- **Latency:** with default settings, AMD "return[s] results within ~4 seconds after the call was answered". Synchronous AMD "introduces several seconds in silence for the callee since the call is not connected until AMD detection has executed". Twilio recommends async. Source: https://www.twilio.com/docs/voice/answering-machine-detection-faq-best-practices
- **Accuracy:**
  - The model was trained mainly on US calls. "94% accuracy" is quoted for US and Canada, and DetectMessageEnd is "close to 100%" for US destinations.
  - For international calls, accuracy "may be slightly reduced because the tones emitted by voicemail boxes … may be distinct in other countries". Tuning may be needed.
  - No UAE data exists.
  - Sources: https://www.twilio.com/docs/voice/answering-machine-detection-faq-best-practices and https://www.twilio.com/en-us/blog/products/launches/introducing-new-answering-machine-detection-html
- UAE mobile voicemail greetings (e& and du) are often in Arabic and/or English carrier prompts. Expect to tune AMD, or to add your own detection inside the voice server as a backstop, for example transcribing the first 2–3 s and classifying it.

## 6. Media Streams (bidirectional WebSocket)

Sources: https://www.twilio.com/docs/voice/twiml/stream and https://www.twilio.com/docs/voice/media-streams/websocket-messages

- **Bidirectional needs `<Connect><Stream>`**. `<Start><Stream>` is one-way only. Twilio does not run the TwiML that follows `<Connect><Stream>` until your server closes the WebSocket. That gives a clean hand-back point, for example `<Dial>` the Manager after the socket closes.
- Protocol: **`wss` only**. Custom `<Parameter>`s are allowed (name plus value under 500 characters each). `statusCallback` reports stream start and stop.
- Audio: **`audio/x-mulaw`, 8000 Hz, mono, base64**, with no file headers, in both directions.
- Messages from Twilio: `connected`, `start` (includes callSid, streamSid, custom parameters), `media` (track, sequence number, timestamp, payload), `dtmf`, `mark`, `stop`.
- Messages to Twilio:
  - `media` — buffered and "played in the order received"
  - `mark` — echoed back once the audio before it has played; used to track barge-in and playback position
  - `clear` — empties the playback buffer and returns pending marks; used for **interruption (barge-in)**
- **Region and latency:** Media Streams run on Twilio Media Engines in **IE1 (Ireland)** and **AU1** as well as US1 (changelog, 23 Apr 2024): https://www.twilio.com/en-us/changelog/media-streams-available-in-ie1-and-au1
  - Twilio edge locations include Frankfurt, Dublin and Singapore. **There is no Middle East edge or region.** Source: https://www.twilio.com/docs/global-infrastructure/edge-locations
  - For UAE calls, use the **IE1** region, and host the voice server in or near Ireland or Frankfurt to keep the Twilio-to-server leg short.
  - The PSTN leg (UAE to Twilio in the EU) is unavoidable with Twilio.
  - Some features are not available in IE1 (for example `<Connect><VirtualAgent>`, `<Start><Siprec>`). Media Streams is available there. Whether AMD is supported in IE1 was not confirmed. Source: https://www.twilio.com/docs/global-infrastructure/regional-product-and-feature-availability

## 7. BYOC (connecting a UAE carrier to Twilio)

Source: https://www.twilio.com/docs/voice/bring-your-own-carrier-byoc and https://www.twilio.com/docs/voice/api/call-resource

- BYOC trunks connect your own PSTN carrier to Twilio Programmable Voice over SIP. Outbound calls go through it via the Calls API `Byoc` parameter, or `<Dial><Number byoc="…">`. TwiML (and so `<Connect><Stream>`) runs on these calls as with any Programmable Voice call.
- On paper, this is the Twilio-native way to satisfy Art. 4(3): the number and the termination belong to e& or du, and Twilio only provides call control and media streaming.
- **Unverified:** whether e& or du will deliver a business SIP trunk to a cloud SBC outside the UAE (Twilio's SIP edges are in the EU, US or APAC), and whether TDRA allows it. Industry sources say UAE SIP trunks are usually delivered to on-premises or in-country equipment. Example (non-primary): https://cloud-call-center.ae/2025/05/28/etisalat-sip-trunk/. This has to be asked of e& or du directly.

---

## Implications for the spec

1. **Treat compliance as the constraint that decides the design, not an add-on.** Qualification Calls promote the agency's services to natural persons, so Resolution 56 probably applies. The "at the request of the Consumer" exception only removes calls from the *unwanted* category. The Art. 4 obligations (licensed local number, recording, disclosure) are written for all Marketing Phone Calls. The spec should assume they apply until a UAE lawyer says otherwise.
2. The Calling Agent's telephony layer should sit behind a **carrier-agnostic interface** (place call, stream audio, hang up or transfer). Then Twilio (foreign CLI, for development and pilots) and a UAE-licensed route (BYOC or a local CPaaS) can be swapped without touching the voice server.
3. Build these into the spec as hard rules:
   - a calling window of **09:00–18:00 Asia/Dubai**
   - retry limits of **at most 1 retry per day and 2 per week** after no answer or hang-up
   - **never call again after a rejection** (fits the Parked Lead concept: no automatic re-dial)
   - a **DNCR check** before dialling
   - **call recording with a disclosure at the start**
   - an opening line that **names the agency and the purpose of the call**
   - asking **"do you want to continue?"** before pitching
   - a **call log** in the Competent Authority's format
4. The audio pipeline must accept **8 kHz μ-law** in and out: resample for STT, and have TTS output μ-law 8k or convert it. Barge-in uses `clear` plus `mark`.
5. Run Twilio in the **IE1** region and put the voice server, STT, LLM and TTS endpoints in the EU (Dublin or Frankfurt) to minimise round-trip time.
6. Use **Async AMD** (or none) plus a detector in the voice server. Never use synchronous AMD: it adds about 4 s of silence at the start of a warm-lead call.
7. Budget about **$0.30/min for UAE mobile termination** on Twilio, which is the largest per-minute cost.
8. Use UAE Twilio numbers only as an **inbound callback line** (toll-free). Outbound caller ID has to come from somewhere else.

## Open uncertainties

- Whether warm-lead callbacks (a Lead who asked to be contacted) are fully exempt from Art. 4(3), the local-number rule. **Needs UAE legal advice.** Also the exact "prior approval" process for the agency's emirate (Art. 4(1), Art. 9(4) local authorities).
- Real answer and block rates at e& and du for calls from Twilio with a US, UK or other foreign CLI. No primary data exists. Run a small pilot and measure it with Voice Insights.
- Whether e& or du will provide a SIP trunk or DIDs that terminate on Twilio BYOC (a foreign cloud), and their per-minute rates.
- Whether AMD is available in the IE1 region, and how accurate it is against UAE carrier voicemail.
- The Twilio help-center pages on caller-ID guarantees and "International Voice Quirks" returned 403 errors. The claims taken from them rest on search snippets.
- The text of Cabinet Resolution No. 57 of 2024 (penalties) was not read in primary form.

## Alternatives if Twilio does not fit

| Option | What it solves | Notes / uncertainty |
|---|---|---|
| **e& (Etisalat) business SIP trunk or DIDs** → own SBC or media server (for example FreeSWITCH or Asterisk, or LiveKit/Pipecat SIP) hosted **in the UAE** (AWS me-central-1, Azure UAE North, G42/Khazna) | Licensed local CLI registered to the trade licence; lowest latency (media stays in-country) | Must buy e& enterprise SIP. Needs an in-country SBC. You build the media-streaming bridge yourself. https://www.etisalat.ae/en/enterprise-and-government/enterprise-solutions/unified-communications.html |
| **du business SIP trunk** | Same as above | Same caveats |
| **Twilio BYOC + e&/du trunk** | Keeps the Twilio API, Media Streams and AMD, with a local CLI | Depends on the carrier agreeing to connect to a foreign SIP endpoint (unverified) |
| **Unifonic Voice** (GCC CPaaS) | Regional presence; lists "SIP trunking/BYOC" and programmable voice | Its page does not mention UAE local CLI or real-time media streaming. https://www.unifonic.com/en/channels/voice |
| **Infobip Calls API** | Programmable voice API; dedicated caller ID requires an Infobip voice number | Real-time media streaming, UAE number availability and outbound CLI not verified. https://www.infobip.com/docs/voice-and-video/calls |
| **Telnyx / Vonage / Plivo** | Twilio-like APIs with media streaming | Same foreign-CLI problem as Twilio. Telnyx says UAE local numbers are not available. Vonage's UAE restrictions page returned 403. https://telnyx.com/phone-numbers/united-arab-emirates |
| **Hosted voice-AI platforms (Retell, Vapi, etc.)** | Faster to build | Some block AE outright. For example, Retell-managed numbers: "Call country not supported: AE" (Sept 2026): https://community.retellai.com/t/uae-outbound-calls-blocked-with-telnyx-byot-call-country-not-supported-ae/3597 |
