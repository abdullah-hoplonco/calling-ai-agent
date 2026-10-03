# Voice agent evals and observability: current practice (as of 2026-09-25)

Ticket: [05-voice-agent-evals-observability](../issues/05-voice-agent-evals-observability.md)

Scope: what a production-grade evaluation and observability setup looks like for a cascaded (Twilio + streaming STT, LLM, TTS) outbound Calling Agent that runs Qualification Calls. Sources are framework docs (Pipecat, LiveKit), specs (OpenTelemetry GenAI), lab guidance (Anthropic, OpenAI), practitioner writing (Hamel Husain), papers (tau-Voice, GAUGE), and vendor engineering blogs (Twilio, Daily, Coval, Hamming, Cekura). Vendor blogs are labeled as such: they are primary for the vendor's own product and practice, but their benchmark numbers are self-reported.

---

## 1. Simulated callers

**The pattern is now built into both big open-source frameworks.** An LLM plays the caller, given a persona and a goal. The real agent runs with its real prompt and tools. A judge then decides whether the call succeeded.

- **Pipecat Evals** (added in Pipecat 1.4.0, released 2026-06-17; extended in 1.11.0, released 2026-09-18, dates from the GitHub releases API) has two scenario kinds in YAML. *Scripted* scenarios (`turns:` with `user:` / `expect:`) assert exact behavior after each turn. *Simulated* scenarios (`persona:`, `goal:`, `success:`, `metrics:`) hand the caller side to an LLM. Assertions include `text_contains`, function-call argument checks, `within_ms` latency budgets and natural-language `eval:` criteria graded by a judge. The judge runs on Ollama by default, or on any OpenAI-compatible endpoint. You run it with `pipecat eval run file.yaml`. In **text mode** STT and TTS are skipped, which makes prompt iteration fast and cheap. In **audio mode** the caller's voice is synthesized with TTS and the agent's speech is transcribed, so the whole pipeline is exercised. https://docs.pipecat.ai/pipecat/evals/overview ; https://github.com/pipecat-ai/pipecat/releases/tag/v1.11.0 ; https://x.com/pipecat_ai/status/2067278219779129851
  - 1.11.0 added multiple scenarios per file (`scenarios:`), `text_excludes:`, judge-graded `eval:` on function calls, `concurrency:`, and per-expectation results. https://github.com/pipecat-ai/pipecat/releases/tag/v1.11.0
- **LiveKit Agent Simulations** also use an LLM-driven simulated user. Each scenario has instructions (persona + goal), `agent_expectations` for the judge, and seeded user data (`ctx.simulation_context()`). An `on_simulation_end` hook lets you check the real end state, but that hook can only *fail* a run; it cannot override the judge. There is a text mode (the default, meant for CI) and an audio mode that covers turn-taking, interruptions, transcription and perceived latency. Commands: `lk agent simulate text --scenarios scenarios.yaml`. Runs execute on LiveKit Cloud, with 15 concurrent per run and 30 per project. https://docs.livekit.io/agents/start/testing/simulations/
- LiveKit's own guidance: use unit tests (pytest/Vitest assertions on messages, tool calls and handoffs) for turn-level behavior, simulations for multi-turn flow, and audio simulation for turn-taking and speech-specific problems. https://docs.livekit.io/agents/build/testing/
- Anthropic's agent-eval guidance notes that conversational agents "often require a second LLM to simulate the user" (for example, tau-bench-style airline booking). https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- **Research benchmark:** tau-Voice (arXiv 2603.13686, March 2026) extends tau²-bench to full-duplex voice. It has 278 grounded tasks and a voice user simulator with accents, noise and turn-taking. The simulator is decoupled from wall-clock time, so it can use a strong LLM without real-time pressure. Headline results: text agents complete 85% of tasks, voice agents 31-51% on clean audio and 26-38% with realistic audio. 79-90% of failures come from agent behavior. https://arxiv.org/abs/2603.13686 ; code: https://github.com/sierra-research/tau2-bench

**Persona design.**
- Simulators are too cooperative by default. Coval's guide (vendor) says LLM callers "bend over backwards to make the conversation succeed," so personas have to be written to stammer, change course and interrupt. It proposes difficulty tiers:
  - Easy: clear speech, one intent.
  - Medium: accent, noise, two intents.
  - Hard: heavy accent, emotional caller, mid-call pivot.
  - Adversarial: social engineering.

  https://www.coval.ai/blog/voice-ai-agent-evaluation-guide/
