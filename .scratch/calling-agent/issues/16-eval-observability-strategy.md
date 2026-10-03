# Evaluation and observability strategy

Type: grilling
Status: resolved
Blocked by: 05, 08
Map: ../map.md

## Question

How will we know the Calling Agent is good before and after it calls real Leads: simulated-Lead persona suite, judge rubrics (tone, rule adherence, booking success, honesty when asked if AI), latency targets per stage, tracing, cost tracking, regression gating for prompt changes, and a human review loop on real calls?

## Answer

Settled with the owner 2026-09-30.

**Tier 1: text evals on every PR**
- A custom pytest harness, modelled on Pipecat Evals and LiveKit simulations.
- Scenarios live in YAML: the 10 from the call-flow prototype, and growing.
- A simulated-Lead LLM persona talks to Omar through the text-mode seam (ticket 21).
- Code-based checks run first: end status, legal opening order, no budget/timeline numbers, no unconfirmed "booked".
- Then the judges run. Any failure blocks the merge.

**Tier 2: real audio calls**
- About 5 real calls nightly over Twilio (weekly acceptable), about $5 a run.
- A simulated caller uses varied TTS voices and accents.
- Measures latency, barge-in and voicemail detection.

**Judges (owner decision)**
- Fast "System-1" judge models: **Jev** (TypeSafe AI), or an open-source alternative.
  - Jev is a non-generative classifier: deterministic, sub-second, it returns a probability and confidence per answer, and it is cheap.
  - It is supported in Langfuse, DeepEval and MLflow.
  - Sources: https://langfuse.com/docs/evaluation/evaluation-methods/jev-as-a-judge, https://mlflow.org/blog/jev-llm-judge/, https://deepeval.com/blog/introducing-jev-in-deepeval
- One binary criterion per failure mode: needy or pushy tone, talking over the Lead, answering from outside the knowledge sheet, missing an Intent to Buy signal.
- Jev gives no written rationale. Low-confidence verdicts escalate to a generative LLM judge, following "JEV-as-a-Judge: Accept When Confident, Escalate When Unsure" (https://arxiv.org/abs/2609.26550).
- Open question for the provider ticket: which open-source System-1 alternative, if any, matches Jev.
- Calibration: the Manager labels about 50 real transcripts during the soft launch. A judge is trusted only once it agrees with those labels.

**Latency targets (starting point)**
- Median turn gap ≤ 1.2 s; p95 ≤ 2.0 s, measured per stage (STT end-of-turn, LLM first token, TTS first byte, network).
- The owner will **recalibrate them from real call trials**.

**Tracing**
- OpenTelemetry → **Langfuse**: one trace per call keyed on the Twilio call SID, with audio attached.

**Production monitoring**
- Every real Connected Call is auto-graded after it ends (code checks + judges).
- Any rule breach alerts the Manager the same day.
- Dashboard metrics:
  - connect rate;
  - booking rate;
  - show-up rate (booked Discovery Calls the Lead actually attended);
  - cost per booked Discovery Call;
  - latency p50/p95.
- Every real failure becomes a new Tier 1 scenario.
