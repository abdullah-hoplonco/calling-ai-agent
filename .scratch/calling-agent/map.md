# Map: Outbound Calling Agent MVP

Label: wayfinder:map

## Destination

A build-ready MVP spec for an outbound, English-language phone **Calling Agent** that calls warm **Leads** in the UAE for our web/mobile dev and digital marketing agency, gives them the info they asked for, detects **Intent to Buy**, handles objections consultatively, and books a **Discovery Call** on the Manager's Google Calendar at a mutually available time. Every decision in the spec is made and understood by the owner (a SWE learning applied AI engineering); the build doubles as a portfolio piece.

## Notes

- **Domain:** voice AI / telephony / sales automation, UAE market. Vocabulary lives in `/CONTEXT.md`; use its terms (Lead, Connected Call, Discovery Call, Intent to Buy, Qualified Lead, Parked Lead, Manager).
- **Skills:** grilling tickets call `grilling` + `domain-modeling`; research tickets call `research`; prototype tickets call `prototype`.
- **Build stance (amended 2026-10-02, ADR 0002):** built on **LiveKit Agents** (open source) + LiveKit SIP, with Twilio bridged over Elastic SIP Trunking; the call state machine, guards, data model, dialer and evals stay ours. Originally: fully custom build. Only telephony and third-party STT, TTS and LLM providers are external. Telephony is Twilio (ticket 17); the compliant caller ID is the legal team's job; the backend, frontend, real-time orchestration and agentic architecture are written by hand. No hosted voice-agent platforms (Vapi/Retell/Bland). Owner works in both JS/TS and Python.
- **Production-grade bar:** the spec should reflect what a competent applied AI engineer ships today: evals, observability, latency budgets, cost awareness, safety. Budget isn't a constraint, but costs must be visible.
- **Settled conversation rules (from charting):**
  - Tone is consultative and persuasive, never needy, desperate or aggressive.
  - The agent doesn't volunteer that it's an AI, but answers honestly if asked. Confirmed lawful by ticket 01 (outside DIFC). It must never deny being an AI or claim to be human.
  - It never says "a human" or "refer you"; it always says "connect you with my manager".
  - Budget and timeline are never discussed; they're deferred to the Discovery Call ("we can adjust budget and timeline to your needs; my manager will go through that with you. Should I book it?").
  - The accent is natural English.
- **Booking (settled):** during the call, the agent asks the Lead's availability, checks the Manager's Google Calendar in real time, and offers a few mutually available slots. If they can't agree, it sends a booking link. The Manager is a single calendar (the owner) for now. There's no live call transfer.
- **Ingestion (settled):** Excel/CSV import for the backlog and parsing of form-notification emails for new Leads. New Leads are called within minutes (speed-to-lead); the backlog is called on a planned schedule.
- **Unanswered calls (settled):** leave a voicemail in the MVP.
- **Qualification (settled):** Intent to Buy is the only criterion; Leads without it are Parked. The rules are expected to change, so keep them configurable.
- **Deliverable PDFs (2026-10-03):** `docs/HoplonCo-AI-Calling-Agent-Executive-Brief.pdf` (2 pages) and `docs/HoplonCo-AI-Calling-Agent-Engineer-Guide.pdf` (14 pages); sources in `docs/pdf-src/`. Awaiting owner approval before the build starts.
- **C-suite risk register:** every risk the C-suite must see lives in [risks.md](risks.md). Any ticket that surfaces or carries a risk adds a row there and a `C-suite risk:` line to its own file. The final spec presents the register in full.
- **Ownership split (2026-09-27):** this map covers engineering and product. Legal and compliance work (approval, caller ID via e&/du, DNCR, consent) goes to the legal team; the spec records each such item as a go-live risk rather than deciding it.
- **Owner decisions (2026-09-26):**
  - The research is good enough to plan on. UAE legal counsel (ticket 18) comes later, before go-live.
  - Backlog Leads are treated as callable, but the consent and fine risk must be raised clearly with the C-suite; the spec must carry that risk statement.
  - Dummy Lead data replaces the real samples for planning.