- AWS Strands ActorSimulator guidance:
  - Keep personas consistent across the conversation.
  - Give the caller an explicit, measurable goal.
  - Set `max_turns` to fit the task (3-5 for focused tasks, 8-10 for multi-step ones).
  - Use auto-generated profiles for breadth and hand-written ones to reproduce production patterns.
  - Look at patterns across the suite, not single transcripts.

  https://aws.amazon.com/blogs/machine-learning/simulate-realistic-users-to-evaluate-multi-turn-ai-agents-in-strands-evals
- Anthropic: start with **20-50 tasks drawn from real failures** rather than waiting for a big dataset. https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents

## 2. Judge rubrics (LLM-as-judge)

- **Binary pass/fail, not Likert scales.** Hamel Husain and Shreya Shankar: "Binary evaluations force clearer thinking and more consistent labeling". Their other rules:
  - Use **one judge per failure mode**. "The most common mistake" is asking one judge to catch many kinds of error.
  - Do error analysis first: open coding, then axial coding, before writing any judge.
  - Put code-based checks before LLM judges.
  - Generic metrics "create false confidence".

  https://hamel.dev/blog/posts/evals-faq/
- **Validate every judge against human labels.** Measure the **true positive rate and true negative rate** separately rather than overall accuracy. Label about **100-200 examples per failure mode**, split into train/dev/test, and keep the test split untouched. https://hamel.dev/blog/posts/evals-faq/
- OpenAI: prefer pairwise or pass/fail over single-answer scoring. Watch for position and verbosity bias. Check agreement with human labels before swapping in a cheaper judge. https://developers.openai.com/api/docs/guides/evaluation-best-practices
- Anthropic describes three grader types:
  - Code-based: fast and objective, but brittle.
  - Model-based: rubric scoring; needs calibration against humans.
  - Human: the gold standard, but expensive.

  Grade both the **transcript** and the **outcome**, meaning the final state of the environment (for example, "was a calendar event actually created"). Use **pass^k**, the probability that all k trials succeed, when users expect the agent to behave reliably every time. "Read the transcripts!" https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- Coval (vendor) recommends one dimension per metric (no bundled "conversation quality" score). Calibrate on 50-100 calls against human review and aim for >85% agreement on binary metrics. https://www.coval.ai/blog/voice-ai-agent-evaluation-guide/
- **A caution from research.** GAUGE (EMNLP 2026 Industry Track, arXiv 2609.12191) found that high judged satisfaction coexisted with task failure: 57.5% of highly rated conversations failed the customer's task. Judge disagreement went from under 1% on pairs of agents with very different quality to 31% on close pairs. Their recommendation is to "calibrate then trust" and keep a simple completion metric as the regression gate. https://arxiv.org/abs/2609.12191

## 3. Regression gating

- OpenAI: "continuous evaluation" means running evals on every change, logging everything, and mining logs to grow the eval set. https://developers.openai.com/api/docs/guides/evaluation-best-practices
- Anthropic distinguishes **regression evals** (should stay near 100%) from **capability evals** (start low and climb). https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- Coval's (vendor) cadence:
  - Per deploy: a core regression suite that runs in minutes and blocks release.
  - Nightly: an extended suite with medium personas.
  - Weekly: the full suite including adversarial cases, non-blocking.

  Example gates: task completion above 95%, 100% on compliance disclosures. Suggested review loop: 10-20% of production calls go to human or judge review, 100% get lightweight anomaly checks (latency spikes, early hang-ups), and flagged calls become new tests. https://www.coval.ai/blog/voice-ai-agent-evaluation-guide/
- Cekura (vendor) ships a GitHub Action that runs a locked scenario suite on each PR or push and nightly on cron. https://www.cekura.ai/blogs/github-actions-voice-agent-testing ; https://github.com/cekura-ai/cekura-github-actions
- Daily (Pipecat maintainers): "build lightweight evals as early as you can" and keep feeding real-world data back into them. https://www.daily.co/blog/advice-on-building-voice-ai-in-june-2025/
- In practice, text-mode simulation is the cheap PR gate, and audio-mode runs are rarer and more expensive. Both Pipecat and LiveKit describe their text modes as the fast, cheap CI option. https://docs.pipecat.ai/pipecat/evals/overview ; https://docs.livekit.io/agents/start/testing/simulations/

## 4. Latency metrics

**Definitions.**
- Twilio separates the **mouth-to-ear turn gap** (what the user experiences, including the PSTN leg) from the **platform turn gap** (internal processing only).
  - Targets: mouth-to-ear 1,115 ms (upper limit 1,400 ms); platform 885 ms (upper limit 1,100 ms).
  - Per component: STT 350 ms (500), LLM TTFT 375 ms (750), TTS TTFB 100 ms (250).
  - The public network leg adds about 40 ms, plus about 30 ms of buffering and 25 ms of decoding.

  https://www.twilio.com/en-us/blog/developers/best-practices/guide-core-latency-ai-voice-agents
