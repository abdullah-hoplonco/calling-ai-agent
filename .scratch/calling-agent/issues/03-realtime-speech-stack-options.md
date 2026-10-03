# Real-time STT, TTS and LLM options for a custom voice pipeline

Type: research
Status: resolved
Map: ../map.md

## Question

Which streaming STT, TTS and LLM providers (and speech-to-speech realtime models, for comparison) are viable for a custom low-latency phone agent? For each: streaming latency (time-to-first-token/byte), cost per minute or token, 8kHz telephony audio support (mulaw), accuracy on UAE-typical English accents (Gulf Arab, South Asian, Filipino, Western), endpointing/turn-detection and barge-in support, tool/function calling (LLM), and voice naturalness (TTS). Also summarise how reference frameworks (Pipecat, LiveKit Agents) solve turn-taking, interruption and latency, as design input for a hand-rolled pipeline.

## Answer

- **STT:** the options that fit a Twilio phone agent are AssemblyAI Universal-3.5 Pro Realtime, Deepgram Flux or Nova-3, Soniox, Speechmatics Linden and Cartesia Ink-2.
  - All cost about $0.002–0.008/min.
  - In independent tests they return the final transcript about 250–370 ms after the caller stops speaking.
  - AssemblyAI and Deepgram accept Twilio's 8 kHz μ-law audio directly and detect end of turn themselves.
- **Accent accuracy:** no independent data exists for Gulf Arab, South Asian or Filipino English on phone audio. This is the biggest unknown, so provider selection needs a head-to-head test on our own lead-call samples.
- **TTS:** the options are Cartesia Sonic-3.6, ElevenLabs Flash v2.5 or v3 Conversational, Deepgram Flux TTS or Aura-2, and Rime.
  - Cartesia Sonic-3.6 ranks #1 in the blind naturalness arena.
  - ElevenLabs Flash v2.5 is fastest among the naturalness leaders at about 190 ms to first audio.
  - Cartesia, ElevenLabs and Deepgram output 8 kHz μ-law natively. Cost is about $0.03–0.05 per 1k characters.
- **LLM:** the rule of thumb is voice-to-voice latency ≈ time to first LLM token + ~500 ms.
  - claude-haiku-4-5: about 640 ms median to first token, 98% on the multi-turn tool benchmark. That gives about 1.1 s voice-to-voice.
  - claude-sonnet-5 (thinking must be disabled): about 1.2 s to first token. Too slow at the median.
  - gpt-4.1, gpt-5.6-luna, Gemini 3.6 Flash and open models on Groq or Baseten trade speed against tool accuracy.
  - Every model sometimes claims actions it didn't take, so a calendar booking must be confirmed by the tool result in code before the agent says it is booked.
- **Speech-to-speech:** measured realtime models (gpt-realtime-2.1, Gemini Live) run about 1.15–1.6 s median voice-to-voice.
  - OpenAI's GPT-Live-1 ($0.05/min plus backend model, launched 2026-09-10) claims about 0.8 s but has no independent measurement yet.
  - A custom cascade can match that speed and keeps more control.
- **Turn-taking approaches to borrow:**
  - Local Silero VAD plus an end-of-turn model. Smart Turn v3 is open source but needs 16 kHz input. The alternative is STT-native end of turn such as Deepgram Flux or AssemblyAI.
  - Speculative generation: LiveKit's preemptive generation, or Deepgram Flux's early end-of-turn signal.
  - Adaptive or minimum-word barge-in filtering, so "uh-huh" doesn't interrupt the agent.
  - False-interruption resume.
  - Commit only the words the caller actually heard, tracked with Twilio `mark` messages and cleared with `clear`.
- **Spec implications:**
  - State the latency target as P50 and P95 measured end to end over Twilio from the UAE. Server and provider region is unmeasured and may dominate.
  - Cost probably shouldn't drive the choice: the cascade is about $0.03–0.10/min before Twilio. Latency, accent accuracy and control should.
- Final provider choice is deferred to the provider-selection ticket (14).

[findings](../research/03-realtime-speech-stack-options.md)
