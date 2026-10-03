# Use LiveKit Agents instead of hand-written real-time orchestration

We originally chose to hand-write the real-time voice orchestration (streaming loop, turn-taking, interruptions) as a learning and portfolio exercise, with LiveKit and Pipecat as reference reading only. On 2026-10-02 the owner reversed this to cut delivery risk and effort ("lower the headache; learning later"). The Calling Agent is now built on the open-source **LiveKit Agents** framework (Apache 2.0) and LiveKit's SIP service, with calls bridged from Twilio over Elastic SIP Trunking.

What stays ours: the code-owned call state machine and compliance guards (ADR 0001) run inside the LiveKit agent, along with the domain model, dialer, data model and evals. LiveKit's plugins connect Deepgram (EU), Cartesia (EU) and our self-hosted LLM (OpenAI-compatible endpoint).

## Considered options

- Hand-written orchestration: most learning and control, but the highest risk to latency quality and to the timeline.
- Pipecat: comparable framework; LiveKit was preferred for its built-in turn-detector model, preemptive generation, SIP stack and a managed cloud option.
- Hosted platforms (Vapi/Retell): rejected earlier; some block UAE calls.

## Consequences

- Twilio Media Streams is replaced by Twilio Elastic SIP Trunking → LiveKit SIP.
- The "text-mode seam" for evals uses LiveKit's own agent testing support where it fits.
- Moving to an e&/du trunk in v2 is a SIP trunk change in LiveKit, not a rewrite.
