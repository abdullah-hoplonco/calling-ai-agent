# Product

<!-- impeccable:product-schema 1 -->

> Written 2026-10-04 from the repository (map.md, tickets, ADRs, PDFs) while the owner was away.
> The owner said "decide on your own". Lines marked _(inferred)_ were not confirmed in an interview.

## Platform

web

## Stack

Next.js (App Router, TypeScript) for `web/`, as decided in ticket 21. The voice worker is Python (LiveKit Agents) in `voice/`.

## Users

- **The owner** (Engr Abdullah Bukhari, Snr. SWE at Hoplon & Co): builds and tunes Omar, runs the demo, reads latency numbers to choose the production stack.
- **A junior engineer** who takes over the build: uses the demo page to see which stage the call is in and why Omar said what he said.
- **The C-suite** of Hoplon & Co: watch the demo once to decide whether to fund the build and go live. They need to understand the call in seconds. _(inferred: they see it in a meeting, on a shared screen or a laptop)_

## Product Purpose

Omar is an AI Calling Agent that phones warm Leads for Hoplon & Co (a Dubai web, app and digital-marketing agency), gives them the information they asked for, finds Intent to Buy, and books a Discovery Call with the Manager. The browser demo (milestone M1) lets a person play a Lead and talk to Omar with no phone network, and shows what the system does on every turn. Success: a believable conversation, the right outcome for each of the 7 demo scenarios, and measured reply delay of 0.9 s or less at p50.

## Positioning

Code owns the call; the LLM only writes the words (ADR 0001). The demo makes that visible: the call stage, the rules the code enforced, and the measured delay of each part of every reply. A hosted voice-agent demo cannot show those things.

## Operating Context

- Used in a desktop browser with a microphone and speakers or a headset. _(inferred: laptop, office light, sometimes on a projector)_
- One call at a time. A call lasts about 1 to 4 minutes.
- Data arrives live from the voice worker over LiveKit data messages (`omar.state`, `omar.latency`).
- Vocabulary from `CONTEXT.md`: Lead, Connected Call, Discovery Call, Intent to Buy, Qualified Lead, Parked Lead, Opted-out Lead, Manager.

## Capabilities and Constraints

- Free tiers only for the demo: LiveKit Cloud Build plan, Deepgram credit, Groq free tier (8,000 tokens a minute), Cartesia free plan (about 27 minutes of speech a month).
- Dummy Leads only. No real names or phone numbers.
- The calendar is fake in the demo (decision D1); the real Google Calendar comes in M2.
- No phone calls, dialer, database or dashboard in the demo.

## Brand Commitments

- Company name: Hoplon & Co (spoken "Hoplon and Co"). Logo: `docs/assets/hoplon-logo.png`.
- House style of the project documents: professional blue (navy `#0B2E6B`, blue `#1F5FBF`) and Noto Sans, from `docs/pdf-src/style.css`.
- Agent persona: Omar, client coordinator, male, neutral or light British accent (ticket 09).
- Writing for the team follows ASD-STE100 Simplified Technical English.

## Evidence on Hand

- Dummy Leads: `.scratch/calling-agent/assets/dummy-leads/` (3 form emails, a 62-row backlog). All synthetic.
- Agency knowledge sheet: `.scratch/calling-agent/assets/agency-knowledge.md` (draft, owner to review).
- No real call recordings, customers, benchmarks or measured latency exist yet. Do not invent them; the demo measures latency live.

## Product Principles

1. Show the mechanism: stage, rule and delay are visible, not hidden behind a chat bubble.
2. Measured, not claimed: every number on screen comes from a real turn.
3. The conversation comes first; the instrumentation explains it and never covers it.
4. Plain words a C-suite reader understands, with the engineering detail one step away.

## Accessibility & Inclusion

No product-specific standard was set. _(inferred: WCAG 2.1 AA as the floor; the call must be usable by keyboard, and live state must not rely on colour alone.)_
