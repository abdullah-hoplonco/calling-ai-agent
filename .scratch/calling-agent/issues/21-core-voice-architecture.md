# Core voice architecture (provider-agnostic)

Type: grilling
Status: resolved
Map: ../map.md

## Question

How is the custom system structured independent of provider choices: language/runtime per part, deployables and services (real-time voice server, API, workers, dialer, scheduler, ingestion, dashboard), the real-time pipeline shape and its adapter interfaces (telephony, STT, turn detection, LLM, TTS), how conversation control splits between code (state machine, compliance) and the LLM (language, tools), the agentic pattern (real-time agent vs post-call agents), interruption handling, and data storage/queues?

## Answer

Settled with the owner over two rounds (2026-09-26/27).

**Languages and frameworks**
- Python for the voice server and backend. FastAPI serves the app API and the voice server's HTTP/WebSocket endpoints.
- TypeScript + Next.js for the dashboard. It is a frontend only: all business logic and data access stay in FastAPI, with no Next API routes holding domain logic.

**Deployables and repo**
- Two deployables from one monorepo:
  - `voice/`: stateful, latency-critical, never restarted mid-call, may run in a different region.
  - `app/`: API, Celery workers and scheduler.
- Layout: `core/` (pure domain, state machine, ports), `voice/`, `app/`, `web/`, `evals/`, in a uv workspace for the Python parts. Adapters depend on `core/`; `core/` depends on nothing.

**Level of "custom"**
- The real-time orchestration (streaming loop, turn-taking, interruptions, state) is hand-written.
- Official vendor SDKs are used. Pipecat and LiveKit are reference reading only.

**Real-time pipeline**
- Telephony adapter → STT → TurnDetector → Conversation Controller → TTS → telephony.
- Every provider sits behind a port: telephony, STT, TurnDetector, LLM, TTS, calendar.
- The LLM port is our own thin interface (`stream_reply(messages, tools)` → tokens + tool calls), with one implementation per provider. No LiteLLM, LangChain or LangGraph on the live path.

**Conversation control**
- Code owns an explicit call state machine: Opening → Consent to continue → Info → Intent probe → Booking → Close, plus Parked, Callback and Voicemail.
- It is hand-written: typed enums, a transition table, pure functions, no I/O.
- The LLM generates language within a stage and calls tools.
- Code enforces the legal opening order, the ban on budget/timeline talk, and "no booking claim before the calendar confirms".

**Agentic pattern**
- One real-time conversational agent with tools.
- Offline post-call agents: outcome extraction, a pre-Discovery-Call summary for the Manager, Intent to Buy evidence, and compliance checks. These may use larger models.
- A live supervisor agent is deferred.

**Interruptions and turn detection**
- Our own VAD (e.g. Silero) detects barge-in fast; the vendor's end-of-turn signal marks turn ends. Both sit behind one TurnDetector interface.
- On barge-in: flush TTS, send Twilio `clear` (or its equivalent), and truncate the assistant message in history to the part the Lead actually heard.

**Concurrency**
- The voice server runs one asyncio process handling many calls, with CPU-heavy VAD work offloaded to a thread or process pool.
- A configurable cap limits concurrent calls, and the dialer checks it before starting a call.

**Storage and jobs**
- Postgres is the durable record.
- Redis holds the Celery broker, the dialer locks (no double calls, which matters legally) and the live call status published for the dashboard.
- Celery was chosen over async-native queues (owner's choice, for industry recognisability). Tasks are sync entry points that run async code via `asyncio.run` where needed. Scheduled retries inside calling hours use Celery `eta`/beat.
- Recordings live in S3-compatible object storage.

**Communication between deployables**
- The app calls the voice server's internal HTTP API (e.g. "start call for Lead X").
- The voice server records events to Postgres and/or sends webhooks back. No message broker until there is more than one voice server.

**Testing seam**
- A text adapter can replace telephony + STT + TTS, so the same controller, state machine and tools run against simulated Leads in plain text. This is a core architectural rule.

**Tracing**
- OpenTelemetry from day one. One trace per call, keyed on CallSid (or equivalent), spans the dialer job, each turn's STT/LLM/TTS stages, tool calls and post-call jobs.
- The trace backend is chosen in ticket 16.

## Amendment (2026-10-02, owner)

**The real-time orchestration is no longer hand-written.** It uses **LiveKit Agents** (open source) with LiveKit SIP; see ADR 0002.

- Still ours: the code-owned call state machine and guards (ADR 0001), the services, the data model and the deployables.
- Interruptions and turn detection now come from LiveKit:
  - its turn-detector model, or Deepgram Flux end-of-turn;
  - preemptive generation;
  - tuned endpointing delays.

**Turn detection (2026-10-02):**
- Default: Deepgram Flux's built-in end-of-turn.
- Alternative: LiveKit's turn-detector model.
- Pick by measured latency and false-interruption rate on simulated and test calls.
- Preemptive generation is on: the LLM drafts during the Lead's speech, and the draft is discarded if they keep talking. Preemptive TTS is evaluated too.
- Minimum endpointing delay starts at 0.3s and is tuned down with evals.