- **Demos before legal clearance:** a browser "talk to Omar" page (LiveKit web/WebRTC, no phone network) and Twilio test calls to the team's own phones only. WhatsApp calling is ruled out: WhatsApp voice calls are blocked in the UAE (TDRA VoIP policy).
- **Callback widget:** the site's "call within 55 seconds" widget will be replaced by the Calling Agent (owner, 2026-09-28). Removing it goes to the website team with the ticket 20 change request.
- **Market:** UAE for v1 (wider Middle East later).

## Decisions so far

<!-- one line per closed ticket: [title](issues/NN-slug.md): gist -->

- [Agent persona and opening line for the UAE market](issues/09-agent-persona-uae.md): Omar, male, neutral or light British accent, "client coordinator at Hoplon and Co"; legally ordered opening that references the Lead's form message; careful first, then warm and talkative; returns Arabic greetings, Parks Arabic-only Leads ("needs Arabic"); honest yes when asked if AI.
- [Telephony route for a UAE-compliant caller ID](issues/17-telephony-route-uae.md): Twilio for development and production, hosted in the EU next to Twilio IE1; the compliant caller ID (likely BYOC with e&/du) goes to the legal team as a go-live risk; own voicemail detection with Twilio AMD as a hint; our own two-channel recording.
- [Create dummy Lead data](issues/06-collect-lead-samples.md): 3 sample notification emails and a 62-row backlog.xlsx in `assets/dummy-leads/`; fields name, email, phone, message, submitted-at; deliberate mess (duplicates, 8+ phone formats, foreign numbers, missing emails, spam, Arabic-only messages, "don't call" notes in the message). Ingestion must normalise phones and dedupe, and the service is inferred from the message.
- [Call attempt, callback and voicemail policy](issues/10-call-attempt-voicemail-policy.md): call Mon-Thu 10:00-17:30 and Fri 10:00-12:00; 3 attempts (immediate, next day at the opposite time, +2 days), then Unreachable; voicemail on attempt 1 plus an email with the booking link; callbacks don't count as retries (max 2); a rejection makes the Lead Opted-out forever; callbacks to the number forward to the Manager.
- [Discovery Call slot-offering and fallback link rules](issues/11-discovery-call-slot-rules.md): Manager calendar on Hoplon's (very likely) Google Workspace via an Internal OAuth app; 30-minute Meet, Mon-Fri 10:00-18:00, 15-minute buffers, 2h to 7 days out; ask a preference, then offer 2 slots twice, then an emailed booking link; private prep brief kept out of the invite; confirm email by domain only.
- [Web form consent wording and evidence capture](issues/20-form-consent-and-evidence.md): a change request to the separate website team (consent checkbox with draft wording for legal, Service dropdown, stored evidence, parseable email); until then Leads are treated as "no recorded consent" (R3).
- [Gather agency knowledge the agent may share](issues/07-gather-agency-knowledge.md): knowledge sheet drafted from hoplonco.com in `assets/agency-knowledge.md` (9 core and 14 specialist services, 5-step process, contact facts); "must not say" list includes the site's own 24h, SEO-guarantee, award and compliance claims; owner to review the [GAP]/[VERIFY] items.
- [Backlog calling plan](issues/13-backlog-calling-plan.md): newest first, with new Leads always ahead; an old-Lead opening that names the month and topic; skip non-UAE numbers; call Arabic-only Leads with the "manager speaks English" offer; soft launch 10 (fully reviewed), then 25, then full; 30 dials a day, 2 concurrent, pause when fewer than 5 free slots.
- [Connected Call flow and objection playbook](issues/08-qualification-call-flow.md): code-driven stages (legal opening, then Info, Intent probe, Booking) validated in a clickable prototype; at least 2 rapport turns before asking; price questions and "can I talk to someone?" count as Intent to Buy; 2 objection attempts, then Park; declined recording → Parked; "booked" only after calendar confirmation.
- [Lead lifecycle and data model](issues/12-lead-lifecycle-data-model.md): Lead statuses including Invalid; one Lead per E.164 phone with many Submissions; Call Attempt vs Connected Call; the Manager marks each Discovery Call Attended/No-show/Won/Lost; append-only event log feeds the legal call register; 12-month default retention plus erase; manual Re-queue for Parked Leads.
- [Evaluation and observability strategy](issues/16-eval-observability-strategy.md): custom pytest harness with YAML scenarios and simulated Leads gating every PR; about 5 nightly real audio calls; Jev System-1 judges (escalating to an LLM when unsure) calibrated on 50 Manager-labelled calls; latency ≤1.2s p50 / ≤2.0s p95 as a starting point to recalibrate from real calls; Langfuse via OTel; every real call auto-graded, and failures become tests.
- [Select STT, TTS and LLM providers](issues/14-provider-selection.md): DeepSeek V4.1 Flash (non-thinking) on a US/EU host with Haiku 4.5 as backup; Deepgram Flux STT (AssemblyAI backup); Cartesia TTS (ElevenLabs backup); Jev judges escalating to Sonnet 5; Haiku as the simulated Lead; same-turn failover for LLM and TTS; ≈$1 per 3-minute call, ~90% of it Twilio.
- [All-UAE low-latency voice stack](issues/25-all-uae-low-latency-stack.md): Core42's Cerebras models run in the USA (and lack tool calling), so they're not a UAE option; managed UAE speech services (Azure) are slow; an all-UAE chain is fast (~0.5-0.7s) only with self-hosted STT, LLM (e.g. Qwen3.8-27B, non-thinking) and TTS on UAE GPUs plus an e&/du SIP trunk (unconfirmed); the current plan is estimated at ~1.4-1.7s; most of the gain comes from a faster LLM and co-located TTS.
- **Owner decision 2026-10-02: Option C v1.** Everything in Ireland/EU (Twilio IE, Deepgram EU, Cartesia EU), the live LLM self-hosted (Qwen3.8-27B) on a rented GPU in Dublin pending the benchmark; LiveKit Agents replaces hand-written orchestration (ADR 0002). All-UAE is v2.
- [Provider adapters and deployment](issues/15-voice-pipeline-architecture.md): Azure North Europe for v1 (UAE North for v2), with Terraform, Container Apps, a GPU VM for Qwen next to the LiveKit agents, Postgres Flexible, Managed Redis, Blob, Key Vault and LiveKit Cloud EU; draining deploys; per-turn latency target ~0.6-0.8s; config split between git (prompts) and the DB (operations); local, staging and prod; GitHub Actions CI/CD.
- [Dashboard screens for the MVP](issues/26-dashboard-screens.md): seven screens (Home, Leads, Calls, Campaigns, Discovery Calls, Settings, Quality); Google sign-in, admin only, no RBAC; no live listening in v1.
- [Mid-call failure handling](issues/27-mid-call-failure-handling.md): same-turn LLM and TTS failover; an STT failure triggers "bad line, I'll call you back" plus a callback counted as a retry; total failure pauses the dialer; alerts by email/Slack.
- [Lead email ingestion mechanism](issues/28-lead-email-ingestion.md): Gmail API push with a 1-minute polling safety net; strict parser with LLM fallback; dedupe by message ID; a "Needs review" list for unparseable emails.
- [Security and abuse guardrails](issues/29-security-abuse-guardrails.md): minimal tools; Omar laughs off prompt-injection attempts and returns to topic; 10-minute call cap; PII masked in logs; self-hosted Langfuse; kill switch plus locks.
- [Compliance hooks in the product](issues/30-compliance-hooks.md): a pre-dial gate (DNCR list, opt-outs, window, retries), call register CSV, PDPL erase/export, consent evidence fields; the legal team supplies the rules.
- [Spec shape and MVP build milestones](issues/31-spec-shape-milestones.md): a 2-page C-suite PDF and an engineer onboarding PDF (blue, STE, visual); milestones M0-M5 (M4 blocked by legal); 8 parallel lanes for subagent-driven build after a contracts-first L0.
- [Core voice architecture (provider-agnostic)](issues/21-core-voice-architecture.md): Python/FastAPI backend + Next.js dashboard; two deployables (voice server, app) in one monorepo with a pure `core/`; hand-written real-time orchestration behind ports; code-owned call state machine with the LLM inside stages; one live agent plus offline post-call agents; own VAD + vendor end-of-turn; asyncio voice server; Postgres + Redis + Celery; text-mode testing seam; OTel trace per call.

