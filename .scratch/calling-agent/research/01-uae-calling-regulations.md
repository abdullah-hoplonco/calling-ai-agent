# UAE rules for outbound AI sales calls

Research for ticket [01-uae-calling-regulations](../issues/01-uae-calling-regulations.md). Researched 2026-09-25. This is research, not legal advice. Before launch, have a UAE lawyer confirm the points marked as interpretation.

## How to read this

- **Source says**: quotes or close paraphrases of the cited text.
- **Interpretation**: my reading of how the text applies to the Calling Agent.
- The official hosts (uaelegislation.gov.ae, moet.gov.ae, ai.gov.ae) blocked direct fetches from this environment (Cloudflare 403 or timeouts). The official English PDFs were therefore read from Internet Archive captures of the **same official URLs**. Those capture URLs are cited next to the canonical ones.

## Primary sources used

| Short name | Instrument | Canonical URL | Copy actually read |
|---|---|---|---|
| **Res 56** | Cabinet Resolution No. (56) of 2024 Concerning the Telemarketing Regulations (issued 10 June 2024) | https://uaelegislation.gov.ae/en/legislations/2519/download | http://web.archive.org/web/20240901045752id_/https://uaelegislation.gov.ae/en/legislations/2519/download |
| **Res 57** | Cabinet Resolution No. (57) of 2024 Concerning the Administrative Violations and Penalties for Acts Violating Res 56 | https://uaelegislation.gov.ae/en/legislations/2523/download | http://web.archive.org/web/20250418050409id_/https://www.uaelegislation.gov.ae/en/legislations/2523/download |
| **PDPL** | Federal Decree-Law No. (45) of 2021 Concerning the Protection of Personal Data | https://uaelegislation.gov.ae/en/legislations/1972/download | http://web.archive.org/web/20240803165005id_/https://uaelegislation.gov.ae/en/legislations/1972/download |
| **Penal Code** | Federal Decree-Law No. (31) of 2021 Promulgating the Crimes and Penalties Law | https://uaelegislation.gov.ae/en/legislations/1529/download | http://web.archive.org/web/20240524065455id_/https://uaelegislation.gov.ae/en/legislations/1529/download |
| **Cybercrime Law** | Federal Decree-Law No. (34) of 2021 On Countering Rumors and Cybercrimes | https://uaelegislation.gov.ae/en/legislations/1526/download | http://web.archive.org/web/20240707222217id_/https://uaelegislation.gov.ae/en/legislations/1526/download |
| **CBUAE TM Reg** | CBUAE Telemarketing Regulation, Art. 16 (financial institutions only) | https://rulebook.centralbank.ae/en/rulebook/article-16-automated-communication-systems-robocalls-and-artificial-intelligence-ai | fetched directly |

