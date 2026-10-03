# Production evaluation and observability practices for voice agents

Type: research
Status: resolved
Map: ../map.md

## Question

What does production-grade evaluation and observability look like for LLM voice agents today? Cover: simulated-caller testing (LLM personas driving the agent), LLM-as-judge transcript scoring and rubric design, regression suites for prompt changes, latency metrics (turn latency percentiles, TTFB per stage), tracing of turns and tool calls, cost tracking per call, and tooling (open-source and commercial) that practitioners use. Prefer primary sources: vendor/engineering blogs from teams running voice agents, framework docs, papers.

## Answer

- Simulated callers now come built into the frameworks. Pipecat Evals (1.4+, YAML with scripted and simulated scenarios, `pipecat eval run`) and LiveKit Agent Simulations both put an LLM caller with a persona and goal against the real agent, then a judge grades the call. Text mode is the cheap gate on every PR; audio mode is for turn-taking, latency and barge-in.
- Default LLM callers are too cooperative, so write personas that are messy on purpose: interruptions, pivots, noise, adversarial callers, UAE accents and code-switching.
- Grade outcomes before judging text. Start with code checks on end state (calendar event created, Lead status) and tool-call arguments. Then use binary judges, one per failure mode, each checked against ~100-200 human labels (TPR/TNR), never Likert scales. GAUGE (EMNLP 2026) shows judged satisfaction can hide task failure.
- Regression gating: every change runs a fast core suite that blocks merges, with nightly and weekly extended or adversarial runs. Use pass^k for critical behaviors. Every production failure becomes a new scenario.
- Latency: report P50/P95/P99, not averages. Split per stage: STT, end-of-utterance, LLM TTFT, TTS TTFB. Targets: about 800 ms median voice-to-voice (Daily); on Twilio, a platform turn gap of about 885 ms and mouth-to-ear of about 1.1-1.4 s. Server-side observers miss the PSTN leg.
- Tracing: OpenTelemetry GenAI semantic conventions (still at Development stability, no audio conventions yet). The Pipecat and LiveKit span trees are conversation → turn → stt/llm/tts/tool, exported over OTLP to Langfuse, Phoenix or LangSmith with call audio attached and PII redacted.
- Cost per call = STT seconds + LLM tokens + TTS characters (Pipecat `ServiceUsageRecord`, LiveKit `session.usage`) + Twilio `price`, which arrives only after the call and covers connectivity only.
- Tooling: open source is Pipecat Evals, LiveKit sims, tau²-bench/tau-Voice, Langfuse, Phoenix and DeepEval. Commercial is LangSmith and Braintrust, plus voice QA vendors Coval, Hamming, Cekura and Roark.

[findings](../research/05-voice-agent-evals-observability.md)