- [UAE rules for outbound AI sales calls](issues/01-uae-calling-regulations.md): Res 56/57 of 2024 apply to all companies; calls only 09:00-18:00, max 1 retry a day and 2 a week, stop after a rejection, DNCR check, mandatory recording with notice; opening order is company and purpose, then recording notice, then "do you want to continue?"; local e&/du caller ID on the trade licence; prior approval; no up-front AI-disclosure duty (except DIFC), but never deny being an AI; PDPL needs explicit form consent covering calls, recording and overseas processors. Fines AED 10k-150k.
- [Google Calendar API for live availability and booking](issues/04-google-calendar-booking-api.md): freeBusy + backend slot generation (Asia/Dubai, UTC+4 fixed); events.insert with sendUpdates=all and an idempotent event id; Meet via conferenceData; OAuth refresh token (personal Gmail) or Internal app / DWD (Workspace); fallback link = hand-made appointment-schedule page stored as config; Lead email must be captured on the call.
- [Production evaluation and observability practices for voice agents](issues/05-voice-agent-evals-observability.md): two-tier evals (text-mode simulated Leads per PR, nightly real-audio calls); binary per-failure-mode judges validated against human labels, code-checked outcomes first; per-stage latency percentiles (target ~800-900ms median turn gap); OTel traces keyed on CallSid; per-call cost ledger.
- [Twilio outbound calling into the UAE](issues/02-twilio-uae-outbound.md): Twilio reaches UAE numbers but only with a foreign caller ID; Cabinet Resolution 56/2024 appears to require local UAE-licensed numbers for marketing calls (plus 09:00-18:00, DNCR, recording disclosure, retry caps). ~$0.30/min to UAE mobiles; async AMD; Media Streams via IE1, so no Middle East edge. Telephony route re-opened, see the Telephony route ticket.
- [Real-time STT, TTS and LLM options for a custom voice pipeline](issues/03-realtime-speech-stack-options.md): STT finals ~250-370ms (AssemblyAI, Deepgram, Soniox, Speechmatics, Cartesia), TTS Cartesia (most natural) / ElevenLabs Flash (fastest), voice-to-voice latency is roughly LLM time-to-first-token + 500ms (Haiku 4.5 ~1.1s); no independent UAE-accent data, so a bake-off is needed; custom pipeline ~$0.03-0.10/min before telephony; bookings must be confirmed in code, never trusted to the LLM's word.