Timing: Res 56 and Res 57 each say they take effect 60 days after publication in the Official Gazette (Res 56 Art. 11; Res 57 Art. 7). Law-firm summaries give the in-force date as **27 August 2024** ([Pinsent Masons](https://www.pinsentmasons.com/out-law/news/uae-telemarketing-rules-ensure-businesses-operate-transparency-integrity)).

---

## 1. Does Res 56 apply to us at all?

**Source says**
- "Telemarketing" means "Phone Calls made by a company or a natural person to a Consumer for marketing, advertising or promoting the products or services they provide … through a landline or mobile number, including marketing text messages and marketing messages through social media applications." "Consumer" means a natural person. (Res 56 Art. 1)
- The resolution applies "to all companies licensed in the State, including those located in free zones, that market products or services through telemarketing." (Res 56 Art. 3(1))
- "Unwanted Marketing Phone Calls" means "Marketing Phone Calls made in violation of the provisions of this resolution, and do not include Marketing Phone Calls made at the request of the Consumer." (Res 56 Art. 1)

**Interpretation**
- A Qualification Call promotes the agency's services to a natural person, so it is a Marketing Phone Call. The agency is covered whether it sits on the mainland or in a free zone.
- The "at the request of the Consumer" wording is the strongest hook for warm Leads, but it is narrow. It only takes such calls out of the definition of *Unwanted* calls. It does **not** say they stop being Marketing Phone Calls, and Art. 4 and Art. 5 impose their controls on "Marketing Phone Calls" generally. The safe design is to **comply with every Art. 4 and Art. 5 control anyway** and treat the form request as extra protection, not as an exemption. Trench & Associates reads it more generously: "Firms will not be penalised for making phone calls initiated at the consumer's request" ([Trench Law](https://www.trenchlaw.com/new-telemarketing-rules-in-uae-timings-fines-exemptions-explained/)). That is one firm's view, and the text does not state it that way.

## 2. TDRA and telemarketing operating rules

All of the following come from **Res 56 Art. 4** (company obligations) and **Art. 5** (call controls), verbatim or close paraphrase.

| Topic | Source says | Clause |
|---|---|---|
| Prior approval | "Obtain prior approval to practice Phone Marketing activity from the Competent Authority." | Art. 4(1) |
| Training | Train marketers on professional ethics and "the basic principles of using the Do Not Call Registry (DNCR)." | Art. 4(2) |
| Numbers | "Use local Phone numbers issued by telecommunications companies licensed in the State, and these numbers shall be registered under the commercial licence of the Company." Also: "Do not use Phone numbers that are not registered or owned by the Company." | Art. 4(3), 4(13) |
| Opt-in channel | "Create a communication channel for Consumers interested in obtaining marketing information, and marketing communication is only made with these Consumers." | Art. 4(4) |
| DNCR | "Do not call for marketing products or services to Consumers whose numbers are listed on the DNCR." | Art. 4(5) |
| Call log | Keep a record of all Marketing Phone Calls "in accordance with the form prepared by the Competent Authority" and do not destroy it before the period that authority specifies. | Art. 4(6) |
| Recording | "Record Marketing Phone Calls, with the necessity of informing the Consumer of this recording when the call begins." | Art. 4(7) |
| Reporting | Submit periodic reports as the Competent Authority determines. | Art. 4(8) |
| Code of conduct | Sign a code of professional conduct if the Competent Authority issues one. | Art. 4(9) |
| Caller identification | "Identify the Company and the purpose of the call at the beginning of the marketing Phone Call." | Art. 4(11) |
| Data source | Disclose the source of Consumer numbers and data if the Competent Authority asks. | Art. 4(12) |
| No pressure | No "marketing methods that put unjustified pressure on the Consumer." | Art. 5(1) |
| No deception | "Avoid deception and misleading when marketing the product or service." | Art. 5(2) |
| Hours | "Make Marketing Phone Calls only during the period from 9:00 am to 6:00 pm." | Art. 5(3) |
| Rejection | "Do not call the Consumer back if he rejects the product or service on the first call." | Art. 5(4) |
| Retry cap | "Do not call the Consumer back, if he does not answer the call or ends the call, more than once a day and a maximum of twice a week." | Art. 5(5) |
| Automation | "Automated communication systems may be used for marketing, advertising and promoting the products or services provided by the Company in accordance with the provisions of this resolution." | Art. 5(6) |
| Permission to continue | "Ask the Consumer whether he wants to continue the Phone Call or not before starting to market, advertise and promote the product or service provided." | Art. 5(7) |

**Days of the week and public holidays**: Res 56 sets no restriction by day or holiday. It sets only the 9:00 to 18:00 window. (Absence confirmed by reading the full text.)

**Who is the "Competent Authority"?** Res 56 Art. 1 defines it as "the federal or local government agency concerned … with licensing or regulating economic activity." Art. 9(4) gives local authorities competence for non-financial telemarketing within each Emirate. Several law firms still write "prior approval from TDRA" ([Morgan Lewis](https://www.morganlewis.com/blogs/sourcingatmorganlewis/2024/07/telemarketing-in-an-evolving-legal-landscape-uae-adopts-regulations-on-telemarketing-activities), [Clyde & Co](https://www.clydeco.com/en/insights/2024/07/uae-tightens-telemarketing-regulations-what-you-ne)).
- **Interpretation**: under the text, the approval body is the agency's licensing authority. For a Dubai mainland company that is the Department of Economy and Tourism (DET), or the relevant free-zone authority. TDRA runs the DNCR. Enforcement evidence supports this reading: the Dubai Corporation for Consumer Protection and Fair Trade (part of DET) fined 159 companies AED 50,000 each and warned 174 ([Gulf News, 25 Feb 2025](https://gulfnews.com/business/markets/159-companies-fined-dh50000-each-for-uae-violating-telemarketing-rules-1.500045784)). I did **not** find the actual application procedure. See Open uncertainties.

**Numbers in practice**: Twilio's UAE terms say customers are "strictly prohibited from placing or attempting to place any outbound voice calls from a UAE Geographic Number via the Services or through any other means, such as a SIP Trunk" ([Twilio UAE number terms](https://www.twilio.com/en-us/legal/service-country-specific-terms/uae-phone-numbers), [Twilio UAE voice guidelines](https://www.twilio.com/en-us/guidelines/ae/voice)).
- **Interpretation**: a Twilio-issued UAE number cannot be the outbound caller ID. A foreign Twilio number would breach Art. 4(3) and 4(13), which carry a fine of AED 25,000 or more. The agency will likely need a number from a UAE-licensed operator (e& or du) registered to its trade licence, connected to Twilio through something like BYOC or an operator SIP trunk. Research ticket 02 ([02-twilio-uae-outbound](./02-twilio-uae-outbound.md)) covers feasibility.

## 3. Must an AI or automated caller disclose that it is an AI?

**Source says**
- Res 56 expressly **permits** automated communication systems for marketing, provided the rest of the resolution is followed (Art. 5(6)). Neither Res 56 nor Res 57 says anything about disclosing AI or automation. The only related violation in Res 57 is "Using automatic calling or marketing … in violation of provisions of this Resolution" (Table 1, item 16: AED 10k / 25k / 50k).
- Res 56 requires identifying the **Company** and the **purpose** at the start of the call (Art. 4(11)). It also forbids "deception and misleading" (Art. 5(2)).
- The PDPL has no AI-disclosure rule. It requires processing to be "fair, transparent and lawful" (Art. 5(1)). It gives a right to object to decisions based on automated processing "particularly those decisions which have legal impact on or adversely affect the Data Subject" (Art. 18(1)), with human review on request (Art. 18(4)).
- The CBUAE Telemarketing Regulation (Circular C 3/2026, in force 31/3/2026) covers **licensed financial institutions only**. Art. 16 covers robocall timing (connect within 2 s, drop unanswered calls within 15 s or 4 rings) and says "The use of artificial intelligence shall be subject to provisions of applicable laws and/or Regulations" ([CBUAE Rulebook Art. 16](https://rulebook.centralbank.ae/en/rulebook/article-16-automated-communication-systems-robocalls-and-artificial-intelligence-ai)). Pinsent Masons reports that under this regulation customers get a choice between human agents, robocalls and AI agents ([Pinsent Masons](https://www.pinsentmasons.com/out-law/news/telemarketing-rules-set-for-uae-financial-institutions)). **It does not apply to a marketing agency.** It does show which way UAE regulators lean.
- The UAE Charter for the Development and Use of AI (June 2024) includes a transparency principle. Latham & Watkins (30 Oct 2025) describes it as "non-binding" ([Latham](https://www.lw.com/en/insights/ai-in-the-uae-understanding-the-regulatory-landscape-and-key-authorities); charter page: https://uaelegislation.gov.ae/en/policy/details/the-uae-charter-for-the-development-and-use-of-artificial-intelligence).
- The new Federal Authority for AI and Data was announced on 14 June 2026. It absorbs the AI Office, TDRA's digital-government sector and the Emirates Data Office. The announcement mentions no disclosure obligations ([Morgan Lewis, June 2026](https://www.morganlewis.com/pubs/2026/06/uae-establishes-federal-authority-for-artificial-intelligence-and-data)).
- DIFC only: DIFC Data Protection Regulation 10 requires notice when personal data is processed by autonomous or semi-autonomous systems. It has been in force since Sept 2023, with full enforcement from 1 Jan 2026 ([Mayer Brown, Jan 2026](https://www.mayerbrown.com/en/insights/publications/2026/01/ai-regulation-in-the-difc-personal-data-processed-through-autonomous-and-semi-autonomous-systems)). This matters only if the agency is a DIFC entity.

**Interpretation**
- **No binding onshore federal rule found that requires a telemarketing call to volunteer that the caller is an AI.** The owner's policy (don't volunteer it, answer honestly if asked) appears lawful for an onshore or non-DIFC free-zone company.
- Denying being an AI when asked, or using a persona built to make the Lead believe they are talking to a human, is high-risk under the Art. 5(2) "deception and misleading" rule (Res 57 item 12: AED 25k / 50k / 75k) and PDPL Art. 5(1) "transparent" processing. "Answer honestly if asked" must be a hard guardrail.
- The Calling Agent has to identify the agency by name anyway (Art. 4(11)), so an AI persona name must not be presented as a separate company.
- If the agency is in DIFC, Reg 10 probably makes AI notice mandatory. Confirm where the agency is licensed.

## 4. Call recording consent

**Source says**
- Res 56 **requires** recording Marketing Phone Calls and informing the Consumer "when the call begins" (Art. 4(7)). Res 57 fines each failure separately: failing to record is AED 10k / 25k / 50k (item 6), and failing to notify at the start is AED 10k / 20k / 30k (item 7).
- Penal Code Art. 431 punishes "Eavesdropping, recording or transmitting by any device … conversations made … by way of telephone" when done "in other than the cases as permitted by law or without the consent of the victim". Recordings are confiscated and erased.
- Cybercrime Law Art. 44(1) punishes "recording … conversations" through IT systems "with the intention of invading the privacy … without his consent in cases other than those authorized by law", with at least 6 months' imprisonment and/or a fine of AED 150,000 to 500,000.

**Interpretation**
- Recording is not optional. Res 56 mandates it, so it is arguably a "case permitted by law" under Art. 431. Consent should still be secured: announce the recording in the opening line, and treat the Lead continuing after the announcement as consent. The web form can add express consent ("I agree to receive a call, which will be recorded"). If a Lead objects to recording, the agent should end the marketing call. It must not continue unrecorded, because that breaches Art. 4(7).
- Transcripts and LLM logs derived from the recording are PDPL personal data (section 5). "Voice" is expressly listed as an identifier in the PDPL definition of Personal Data.

## 5. PDPL: storing Lead PII, recordings and transcripts

**Source says (PDPL)**
- Scope: covers controllers in the UAE, and processing of UAE data subjects' data from abroad. It excludes "Companies and establishments located in free zones … and have special legislations regarding Personal Data protection" (Art. 2(1), 2(2)(g)). DIFC and ADGM are the free zones with their own regimes ([u.ae](https://u.ae/en/about-the-uae/digital-uae/data/data-protection-laws)).
- Personal Data includes data identifiable by "name, voice, image …". Sensitive data includes "biometric data" (Art. 1).
- Consent is the default lawful basis: "It is prohibited to process Personal Data without the consent of its owner", subject to exceptions (Art. 4). Among them: processing "necessary … to take measures at the request of the Data Subject with the aim of concluding … a contract" (Art. 4(9)).
- Valid consent must be "specific, clear and unambiguous … through a clear positive statement or action" (Art. 1). The controller must be able to prove it, it must be clear and easily accessible, and it must include the right to withdraw easily (Art. 6).
- Controls (Art. 5): specific purpose, data minimisation, accuracy, security, and "shall not be kept after the purpose of its processing has been exhausted" unless anonymised.
- Before processing, tell the data subject the purposes, the sectors or establishments the data is shared with inside and outside the UAE, and the cross-border protections (Art. 13(2), referring to 13(1)(b), (d), (g)).
- Right to object to and stop processing "for the purposes of direct marketing, including profiling related to direct marketing" (Art. 17(1)). Rights to correction and erasure (Art. 15), restriction (Art. 16), and a clear contact channel (Art. 19).
- Controller duties: security measures, a processing record, and processors with sufficient guarantees (Art. 7). Security includes encryption and pseudonymisation (Art. 20). Breaches must be notified to the Bureau and to affected data subjects (Art. 9).
- A DPIA is needed for high-risk new technology, including systematic automated assessment such as profiling "having legal consequences or serious impact" (Art. 21). A DPO is needed in some high-risk cases (Art. 10).
- Cross-border transfer is allowed to adequate jurisdictions (Art. 22). Otherwise it needs, among other routes, a contract imposing PDPL-equivalent measures, the data subject's "explicit consent", or necessity to perform a contract with or in the interest of the data subject (Art. 23).
- Penalties are left to a Cabinet decision (Art. 26). Executive Regulations were due within 6 months (Art. 28).
- **Status**: as of 10 March 2026, "The Implementing Regulations … have yet to be issued" and enforcement was "limited" ([Chambers Data Protection 2026 – UAE](https://practiceguides.chambers.com/practice-guides/data-protection-privacy-2026/uae/trends-and-developments)). Morgan Lewis (June 2026) says they "have still not been issued" ([Morgan Lewis](https://www.morganlewis.com/pubs/2026/06/uae-establishes-federal-authority-for-artificial-intelligence-and-data)).

**Res 56 overlap**: consumer personal data "may not be disclosed without his consent or to trade it for reprocessing" (Art. 6(4)). Res 57 item 18 fines this AED 50k / 75k / 150k, the top tier.

**Interpretation**
- Twilio, STT, LLM and TTS vendors are Processors. The agency is the Controller. Most of these vendors process outside the UAE, which is cross-border processing. The simplest compliant route is **explicit consent to cross-border processing in the web form**, plus Data Processing Agreements (Art. 23(1)(a)/(b)). Naming vendor categories and countries in the privacy notice covers Art. 13(2).
- Plain STT is probably **not** "biometric data" under the PDPL definition, because it is not used to identify or confirm the person's unique identity. Voice cloning or speaker identification would be. Do not add voiceprint or speaker-ID features.
- Retention: define a fixed period for recordings and transcripts, aligned with whatever period the Competent Authority sets for Art. 4(6) call records. Delete or anonymise Parked Leads' data when the purpose ends.
- The Calling Agent's Intent to Buy judgement only decides whether a Discovery Call gets booked. It is unlikely to be a decision with "legal impact" under Art. 18. Still, record it and let a Manager review it on request.

## 6. Does a web-form submission count as sufficient consent?

**Source says**: Res 56 Art. 4(4) (marketing only to Consumers who came through a channel for those "interested in obtaining marketing information"). Res 56 Art. 1 (calls "at the request of the Consumer" are not Unwanted). PDPL Art. 1 and Art. 6 (consent must be specific, a clear positive action, provable and withdrawable).

**Interpretation**: a web form fits the Res 56 model well, because it *is* the Art. 4(4) channel. Whether it amounts to valid PDPL consent depends on how the form is built. A phone field alone is weak. To be solid, the form should have:
1. An **unticked checkbox** (positive action) with specific wording, for example: "I'd like [Agency] to call me on this number about my project. Calls may be made by an automated/AI assistant and are recorded."
2. Mention of cross-border processing by service providers (PDPL Art. 23(1)(b)), and a link to the privacy notice (Art. 13(2)).
3. How to withdraw (Art. 6(1)(c)).
4. **Storage of consent evidence**: timestamp, IP address, form version or wording, and the phone number (Art. 6(1)(a); and Res 56 Art. 4(12), disclosing the data source on request).

Mentioning AI in the consent text is optional under the law as found. But it is cheap, and it largely removes the deception risk in section 3. The owner may want to weigh this against the "don't volunteer" preference.

**DNCR and warm Leads**: Art. 4(5) has **no stated exception** for consumers who asked to be called. **Interpretation**: a Lead on the DNCR who submitted the form may still be treated as off-limits under a strict reading. Screen every number against the DNCR (or rely on operator-side blocking, see Open uncertainties). If a number is listed, fall back to email or WhatsApp and ask the Lead to call in, or have the Manager call.

## 7. Penalties

**Source says (Res 57 Table 1, companies; AED for 1st / 2nd / 3rd offence)**

| # | Violation | Clause | Fine |
|---|---|---|---|
| 1 | No prior approval | Art. 4(1) | 75,000 / 100,000 / 150,000 |
| 2 | No training | Art. 4(2) | 10,000 / 25,000 / 50,000 |
| 3 | Numbers not registered to company licence | Art. 4(3) | 25,000 / 50,000 / 75,000 |
| 4 | Calling DNCR numbers | Art. 4(5) | 50,000 / 75,000 / 150,000 |
| 5 | No call register | Art. 4(6) | 10,000 / 25,000 / 50,000 |
| 6 | Not recording calls | Art. 4(7) | 10,000 / 25,000 / 50,000 |
| 7 | Not notifying recording at start | Art. 4(7) | 10,000 / 20,000 / 30,000 |
| 8 | No periodic reports | Art. 4(8) | 10,000 / 20,000 / 30,000 |
| 9 | Not identifying company and purpose at start | Art. 4(11) | 10,000 / 20,000 / 30,000 |
| 10 | Not disclosing data source on request | Art. 4(12) | 25,000 / 50,000 / 75,000 |
| 11 | Unreasonable pressure | Art. 5(1) | 10,000 / 25,000 / 50,000 |
| 12 | Fraud or deception | Art. 5(2) | 25,000 / 50,000 / 75,000 |
| 13 | Calling outside 9:00–18:00 | Art. 5(3) | 10,000 / 25,000 / 50,000 |
| 14 | Calling back after rejection | Art. 5(4) | 10,000 / 25,000 / 50,000 |
| 15 | Retries beyond 1/day, 2/week | Art. 5(5) | 10,000 / 25,000 / 50,000 |
| 16 | Automated calling in breach of the resolution | Art. 5(6) | 10,000 / 25,000 / 50,000 |
| 17 | Not asking whether the consumer wants to continue | Art. 5(7) | 10,000 / 20,000 / 30,000 |
| 18 | Disclosing or trading personal data without consent | Art. 6(4) | 50,000 / 75,000 / 150,000 |

Other sanctions under Res 57 Art. 3: a warning; total or partial suspension of activity for 7 to 90 days; "Cancellation of license and deletion from the commercial register, cutting communications services and removing the phone number". The authority may skip straight to the most severe penalty for a repeat within 6 months. Appeals must be filed within 15 days (Art. 6). Criminal exposure for unlawful recording: Penal Code Art. 431 and Cybercrime Law Art. 44 (section 4). PDPL fines are not yet set (Art. 26 decision pending).

Note: the table above is taken directly from the Res 57 text. Secondary summaries sometimes omit tiers or merge rows.

---

## Implications for the spec

Legal requirements (from the text). The first nine are near-certain; the rest are strongly implied.

1. **Opening script, in order**: (a) name the agency and give the purpose, e.g. "Hi, this is [name] calling from [Agency] about the website/app enquiry you submitted" (Art. 4(11)); (b) say the call is recorded (Art. 4(7)); (c) **ask whether they want to continue before any pitch** (Art. 5(7)). If they say no, end the call politely and mark the Lead so it is never called again.
2. **Calling window**: place calls only between 09:00 and 18:00 UAE time (GST, UTC+4). The dialer should refuse to start a call if the conversation could plausibly run past 18:00; a cut-off such as 17:45 is a design choice. No day-of-week rule, but keeping Sundays and holidays configurable is sensible.
3. **Retry policy**: after no answer, or the Lead ending the call, allow at most **1 attempt per calendar day and 2 per rolling week** (Art. 5(5)). Make this a hard limit in the scheduler.
4. **Rejection is terminal**: if the Lead rejects the service on the first call, never call again (Art. 5(4)). This maps to a Parked Lead with a "do-not-call" flag that re-nurturing cannot override for calls. Also honour PDPL Art. 17 objection to direct marketing.
5. **DNCR screening** before every campaign and every call. Store the result.
6. **Caller ID** must be a UAE number from a licensed operator, registered to the agency's trade licence. Twilio-native UAE numbers cannot be used for outbound calls (see ticket 02).
7. **Record 100% of calls**. If the Lead objects to recording, end the call. Keep a call register per the Competent Authority's form: timestamp, number, duration, outcome, recording reference, and consent-source reference (Art. 4(6), 4(12)).
8. **Honesty guardrail**: the agent must never deny being an AI or claim to be human. If asked, it confirms plainly and offers the Manager. No pressure tactics, no false urgency, no misleading claims (Art. 5(1), 5(2)).
9. **Web form consent**: unticked checkbox with specific wording covering phone call, recording, automated/AI assistant (recommended), and cross-border processors. Store proof of consent. Offer an easy withdrawal route.
10. **PDPL data handling**: privacy notice (purposes, processors, countries); DPAs with Twilio, STT, LLM and TTS vendors; encryption at rest; a fixed retention period for recordings and transcripts; deletion or anonymisation of Parked Leads after that period; processes for access, correction, erasure and objection; a breach-notification runbook.
11. **Organisational prerequisites** (not code): obtain telemarketing approval from the Competent Authority, train staff on ethics and DNCR, sign the code of conduct if issued, and prepare periodic reports.

## Open uncertainties

1. **Approval procedure**: which body approves (DET for Dubai mainland, or the specific free-zone authority), the application route, and turnaround. Not found in primary sources. The text says "Competent Authority" (the licensing body). Law firms say TDRA. **Action: ask the agency's licensing authority.**
2. **DNCR access for businesses**: how a company checks numbers (API, file, or operator-side blocking on registered telemarketing numbers) was not found in a primary source. **Action: ask e&/du when provisioning the number, and check TDRA's DNCR page.**
3. **Call-register form and retention period** (Art. 4(6)): the form and the retention period are set by the Competent Authority. Neither was found.
4. **"At the request of the Consumer" scope**: it is unclear whether form-requested calls fall outside Art. 4 and Art. 5 entirely. The spec assumes they do not.
5. **DNCR and a Lead who requested a call**: no explicit carve-out. Strict reading adopted.
6. **AI disclosure**: none found as of this date. This area is moving fast: the Federal Authority for AI and Data was announced on 14 June 2026. Check again before launch. If the agency is a **DIFC** entity, DIFC Reg 10 notice rules probably apply. I did not read the Reg 10 text directly; Mayer Brown is the source.
7. **PDPL Executive Regulations and penalties**: not issued as of June 2026, per secondary sources. Once issued they may add direct-marketing, retention and transfer rules. Check the Data Office / new Authority.
8. **Currency of the legal texts**: the PDFs read are Internet Archive captures from 2024–2025. I did not check for later amendments to Res 56 or 57, to Penal Code Art. 431, or to Cybercrime Art. 44. The official site blocked access from this environment.
9. **Recording consent**: whether announcing the recording and the Lead continuing is enough "consent" under Penal Code Art. 431 has not been confirmed by case law in this research. Express consent in the form reduces the risk.
