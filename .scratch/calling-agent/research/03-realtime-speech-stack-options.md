# Real-time STT, TTS, LLM and speech-to-speech options for the Calling Agent

Research for [issue 03](../issues/03-realtime-speech-stack-options.md). Researched 2026-09-25. Prices are list/pay-as-you-go USD as published on that date and change often; re-check before committing.

**How to read the numbers.** Each figure is tagged:

- **[V]**: vendor-claimed (the vendor's own pricing page, docs or marketing).
- **[I]**: measured by a third party with a published method. The main third-party sources are:
  - the Pipecat/Daily open benchmarks (`pipecat-ai/stt-benchmark`, `kwindla/aiewf-eval`, PhoneBench);
  - Coval's continuously-run leaderboards;
  - the Artificial Analysis Speech Arena, which is based on blind preference votes.
- **[I, vendor-adjacent]**: Daily builds Pipecat and ships its own PhoneLLM model, and Coval sells voice-agent evals. Both are independent of the STT/TTS/LLM vendors but not neutral bystanders.

**Caveat that applies to every table.** None of the third-party benchmarks below uses 8 kHz μ-law telephony audio from UAE callers. They are wideband English conversational data. For our use case they rank latency well, but they only weakly predict accuracy.

---

## 1. Streaming STT

| Provider / model | Price **[V]** | Pipecat stt-benchmark **[I]** TTFS median / P95; semantic WER (pooled) | Coval **[I]** WER; TTFS | 8 kHz μ-law in | Turn detection / endpointing |
|---|---|---|---|---|---|
| **Deepgram Flux** (`flux-general-en`) | $0.0065/min promo, $0.0077 regular ([pricing](https://deepgram.com/pricing)) | not listed | 5.9 %; 98 ms | Yes: mulaw, 8000 Hz ([docs](https://developers.deepgram.com/docs/flux/quickstart)) | Native model-based end of turn. Events: `StartOfTurn`, `EagerEndOfTurn`, `TurnResumed`, `EndOfTurn`. Params: `eot_threshold` (default 0.7), `eager_eot_threshold` (off by default), `eot_timeout_ms` (default 5000) ([docs](https://developers.deepgram.com/docs/flux/quickstart)). Vendor claim: EoT around 260 ms P50 **[V]** ([blog](https://deepgram.com/learn/introducing-flux-conversational-speech-recognition)) |
| Deepgram Nova-3 | $0.0048/min promo, $0.0077 regular | 247 / 298 ms; 1.62 % | 5.4 %; 84 ms | Yes | Silence-based endpointing plus VAD; you pair it with your own turn model |
| **AssemblyAI Universal-3.5 Pro Realtime** (`u3-rt-pro`) | $0.45/hr base, about $0.0075/min. Billed on WebSocket open time, idle included ([pricing](https://www.assemblyai.com/pricing)) | 282 / 354 ms; 1.22 % | 2.3 %; 162 ms (rank #1) | Yes: `encoding=pcm_mulaw`, `sample_rate=8000`, native ([Twilio guide](https://www.assemblyai.com/blog/twilio-phone-agent-with-assemblyai)) | About 300 ms EoT from tonality, pacing and terminal punctuation. Modes: `min_latency`, `balanced`, `max_accuracy` **[V]** |
| AssemblyAI universal-3-6-pro | not on pricing page yet | 307 / 401 ms; 0.96 % | n/a | presumably same API | same |
| AssemblyAI Universal-Streaming English | $0.15/hr, about $0.0025/min | 256 / 362 ms; 3.02 % | 5.9 % | Yes | Built-in turn detection |
| **Soniox** stt-rt-v5 / v4 | $0.12/hr, about $0.002/min ([pricing](https://soniox.com/pricing)) | v5 260 / 305 ms, 1.27 %; v4 249 / 281 ms, 1.29 % | v5 4.6 %; 47 ms | Not confirmed in sources read | Endpoint detection (details not verified) |
| **Speechmatics Linden-1** ("Agent STT") | $0.30/hr, falling to $0.15/hr with volume ([voice-agents page](https://www.speechmatics.com/voice-agents)) | 369 / 438 ms; 1.05 % | 4.2 %; 229 ms | Not confirmed in sources read | `end_of_utterance_silence_trigger` (0.5 to 0.8 s recommended) and `ForceEndOfUtterance`. Server-side semantic turn detection is "coming soon" ([docs](https://docs.speechmatics.com/speech-to-text/realtime/turn-detection)). Vendor claims 55+ languages and the "deepest accent coverage" (the latter comes from a secondary source) |
| Cartesia Ink-2 | bundled credits ([pricing](https://cartesia.ai/pricing)) | 299 / 328 ms (P99 1584 ms); 1.25 % | 3.5 %; 153 ms | likely; not verified | Turn-aware variant exists in Pipecat (`CartesiaTurnsSTTService`) |
| ElevenLabs Scribe v2 Realtime | $0.39/hr ([pricing](https://elevenlabs.io/pricing/api)) | 281 / 348 ms; 3.12 % | 4.2 %; 122 ms | not verified | VAD-based commit |
| NVIDIA Nemotron 3.0 ASR (en) | self-host or partner | 221 / 238 ms; 1.95 % (fastest, tightest tail) | n/a | self-host, so you resample | none (bring your own) |
| Gladia Solaria | $0.75/hr starter, $0.25/hr growth ([pricing](https://www.gladia.io/pricing)) | not listed | Solaria-1 5.9 %; 741 ms | not verified | n/a |
| OpenAI gpt-realtime-whisper / gpt-4o-transcribe | $0.017/min / $0.006/min ([pricing](https://developers.openai.com/api/docs/pricing)) | 740 ms / 637 ms median; 2.7 to 3.1 % | 3.9 % / 3.6 % | `audio/pcmu` supported in Realtime | Server VAD or semantic VAD |
| Google gemini-3.5-transcribe-live | $0.005/min in plus $0.004/min text out ([pricing](https://ai.google.dev/gemini-api/docs/pricing)) | 458 / 532 ms; 2.24 % | 3.0 %; 321 ms | 16 kHz PCM only, so you resample | n/a |

Sources for the independent columns:

- [pipecat-ai/stt-benchmark README](https://github.com/pipecat-ai/stt-benchmark).
  - Data: 1000 samples of `smart-turn-data-v3.1`.
  - Semantic WER is judged by Claude. TTFS is measured from actual speech end to the final transcript, with VAD `stop_secs=0.2`.
  - The benchmark does not state the sample rate.
- [Coval STT leaderboard](https://benchmarks.coval.ai/stt).
  - Data: 3,500 samples covering clipping, far-field, phone-codec, reverb, accents and noise, as described by [AssemblyAI's summary of it](https://www.assemblyai.com/blog/universal-3-5-pro-independent-stt-benchmarks).
  - Coval's own write-up gives no per-accent or telephony breakdown ([Coval blog](https://www.coval.ai/blog/best-speech-to-text-providers-in-2026-independent-benchmarks-and-how-to-choose/)).
  - Coval measures "TTFS" differently from Pipecat, so compare within one source only.

**Accent accuracy (Gulf Arab, South Asian, Filipino English).** I found no primary or independent benchmark with a per-accent breakdown for these groups on streaming, telephony-band audio.

- The only numbers turned up were a Hindi-language comparison from a secondary blog: Speechmatics 16.6 % vs Deepgram 23.0 % WER ([futureagi](https://futureagi.substack.com/p/speech-to-text-apis-in-2026-benchmarks)). That is Hindi speech, not Indian-accented English, and the source is low-trust.
- Academic work (EdAcc, GigaSpeechBench, [arXiv 2606.28884](https://arxiv.org/pdf/2606.28884)) reports large WER drops on non-US/UK accents in general.
- **Conclusion:** accent accuracy has to be measured on our own lead-call samples (see issue 06).

**Keyword boosting** matters for names, business names and "Discovery Call" slot phrasing:

- Deepgram and AssemblyAI support keyterm prompting.
- Speechmatics supports custom vocabulary of up to 1,000 words **[V]**.
- ElevenLabs charges for keyterm prompting as an add-on **[V]**.

---

## 2. Streaming TTS

| Provider / model | Price **[V]** | Coval TTFA median **[I]** | Artificial Analysis Arena Elo **[I]** (blind preference) | 8 kHz μ-law out | Streaming and interruption features |
|---|---|---|---|---|---|
| **Cartesia Sonic-3.6** | Plan credits: $299/mo buys 8M credits, about 10.7k min. That is about $0.037 per 1k chars, or about $0.028/min on the Scale plan ([pricing](https://cartesia.ai/pricing)). AA lists $49 per 1M chars | 297 ms (Sonic-3.5: 272 ms) | **1279 (#1 overall)**; Sonic-3.5 1185 | Yes: `pcm_mulaw`, 8000 Hz ([WS docs](https://docs.cartesia.ai/api-reference/tts/websocket)) | WebSocket `context_id` with `continue` for token streaming, `cancel`, word and phoneme timestamps, `max_buffer_delay_ms` (default 3000) |
| **ElevenLabs Flash v2.5** | $0.05 per 1k chars, "about $0.05/min" ([pricing](https://elevenlabs.io/pricing/api)) | 189 ms | 1074 | Yes: `ulaw_8000` ([Twilio cookbook](https://elevenlabs.io/docs/cookbooks/text-to-speech/twilio)) | Multi-context WebSocket with `flush`, `close_context` and character-level alignment ([docs](https://elevenlabs.io/docs/api-reference/text-to-speech/v-1-text-to-speech-voice-id-multi-stream-input)). Vendor claims about 75 ms model latency **[V]** |
| **ElevenLabs Eleven v3 Conversational** | $0.05 per 1k chars | 328 ms | 1196 | ulaw_8000 (same API) | Vendor claims about 280 ms latency and audio tags **[V]** |
| **Deepgram Flux TTS** (launched 2026-08-12) | Pricing not published on the pages read. Free until 2026-09-12, standard pricing from 2026-09-13 ([product page](https://deepgram.com/product/text-to-speech/flux)) | 268 ms | not listed | Deepgram TTS WS supports mulaw at 8000 ([encoding docs](https://developers.deepgram.com/docs/tts-encoding)); not verified specifically for `/v2/speak` | `wss://api.deepgram.com/v2/speak`. Accepts LLM tokens directly and keeps context across turns. On interrupt it reports `text_spoken`, i.e. what the user actually heard ([docs](https://developers.deepgram.com/docs/flux-tts/overview)). Vendor claims 80 ms first response **[V]** |
| Deepgram Aura-2 | $0.030 per 1k chars ([pricing](https://deepgram.com/pricing)) | 296 ms | not listed on main board | Yes, mulaw 8000 | Aura model strings are rejected on `/v2/speak` and use v1 ([docs](https://developers.deepgram.com/docs/tts-websocket)) |
| Rime Mist v3 / Coda | $0.03 / $0.05 per 1k chars ([pricing](https://rime.ai/pricing)) | 279 ms / 331 ms (Coda WER 6.3 %) | Coda 1055; Mist v2 908 | not verified | Starter plan caps at 20 concurrent generations **[V]** |
| Inworld Realtime TTS-2 / TTS-2 Flash | AA lists $20.8 / $10.4 per 1M chars | TTS Flash 2: 62 ms; TTS 2: 485 ms | 1246 / 1210 | not verified | n/a |
| Google Gemini 3.8 Flash TTS | AA lists $16.5 per 1M chars | not listed (Chirp 3 HD: 589 ms) | 1265 (#2) | not verified | Not a streaming-conversation API per se |
| Gradium | AA lists $47.2 per 1M chars | 56 ms | 1149 | not verified | n/a |
| OpenAI gpt-4o-mini-tts | per pricing page | **2474 ms** | n/a | n/a | Too slow for turn-by-turn use |

Sources:

- [Coval TTS leaderboard](https://benchmarks.coval.ai/tts). TTFA is measured on production endpoints. Gradium's own write-up says Coval figures are continuously re-measured and that variance (IQR) differs widely ([Gradium](https://gradium.ai/content/tts-latency-benchmark-2026)); that write-up is vendor-authored.
- [Artificial Analysis TTS leaderboard](https://artificialanalysis.ai/text-to-speech/leaderboard). Elo from blind pairwise "which sounds more natural" votes; most models have about 1.3k to 7k samples.
- Naturalness Elo is measured on wideband audio. At 8 kHz μ-law, differences between top voices shrink. This is my inference, not something the sources measured.

---

## 3. LLM (text, tool calling)

The key metric is **TTFAT**: time to first answer token or tool call. Per the aiewf-eval authors, voice-to-voice latency is roughly **TTFAT + 500 ms**, and TTFAT above about 700 ms "is too slow for most voice agent use cases" ([aiewf-eval README](https://github.com/kwindla/aiewf-eval)).

| Model | Price per 1M in / out **[V]** | aiewf medium-context **[I, vendor-adjacent]** pass rate; TTFAT P50 / P95 | PhoneBench Alpha 1 **[I, vendor-adjacent]** score; TTFAT P50 / P95; $/min | Notes |
|---|---|---|---|---|
| **claude-haiku-4-5** | $1 / $5; cache hit $0.10 ([pricing](https://platform.claude.com/docs/en/about-claude/pricing)) | 98.0 %; 637 / 1615 ms | 67.8 %; 707 / 899 ms; $0.0188 | Best Anthropic latency; tight P95 on PhoneBench |
| claude-sonnet-5 (thinking disabled) | $2 / $10 (intro price made permanent) | 93.0 %; 1204 / 2465 ms | 68.9 %; 1651 / 2166 ms; $0.052 | Adaptive thinking runs by default, so it must be disabled explicitly for voice. Failure mode: re-asks for data it already has ([README note](https://github.com/kwindla/aiewf-eval)) |
| claude-sonnet-4-6 | $3 / $15 | 100 %; 850 / 4126 ms | n/a | Long P95 tail |
| claude-opus-5-5 | $4 / $20; fast mode $8 / $40 | not benchmarked | not benchmarked | Probably too slow and too expensive per turn; fast mode is in research preview |
| gpt-5.6-luna (reasoning none) | $0.20 / $1.20 ([pricing](https://developers.openai.com/api/docs/pricing)) | 88.3 %; 671 / 2304 ms | 70.7 %; 786 / 1736 ms; $0.0035 | Cheapest capable hosted option |
| gpt-5.6-terra | $2 / $12 | none: 91.3 %, 621 ms; medium: 97.8 %, 927 ms | 72.4 %; 980 / 1957 ms; $0.0347 | Tools plus reasoning effort needs the Responses API |
| gpt-4.1 | $2 / $8 | 96.3 %; 536 / 1771 ms | 57.4 %; 889 / 1190 ms | Older, fast |
| gemini-3.6-flash (minimal) | n/a (3.8 Flash: $0.75 / $3.75, [pricing](https://ai.google.dev/gemini-api/docs/pricing)) | 97.1 %; 798 / 984 ms | **78.6 % (#1)**; 1168 / 1468 ms; $0.0751 | Best PhoneBench score, but P50 is over 1 s |
| gemini-3.5-flash-lite | $0.30 / $2.50 | 68.6 % | 57.8 % | Weak on tools |
| gpt-oss-120b on **Groq** | $0.15 / $0.60, about 500 tok/s ([Groq docs](https://console.groq.com/docs/models)) | 86.3 %; **98 / 217 ms** | n/a | Very fast, weaker tool accuracy |
| nemotron-3-ultra / qwen3.8-27b (Baseten, self-host) | varies | 100 % at 541 / 712 ms; 98.2 % at 649 / 801 ms | Nemotron Ultra 38.1 % | Open weights; strongest latency-accuracy tradeoff on aiewf |
| Pipecat PhoneLLM 30B Alpha 1 | self-host | n/a | 72.3 %; 331 / ~600 ms; $0.0025 | Built by Daily, who also runs the benchmark |

Sources:

- aiewf medium-context: 30-turn scripted conversations scoring tool use, instruction following and KB grounding ([README](https://github.com/kwindla/aiewf-eval)).
- PhoneBench Alpha 1: 15 models on multi-turn phone-assistant tool calling, judged by an LLM panel, including "say/do consistency" (claiming a booking without calling the tool) ([PhoneBench](https://www.pipecat.ai/benchmarks/phonebench-alpha-1)).

**Takeaways for tool calling (Google Calendar availability and booking):**

- The two benchmarks rank models differently. For example, Haiku 4.5 scores 98 % on aiewf but 67.8 % on PhoneBench.
- Absolute PhoneBench scores are low for every model (below 80 %). "Said it booked but didn't call the tool" is a named failure class.
- The spec needs guardrails that don't depend on which model we pick: server-side confirmation of the booking before the agent says it is booked, and eval coverage of that failure.

---

## 4. Speech-to-speech and bundled voice agents (for comparison)

| Option | Price **[V]** | Measured V2V latency and quality **[I, vendor-adjacent]** (aiewf S2S) | Telephony | Notes |
|---|---|---|---|---|
| **OpenAI GPT-Live-1** (API since 2026-09-10) | **$0.05/min** voice layer, billed per second, plus separate backend model and tool costs ([announcement](https://community.openai.com/t/introducing-gpt-live-1-in-the-api/1396471); [pricing](https://developers.openai.com/api/docs/pricing)) | Not in aiewf yet. Vendor claims 0.798 s turn-taking latency, 87 % tool-calling success, and +30 pts on Full Duplex Bench vs gpt-realtime-2.1 **[V]** | WebSocket, WebRTC, SIP | Full-duplex front end that delegates reasoning and tools to a backend model you choose ("Responses delegation" or client delegation). Community reports endpointing issues **[unverified]** |
| OpenAI gpt-realtime-2.1 / gpt-realtime-2 | Audio $32 in / $64 out per 1M tokens; text $4 / $24 | realtime-2.1 (low reasoning): **97.2 % pass; V2V median 1504 ms**, max 4288 ms. gpt-realtime-1.5: 93.3 %, 1152 ms | SIP (`sip.api.openai.com`) and `audio/pcmu` G.711 ([SIP guide](https://developers.openai.com/api/docs/guides/realtime-sip)) | `server_vad` (threshold, `prefix_padding_ms`, `silence_duration_ms`) or `semantic_vad` (eagerness low/medium/high/auto), with `interrupt_response` ([VAD guide](https://developers.openai.com/api/docs/guides/realtime-vad)). 128k context |
| Google Gemini 3.8 Live (`gemini-3.8-live`) | Audio $0.005/min in, $0.018/min out; text $0.75 / $4.50 ([pricing](https://ai.google.dev/gemini-api/docs/pricing)) | Not measured. gemini-3.1-flash-live (minimal): 91.7 %, V2V 1632 ms; "even minimal is too slow for voice agent use cases, today" | No first-party PSTN. Input is 16 kHz PCM, output 24 kHz ([Live docs](https://ai.google.dev/gemini-api/docs/live)), so μ-law needs transcoding and resampling | Barge-in, proactive audio, function calling |
| grok-voice-think-fast-1.0 | n/a | 95.3 %; V2V 2336 ms | n/a | n/a |
| AWS nova-2-sonic | n/a | V2V 1280 ms | n/a | n/a |
| Deepgram Voice Agent API | $0.075/min standard, $0.163/min advanced ([pricing](https://deepgram.com/pricing)) | not measured | Twilio guide available | Bundled STT + LLM + TTS, still a cascade under the hood |
| AssemblyAI Voice Agent API | $0.075/min all-in ([pricing](https://www.assemblyai.com/pricing)) | not measured | Twilio SIP "expected" | Runs on self-hosted LiveKit |
| ElevenLabs Speech Engine | $0.08/min ([pricing](https://elevenlabs.io/pricing/api)) | not measured | ulaw_8000 natively | n/a |
| Cartesia agents | $0.06/min, plus $0.014/min telephony ([pricing](https://cartesia.ai/pricing)) | not measured | Own numbers | n/a |

Source for the S2S rows: aiewf-eval measures V2V from the recording, from end of user speech to start of model speech ([README](https://github.com/kwindla/aiewf-eval)).

**Rough comparison.**

- Measured realtime S2S models sit around 1.15 to 1.6 s median V2V in this benchmark, with multi-second maxima.
- A well-tuned cascade is estimated at TTFAT + about 500 ms:
  - Haiku 4.5: about 1.14 s.
  - gpt-4.1: about 1.04 s.
  - Groq-hosted open models: under 0.7 s.
- The cascade estimate is the benchmark authors' rule of thumb, not an end-to-end measurement over Twilio from the UAE.

---

## 5. Turn-taking, barge-in and latency techniques (Pipecat and LiveKit Agents)

These are design inputs for a hand-rolled pipeline.

### End-of-turn detection

- **Pipecat defaults.**
  - Silero VAD with `start_secs=0.2`, `stop_secs=0.2`, `confidence=0.7`, `min_volume=0.6`.
  - Silero processes each 30 ms chunk in under 1 ms on a single CPU thread.
  - The default stop strategy is Smart Turn v3 (`TurnAnalyzerUserTurnStopStrategy(LocalSmartTurnAnalyzerV3())`). The alternative is `SpeechTimeoutUserTurnStopStrategy(user_speech_timeout=0.6)`.
  - Local VAD is "150-200ms faster than remote VAD services".
  - Source: [Pipecat speech input](https://docs.pipecat.ai/pipecat/learn/speech-input.md).
- **Smart Turn v3.2.**
  - BSD-2 licence; weights, data and training code are open.
  - About 8M parameters on a Whisper-Tiny backbone; 8 MB int8 CPU build.
  - Inference is about 10 to 100 ms on CPU (about 65 ms on Pipecat Cloud).
  - 23 languages, including Arabic, Hindi and English.
  - It runs only after VAD silence, over up to 8 s of **16 kHz** turn audio, re-run whenever the user resumes speaking.
  - For us, Twilio's 8 kHz μ-law must be decoded and upsampled before it reaches the model.
  - Source: [smart-turn README](https://github.com/pipecat-ai/smart-turn).
- **STT/VAD coupling in Pipecat.**
  - After VAD stop, Pipecat waits the STT's measured P99 TTFS (`ttfs_p99_latency`) so the final transcript has arrived, then responds immediately.
  - Changing `stop_secs` invalidates the built-in P99 values; re-measure with stt-benchmark.
  - Source: [STT latency tuning](https://docs.pipecat.ai/pipecat/fundamentals/stt-latency-tuning).
- **LiveKit Agents defaults.**
  - The default turn detection is an audio `TurnDetector` model that uses semantics and prosody on top of Silero VAD.
  - Two versions: `v1`, served on LiveKit Cloud, and `v1-mini`, free on local CPU. 14 languages, including Arabic and Hindi.
  - With the detector, endpointing defaults are `min_delay` 0.3 s and `max_delay` 2.5 s (otherwise 0.5 s / 3.0 s).
  - If the model hasn't answered within about 1 s, the turn commits anyway.
  - Optional `endpointing.mode="dynamic"` adapts delays to the caller's measured pause statistics.
  - Other modes: `vad`, `stt` (use provider EoT, e.g. Flux or AssemblyAI), `realtime_llm`, `manual`.
  - Sources: [turns](https://docs.livekit.io/agents/build/turns/), [turn detector](https://docs.livekit.io/agents/logic/turns/turn-detector/), [tuning](https://docs.livekit.io/agents/logic/turns/tuning.md).
- **STT-native EoT as an alternative.**
  - Deepgram Flux and AssemblyAI u3-rt-pro fold turn detection into the STT, which removes a separate VAD-then-turn-model hop.
  - LiveKit exposes this as `turn_detection="stt"` and still uses VAD for interruptions.

### Speculative / preemptive generation

- **LiveKit.**
  - `preemptive_generation` is on by default: the LLM starts on the final transcript before the turn is confirmed.
  - `preemptive_tts` is off by default, because of wasted compute on cancellation.
  - Preemption is skipped for utterances over `max_speech_duration` (10 s), with `max_retries` of 3.
  - LiveKit warns that it "doesn't always reduce latency" and should be verified with metrics.
  - Source: [tuning](https://docs.livekit.io/agents/logic/turns/tuning.md).
- **Deepgram Flux.** `EagerEndOfTurn` lets you start the LLM early. If `TurnResumed` follows, you cancel. Vendor claims this saves 200 to 600 ms **[V]** ([eager EoT docs](https://developers.deepgram.com/docs/flux/voice-agent-eager-eot)).

### Barge-in (interruptions)

- **Pipecat.**
  - A turn start with `enable_interruptions=True` broadcasts a system-priority `InterruptionFrame`.
  - On that frame: the LLM stream is cancelled, function calls with `cancel_on_interruption=True` are cancelled, TTS buffers are cleared, and the transport flushes unplayed audio.
  - Only text that was actually played (tracked via `TTSTextFrame`s synced to playback) is committed to the assistant context.
  - Backchannel handling:
    - `MinWordsUserTurnStartStrategy(min_words=3)`;
    - Krisp VIVA interruption prediction;
    - mute strategies (`AlwaysUserMuteStrategy`, `FirstSpeechUserMuteStrategy`) to protect, for example, the opening disclosure.
  - Source: [Pipecat interruptions](https://docs.pipecat.ai/pipecat/fundamentals/interruptions.md).
- **LiveKit.**
  - `interruption.mode="adaptive"` is a barge-in model that separates real interruptions from "uh-huh" and "okay" acoustically, before a transcript exists. It is LiveKit Cloud only, with limited local dev use.
  - `min_duration` defaults to 0.5 s and `min_words` to 0.
  - False-interruption recovery: if VAD fired but no words arrived within `false_interruption_timeout` (2.0 s), the agent resumes where it left off (`resume_false_interruption=True`).
  - Sources: [adaptive interruption](https://docs.livekit.io/agents/logic/turns/adaptive-interruption-handling.md), [turns](https://docs.livekit.io/agents/build/turns/).
- **Twilio mechanics for a hand-rolled pipeline.**
  - Send a `clear` message to empty Twilio's buffered outbound audio; outstanding `mark`s are returned when you do.
  - Use `mark` messages to learn when each chunk finished playing, and therefore which words were heard.
  - Outbound media must be base64 `audio/x-mulaw` 8000 Hz with no header bytes.
  - Source: [Twilio Media Streams messages](https://www.twilio.com/docs/voice/media-streams/websocket-messages).
  - Cartesia word timestamps, ElevenLabs alignment and Flux TTS `text_spoken` give the same "what was heard" signal from the TTS side.

### Other latency levers seen in the frameworks and benchmarks

- **Match audio formats.** STT that takes μ-law 8 kHz natively (Deepgram, AssemblyAI) and TTS that emits it (Cartesia, ElevenLabs, Deepgram) avoid transcoding hops.
- **Noise and voice isolation before VAD/STT.** LiveKit recommends Krisp `BVCTelephony` for SIP callers; Pipecat recommends Krisp VIVA, ai-coustics or RNNoise over raising VAD thresholds.
- **Keep LLM reasoning off, prompts short and prefixes cached.** Reasoning modes add 0.6 to 3 s of TTFAT in aiewf. Sonnet 5 needs thinking explicitly disabled.
- **User turn limits** (`max_words`/`max_duration`) and idle-user detection handle monologues and silence. LiveKit's default cut-in is `on_user_turn_exceeded`; Pipecat has a user-idle processor.
- **Tail latency matters more than the median.** The stt-benchmark README states this directly. Several providers have P99 over 1.5 s (Cartesia Ink-2, Meta, Mistral) or tails of 4 to 9 s (Sonnet 4.6/5).

---

## Implications for the spec

1. **The ~1 s voice-to-voice target is feasible but tight with a cascade.** Using the published rule of thumb (V2V ≈ LLM TTFAT + ~500 ms), it is only met at the median with an LLM whose P50 TTFAT is ≤ ~500 ms:
   - gpt-4.1, open models on Groq or Baseten, or PhoneLLM, or
   - speculative generation plus short, cached prompts.
   - Haiku 4.5 lands at about 1.1 s median.

   The spec should state the target as P50 and P95 per turn, measured end to end on Twilio (for example P50 ≤ 1.0 s, P95 ≤ 2.0 s), rather than a single number.
2. **Geography is unmeasured and may dominate.** All providers above are US/EU-hosted. Round trips from UAE PSTN via Twilio to US endpoints could add hundreds of ms. The architecture ticket (15) needs a region decision: co-locate the server near the Twilio media edge and the provider endpoints.
3. **Pick a turn-detection architecture, not just an STT.** Two viable shapes:
   - (a) An STT with native EoT (Flux or AssemblyAI u3-rt-pro), plus local Silero VAD for barge-in.
   - (b) Any fast STT plus Silero plus Smart Turn v3 (open, BSD, Arabic/Hindi aware, but needs 16 kHz upsampling).

   LiveKit's audio turn detector and adaptive interruption model are tied to the LiveKit SDK/Cloud and are less portable to a hand-rolled stack.
4. **Barge-in requirements to put in the spec:**
   - on user speech: Twilio `clear`, then cancel the LLM and TTS;
   - commit only heard text to context, using marks or TTS timestamps;
   - backchannel tolerance (minimum words or duration);
   - false-interruption resume;
   - non-interruptible segments for the legally required opening disclosure (see issue 01).
5. **Tool-call integrity must be enforced in code.** Every benchmark shows models sometimes claiming actions they didn't take or re-asking for data they already have. Calendar booking should be confirmed by the tool result before the agent verbalises it, and evals (issue 05/16) need a case for this.
6. **Accent accuracy is the biggest unknown.** No independent data covers Gulf Arab, South Asian or Filipino English on 8 kHz audio. Provider selection (ticket 14) should run a bake-off of 3 or 4 STTs on real or recorded lead-call audio (issue 06), reporting semantic WER on names, emails, phone numbers and dates.
7. **Cost is low relative to telephony, excluding Twilio.** At the per-minute rates above:
   - STT: ~$0.002 to $0.008/min;
   - TTS: ~$0.015 to $0.05 per speaking-minute;
   - LLM: ~$0.004 to $0.05/min, using PhoneBench's estimates.

   The cascade is roughly $0.03 to $0.10/min. That is comparable to GPT-Live-1 at $0.05/min plus backend, bundled agents at $0.06 to $0.08/min, and gpt-realtime-2.1 (token-billed, grows with context). Cost probably shouldn't drive the choice. Latency, accent accuracy and control should.
8. **Speech-to-speech is a credible alternative only via GPT-Live-1.** It is new, measured only by the vendor, and delegates tools to a backend model. Existing realtime models measured at 1.15 to 1.6 s median V2V. A custom cascade keeps provider swap-ability and transcript/tool control, which matter for evals.

## Open uncertainties

- **Accent WER on 8 kHz μ-law** for all STTs. Unmeasured; needs our own test set.
- **End-to-end V2V from the UAE over Twilio.** No source measures it. Twilio edge and region choice sits in issue 02/15.
- **Deepgram Flux TTS pricing** after 2026-09-13, and whether `/v2/speak` emits mulaw 8 kHz. Not found on the pages read.
- **Soniox, Speechmatics Linden and Rime:** native μ-law 8 kHz support not confirmed in the sources read.
- **GPT-Live-1:** independent latency and quality numbers, SIP/Twilio specifics, delegation cost and latency. Only vendor claims and a community thread so far.
- **Benchmark neutrality.** The Pipecat/Daily benchmarks (including PhoneBench, where Daily's own PhoneLLM ranks #3) and Coval are the best available, but they are vendor-adjacent. Coval and Pipecat define "TTFS" differently.
- **Naturalness at 8 kHz.** Arena Elo is wideband; the phone-band ranking may differ. Needs listening tests on actual Twilio calls.
- **Anthropic Opus 5.5 fast mode and Gemini 3.8 Flash/Live** are not in any voice benchmark yet.
- **Price volatility.** Deepgram shows promo prices, Sonnet 5 changed pricing in September 2026, and AssemblyAI's "base" price suggests add-ons. Re-verify at selection time.