- Daily: aim for **800 ms median voice-to-voice**. Rough budget: network ~200, STT + turn detection ~400, LLM ~500, TTS ~200 ms. "Any conversation turn with a tool call doubles the LLM latency." https://www.daily.co/blog/advice-on-building-voice-ai-in-june-2025/
- LiveKit's approximation: `total_latency = eou.end_of_utterance_delay + llm.ttft + tts.ttfb`. Metric fields: `ttft`, `ttfb`, `end_of_utterance_delay`, `transcription_delay`, `on_user_turn_completed_delay`. The last one is **not** included in the end-of-utterance delay but still adds to perceived latency. https://docs.livekit.io/testing/observability/data/ ; https://github.com/livekit/agents/issues/3236
- Pipecat metric types:
  - Latency: `TTFBMetricsData`, `TTFAMetricsData` (time to first audio, TTS), `TTFATMetricsData` (time to first answer token, LLM), `ProcessingMetricsData`, `TextAggregationMetricsData`.
  - Usage: `LLMUsageMetricsData`, `STTUsageMetricsData`, `TTSUsageMetricsData`.
  - Enabled with `enable_metrics` / `enable_usage_metrics`.

  `UserBotLatencyObserver` measures the gap from the user stopping speech to the bot starting speech, inside the pipeline. https://docs.pipecat.ai/pipecat/fundamentals/metrics
- The OTel GenAI conventions define `gen_ai.response.time_to_first_chunk` for streaming responses. https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/gen-ai-spans.md

**Report percentiles, not averages.** Hamming (vendor) reports production turn latency, from user stop to first agent audio, across 10M+ minutes and 10K+ agents: P50 1.4-1.7 s, P90 3.3-3.8 s, P95 4.3-5.4 s, P99 8.4-15.3 s. It says averages hide tails ("a 500ms average can mask 10% of calls spiking to 3+ seconds"). https://hamming.ai/resources/voice-ai-latency-whats-fast-whats-slow-how-to-fix-it ; https://hamming.ai/blog/testing-voice-agents-production-reliability

**Server-side vs perceived.** A worked Pipecat + Twilio + Modal measurement found about 570 ms spent in AI services (STT 195, turn detection 84, LLM 268, TTS 23 ms) and about 480 ms of overhead and network. Pipeline observers alone understate what the caller hears. https://www.fullstackml.dev/p/15-where-does-the-time-go-measuring

## 5. Tracing

