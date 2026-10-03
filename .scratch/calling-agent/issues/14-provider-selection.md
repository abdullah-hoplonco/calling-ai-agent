# Select STT, TTS and LLM providers

Type: grilling
Status: resolved
Blocked by: 02, 03, 17
Map: ../map.md

## Question

Which STT, TTS and LLM providers does the MVP use (and which are fallbacks), given the latency, cost, accent-accuracy and telephony findings from tickets 02 and 03? Includes the per-minute cost estimate for a typical call.

Also decide the LLM latency strategy: a faster model vs Haiku 4.5, or starting the reply before the Lead's turn is confirmed.

Also: choose the eval judge model: Jev (owner's preference) or an open-source System-1 alternative (see ticket 16).

## Answer

Settled with the owner 2026-09-30. Every provider sits behind an adapter (ticket 21), so each choice is a config change.

**LLM (live Omar)**
- **DeepSeek V4.1 Flash**, non-thinking mode (owner's pick for its intelligence-to-cost ratio), served by a **US/EU host** (e.g. Fireworks or DeepInfra). **Not** DeepSeek's first-party API, which runs in China (risk R10).
- About 22 hosts serve it; tool calling is supported.
- Price is about $0.15/$0.60 per million input/output tokens on DeepSeek's API, with peak 2× during 10:00-14:00 UAE. Host prices vary (OpenRouter endpoint list).
- One reported time-to-first-token is ~1.37 s (possibly thinking mode), which would miss the 1.2 s target. A latency benchmark (ticket 23) confirms the host before lock-in.
- Backup: claude-haiku-4-5 (~640 ms TTFT, 98% tool-call pass in the research).

**STT**
- **Deepgram Flux** as primary: native μ-law, built-in end-of-turn.
- **AssemblyAI Universal streaming** as backup.

**TTS**
- **Cartesia Sonic** as primary; **ElevenLabs Flash** as backup.
- Omar's exact voice is picked by ear (ticket 24).

**Evals and after-call agents**
- Judges: Jev, escalating to **Claude Sonnet 5** (a different family from Omar).
- Post-call agents (summary, outcome, Intent to Buy evidence): DeepSeek V4.1 Flash in thinking mode.
- Simulated Lead in evals: **Claude Haiku 4.5** (a different family from Omar).

**Failover**
- LLM and TTS switch to the backup within the same turn on error or a wait over ~1.5 s.
- STT failure alerts only.

**Cost estimate per connected minute** (to verify on real calls)
- Twilio ~$0.30 + Media Streams ~$0.004.
- STT ~$0.005-0.008.
- TTS ~$0.01-0.02 (Omar speaks ~40% of the time).
- LLM ~$0.005.
- Total: **≈ $0.33/min, ≈ $1 per 3-minute call**. Twilio's UAE termination is about 90% of it.

Sources: https://openrouter.ai/deepseek/deepseek-v4.1-flash, https://artificialanalysis.ai/models/deepseek-v4-1-flash/providers, https://api-docs.deepseek.com/quick_start/pricing/, research/02 and research/03.

## Amendment (2026-10-02, owner): Option C

- **Live LLM:** **self-hosted Qwen3.8-27B (thinking off) on a rented GPU in Dublin**, next to the agent (~100 ms first token, measured on similar hardware), served through an OpenAI-compatible endpoint.
- **Final choice comes from ticket 23's benchmark.** Candidates:
  - our own GPU;
  - Groq (Helsinki);
  - Nebius (EU);
  - DeepSeek V4.1 Flash on an EU/US host.
- **Backup:** DeepSeek V4.1 Flash on an EU/US host. **After-call agents:** DeepSeek V4.1 Flash (thinking).
- **STT/TTS:** Deepgram **EU endpoint** and Cartesia **EU endpoint**.
- **Cerebras:** add it to the benchmark once its EU capacity is live (announced for end of 2026).
