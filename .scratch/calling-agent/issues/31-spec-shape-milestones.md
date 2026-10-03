# Spec shape and MVP build milestones

Type: grilling
Status: resolved
Blocked by: 26, 27, 28, 29, 30
Map: ../map.md

## Question

How is the final spec structured, and how is the MVP sliced into build milestones (e.g. web demo → internal phone calls → soft launch → backlog)?

## Answer

Settled with the owner 2026-10-03.

**Deliverables**
- Engineering source of truth: this map, the tickets, the ADRs and `CONTEXT.md`.
- PDFs in professional blue, with the hoplonco.com logo and the byline "Research and report by Engr Abdullah Bukhari, Snr. SWE, HoplonCo". Written in ASD-STE100 only, skimmable, with plenty of visuals:
  - (a) **C-suite brief:** at most 2 pages, to read on their own;
  - (b) **Engineer onboarding guide:** the whole project.
- Order: PDFs first; the owner reviews the complete picture; build starts only after approval.

**Builder**
- The owner alone, using subagent-driven development, so the plan maximises parallel lanes.

**Milestones**
- **M0 Setup:** repo, Azure plus GPU quota, accounts, Terraform skeleton.
- **M1 Web demo:** "Talk to Omar" in the browser; state machine; text evals.
- **M2 Internal phone calls:** Twilio SIP to LiveKit, real bookings, recording, voicemail detection, LLM benchmark, voice pick.
- **M3 Platform:** ingestion, Lead lifecycle, dialer with pre-dial gate, 7 dashboard screens, Langfuse, judges, nightly audio evals.
- **M4 Soft launch:** blocked by legal (R1, R2); 10 → 25 Leads; judge calibration.
- **M5 Full operation.**

**Parallel lanes for subagents** (contracts first, then lanes run in parallel)
- **L0 Contracts (sequential, first):** domain model, ports, DB schema, OpenAPI, event types in `core/`.
- **L1 Agent:** LiveKit worker, prompts, turn tuning, tools.
- **L2 Evals:** harness, YAML scenarios, judges.
- **L3 Platform API:** FastAPI, Postgres, Celery, dialer, gate.
- **L4 Ingestion:** Excel, Gmail.
- **L5 Dashboard:** Next.js, built against a mocked OpenAPI.
- **L6 Infra:** Terraform, CI/CD, Langfuse, GPU/vLLM.
- **L7 Telephony:** Twilio SIP, voicemail detection, recording.

L1, L2, L3, L4, L5 and L6 start in parallel after L0; L7 starts after L1's first working agent.