- **Standard:** OpenTelemetry GenAI semantic conventions. They moved in 2026 to their own repo, https://github.com/open-telemetry/semantic-conventions-genai, and the old path now redirects (https://github.com/open-telemetry/semantic-conventions/blob/main/docs/gen-ai/gen-ai-spans.md). All spans are still **Development** stability.
  - Span name: `{gen_ai.operation.name} {gen_ai.request.model}`.
  - Operation names include `chat`, `execute_tool`, `invoke_agent`, `create_agent`.
  - `gen_ai.provider.name` is required.
  - `gen_ai.usage.input_tokens` / `output_tokens` are recommended; use billed counts where providers report both.
  - `gen_ai.conversation.id` is conditionally required.

  There are no audio- or speech-specific conventions yet (this repo's docs show none). https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/gen-ai-spans.md
- **Pipecat** span tree: `conversation` → `turn` (with `turn.number` and `turn.was_interrupted`) → `stt` / `llm` / `tts`.
  - LLM spans carry `gen_ai.*` attributes.
  - STT spans carry the transcript and `is_final`.
  - TTS spans carry `voice_id` and `metrics.character_count`.
  - Every span carries `metrics.ttfb`.

  Enable with `pipecat-ai[tracing]`, `setup_tracing(exporter)`, `enable_tracing=True` and `enable_turn_tracking=True`. Exports to any OTLP backend (Jaeger, Grafana, Langfuse, LangSmith, Datadog and others). https://docs.pipecat.ai/server/utilities/opentelemetry
- **LiveKit**: `set_tracer_provider()`. Attributes use two namespaces: `lk.*` (speech IDs, turn timings) and `gen_ai.*`. Content-bearing attributes use an `lk.pii.` prefix and can be stripped with `allow_pii=False`. The docs show Langfuse as the backend via `OTEL_EXPORTER_OTLP_*`. https://docs.livekit.io/testing/observability/tracing/
- **Audio on traces** is now common:
  - Langfuse attaches audio files to traces. https://langfuse.com/integrations/frameworks/pipecat
  - LangSmith (2026-07-21) added voice tracing for Pipecat, LiveKit, OpenAI Realtime and Gemini Live, with full call audio overlaid on the trace and spans for STT, TTS, VAD and interruptions. https://www.langchain.com/blog/trace-voice-agents-in-langsmith
  - Braintrust supports audio attachments on traces. https://www.braintrust.dev/docs/cookbook/recipes/VoiceAgent
- Daily: "The easier it is to look at stack traces, otel spans, and inference results for every unsuccessful conversation, the faster you will be able to improve your agents." https://www.daily.co/blog/advice-on-building-voice-ai-in-june-2025/

## 6. Cost tracking per call

A call's cost has four parts: telephony, STT (billed by audio seconds), LLM (tokens, including cached and reasoning tokens) and TTS (characters). The frameworks now emit the usage data for all of them.
- Pipecat `ServiceMetricsObserver` (PR #5607, merged 2026-09-04) turns metrics into `ServiceLatencyRecord` and `ServiceUsageRecord` records: STT audio seconds, TTS characters, and LLM tokens including cache reads and reasoning. Records are not aggregated, so you group them by turn, session or model yourself. https://github.com/pipecat-ai/pipecat/pull/5607
- LiveKit exposes `session.usage` and `SessionUsageUpdated` events, with usage per model (`LLMModelUsage`, `STTModelUsage`, `TTSModelUsage`), and reports `gen_ai.usage.cache_read.input_tokens` on spans. https://docs.livekit.io/testing/observability/data/ ; https://docs.livekit.io/testing/observability/tracing/
- Twilio: the Call resource's `price` / `price_unit` is "Populated after the call is completed. May not be immediately available". It covers connectivity only; answering machine detection (AMD), TTS and SIP REFER are excluded. Plan for an asynchronous reconciliation job. https://www.twilio.com/docs/voice/api/call-resource
- Langfuse: cost you send in takes priority over cost it infers. Inferred cost comes from regex-matched model price definitions. You can define custom models and usage types (for example `audio_tokens`), and cost rolls up per trace. https://langfuse.com/docs/observability/features/token-and-cost-tracking

## 7. Tooling landscape (2026)

| Category | Tool | Notes | Source |
|---|---|---|---|
| Framework-native evals (OSS) | Pipecat Evals | YAML scripted + simulated, text/audio, CLI, local judge | https://docs.pipecat.ai/pipecat/evals/overview |
| Framework-native evals | LiveKit tests + Agent Simulations | pytest assertions; simulations on LiveKit Cloud | https://docs.livekit.io/agents/build/testing/ ; https://docs.livekit.io/agents/start/testing/simulations/ |
| Benchmark (OSS) | tau²-bench / tau-Voice | Grounded tasks, voice user simulator | https://github.com/sierra-research/tau2-bench |
| Tracing + evals (OSS / self-hostable) | Langfuse | OTel ingest, Pipecat/LiveKit integrations, audio, cost | https://langfuse.com/integrations/frameworks/pipecat ; https://langfuse.com/integrations/frameworks/livekit |
| Tracing + evals (OSS) | Arize Phoenix / OpenInference | OTel-based; audio eval cookbook (tone) | https://arize.com/docs/ax/cookbooks/evaluate/tracing-and-evaluating-audio |
| Tracing + evals (commercial) | LangSmith | Voice tracing for 4 frameworks (Jul 2026) | https://www.langchain.com/blog/trace-voice-agents-in-langsmith |
| Evals platform (commercial) | Braintrust | Scenarios, custom scorers, audio attachments | https://www.braintrust.dev/docs/cookbook/recipes/VoiceAgent |
| Evals (OSS) | DeepEval | Voice personas / conversation simulator | https://deepeval.com/docs/conversation-simulator-voice-personas |
| Voice QA / simulation (commercial) | Coval, Hamming, Cekura, Roark | Real-audio phone simulation, production monitoring, CI hooks | https://www.coval.ai/blog/voice-ai-agent-evaluation-guide/ ; https://hamming.ai/resources/voice-agent-testing-guide ; https://www.cekura.ai/blogs/github-actions-voice-agent-testing ; https://roark.ai/ |
| Platform observability | LiveKit Cloud | Transcripts, recordings, traces, 30-day retention, PII redaction | https://docs.livekit.io/agents/observability/ |

---

## Implications for the spec

1. **Two-tier eval harness in the repo.**
   - Tier 1 (runs on every PR): text-mode scenario suite of scripted + simulated Qualification Calls.
   - Tier 2 (nightly or on demand): audio-mode suite placing real Twilio calls from a simulated-caller number, to measure mouth-to-ear latency and barge-in.

   Pipecat Evals covers both tiers without a vendor if the stack is Pipecat. Keep the scenarios as YAML under version control.
2. **Personas from the domain.** Cover:
   - A clear Lead with Intent to Buy.
   - A Lead who wants budget talk now. The agent must defer, because budget belongs on the Discovery Call, never on the Qualification Call.
   - A Lead who asks for a person. The agent should route to the Manager.
   - A Lead who says "not now", which should become a Parked Lead.
   - Voicemail or answering machine.
   - Hostile or silent callers.
   - Arabic/English code-switching and Gulf-accented English (UAE context).

   Make personas uncooperative on purpose.
3. **Outcome graders before LLM judges.**
   - Code checks on end state: was a Discovery Call event created on the Manager's Google Calendar with the correct slot? Is the Lead's status Qualified or Parked as expected?
   - Tool-call argument assertions.
   - Then **binary, single-failure-mode judges**, for example "mentioned pricing/budget", "booked without explicit Intent to Buy", "failed to identify as AI" (if disclosure is required) and "talked over caller". Validate each against ~100 hand-labeled transcripts (TPR/TNR).
4. **Gate on pass^k.** Run each regression scenario k times (e.g. k=3-5) and require all to pass for critical behaviors such as booking correctness and no budget talk. Track pass rates for softer metrics. Keep a plain completion metric as the gate, per GAUGE.
5. **Latency SLOs as percentiles.** Record per-turn `stt`, `eou`, `llm.ttft`, `tts.ttfb` and the server-side user-stop to bot-start gap. Put P50/P95/P99 on a dashboard. Suggested targets from Twilio and Daily: P50 platform turn gap ≤ ~900 ms and mouth-to-ear ≤ ~1.1-1.4 s. Measure mouth-to-ear separately from recorded calls, since server observers miss the PSTN leg. Tag turns that include a tool call (for example calendar lookups), because they roughly double LLM latency.
6. **OTel tracing from day one.**
   - One trace per call. `gen_ai.conversation.id` = Twilio CallSid.
   - Span tree: conversation → turn → stt/llm/tts/`execute_tool`.
   - Export over OTLP to self-hosted Langfuse (or Phoenix), with call audio attached.
   - Redact PII (phone numbers, names) at the span level.
7. **Per-call cost ledger.**
   - Sum STT seconds, LLM tokens (cached, uncached, reasoning) and TTS characters from framework usage records, priced from a versioned price table.
   - Reconcile asynchronously with Twilio `price` after the call ends. It excludes AMD and other add-ons.
   - Report cost per call, per Qualified Lead and per booked Discovery Call.
8. **Production-to-eval loop.**
   - Review every call automatically (anomaly flags, judges).
   - Review a sample by hand.
   - Turn each confirmed failure into a new regression scenario.

## Open uncertainties

- The OTel GenAI conventions are still at Development stability, and there are no audio or speech semantic conventions yet. Pipecat (`metrics.ttfb`, `turn.*`) and LiveKit (`lk.*`) each use their own attributes, so dashboards will not port between frameworks.
- Nobody publishes an independent end-to-end latency benchmark for Twilio Media Streams. The Hamming, Telnyx and Twilio figures are all vendor-reported, and the percentile ranges differ widely (for example Hamming's P50 of about 1.5 s versus Twilio's mouth-to-ear target of 1.1 s).
- The tau-Voice numbers cover native and realtime voice systems. How much they apply to a cascaded STT-LLM-TTS agent is unclear, although MTVA-Bench (arXiv 2609.20152) looks at the LLM inside cascaded agents and was not reviewed here.
- How well LLM simulated callers reproduce UAE-specific speech (Gulf English, Arabic code-switching) is untested. TTS voices for the simulated caller may not cover it.
- Commercial voice QA vendors (Coval, Hamming, Cekura, Roark) were not compared on price or on how realistic their simulations are. Their blogs double as marketing.
- It is not verified whether Pipecat Evals audio mode can drive a *telephony* (Twilio) transport, as opposed to a local or WebRTC one. If it cannot, real-call audio tests need a custom dialer harness or a vendor.
- A few fetched pages were summarized by a tool, and minor specifics were not re-checked against raw source: exact LiveKit API field names, and OpenAI's example model name, which was omitted.