## Not yet specified

<!-- All fog graduated 2026-10-03: the remaining patches became tickets 26-31; the rest was settled by tickets 12, 14, 15 and 16. -->

## Out of scope

- ⚠ **C-suite: go-live blockers owned by the legal team.** These are off this map's route but must be presented (see [risks.md](risks.md)):
  - [Confirm telemarketing approval path and warm-lead exemption](issues/18-uae-legal-approval.md): approval, DNCR procedure, call register, recording consent, DIFC status (R2, R4, R5, R7, R9).
  - [Ask e& and du about a business SIP trunk](issues/22-ask-carriers-sip-trunk.md): compliant caller ID via Twilio BYOC (R1).
- [Record accent test clips](issues/19-accent-test-clips.md): skipped; Omar uses international English and STT accent accuracy is judged on real calls (T1 accepted).

- CRM updates after calls (v2).
- Second language(s) (v2).
- Inbound calls (later; choices should not preclude them).
- Productizing for clients: multi-tenant, self-serve, billing (later).
- WhatsApp audio and text follow-ups after missed calls (later).
- Website form webhook ingestion (later; the MVP uses email parsing and Excel import).
- Live call transfer to the Manager.
- **All-UAE stack (v2):** e&/du SIP trunk + self-hosted STT/LLM/TTS in Azure UAE North (~0.5-0.7s); depends on the legal team's trunk (R1) and Enterprise licences. See [All-UAE low-latency voice stack](issues/25-all-uae-low-latency-stack.md).
- Moving the Lead journey (retries, callbacks) to Temporal durable workflows: possible v2. The MVP keeps Celery (owner confirmed 2026-09-27), with retry and callback logic kept isolated so it can move later.
