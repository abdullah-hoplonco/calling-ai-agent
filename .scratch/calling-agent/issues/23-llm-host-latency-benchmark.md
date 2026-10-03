# Benchmark LLM hosts for Omar's latency

Type: task
Status: open
Map: ../map.md

## Question

AFK once API keys exist. From an EU server (the planned voice-server region), measure time-to-first-token and tool-call correctness for: self-hosted Qwen3.8-27B (thinking off) on a rented GPU in Dublin; Groq (Helsinki); Nebius (EU); DeepSeek V4.1 Flash (non-thinking) on an EU/US host; with claude-haiku-4-5 as the baseline. Add Cerebras once its EU capacity is live. Use a realistic Omar prompt (system prompt + knowledge sheet + ~6 turns of history + tools), about 50 requests each, reporting p50/p95. Record the winning host, or fall back to the backup model if none meets a p50 TTFT of about 700 ms or less.
