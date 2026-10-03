# All-UAE low-latency voice stack

Type: research
Status: resolved
Map: ../map.md

## Question

Can the whole real-time voice chain run inside the UAE for the lowest possible latency, and with what components? The owner (2026-10-02) wants to drop cost as a constraint and hunt the lowest latency. Candidate: Core42 Compass models on Cerebras (non-thinking), with STT and TTS in the same UAE cloud (Azure UAE North or AWS me-central-1). Find out, from primary sources:

1. **LLM:** which Core42 Compass models run on Cerebras, and are they physically in the UAE? Measured or published time-to-first-token and tokens/sec; tool/function-calling support; non-thinking or low-reasoning modes; quality fit for a sales conversation agent; API access terms for a small company; data residency.
2. **STT in the UAE:** streaming speech-to-text that runs in Azure UAE North or AWS me-central-1:
   - Azure AI Speech region availability;
   - Amazon Transcribe streaming in me-central-1;
   - Deepgram self-hosted;
   - other vendors' UAE or ME regions;
   - open-source models self-hosted on UAE GPUs (and whether GPU VMs are available there).
   For each: latency, 8kHz telephony support, end-of-turn detection.
3. **TTS in the UAE:**
   - Azure Neural TTS in UAE North;
   - Amazon Polly in me-central-1;
   - ElevenLabs data residency or regions (is there a UAE/ME region?);
   - Cartesia on-prem/self-hosted;
   - open-source TTS self-hosted.
   For each: time to first audio, naturalness, male international/British voices.
4. **Telephony in the UAE:** Twilio's media servers are in Ireland (no ME edge), so an all-UAE chain needs the call audio to terminate in the UAE: an e&/du SIP trunk into a media server/SBC we run in a UAE cloud region. Open-source media/SIP options (FreeSWITCH, Asterisk, Jambonz, Kamailio + rtpengine, LiveKit SIP for reference), and whether e&/du SIP trunks can terminate on Azure UAE North / AWS me-central-1. Does any CPaaS offer media in the UAE?
5. **Latency estimate:** an end-to-end per-turn latency estimate for the all-UAE chain vs the current plan (Twilio IE1 + Dublin + Deepgram + DeepSeek on a US/EU host + Cartesia).

Also note in passing: DeepSeek's first-party API location and typical latency from the UAE (the owner floated "DeepSeek official API" for a simple v1).

## Answer

Researched 2026-10-02. These are options, not a decision.

- **Compass on Cerebras is not in the UAE.** Both Cerebras-served models on Compass (`gpt-oss-120b-cerebras`, `k2-think-cerebras`) are listed as USA. That adds about 180–240 ms of round trip from Dubai per LLM call, and neither model is in Compass's function-calling list. Cerebras hardware in the UAE (Stargate UAE) is announced but unconfirmed as live.
- **In-UAE LLM options:**
  - Compass serves GPT-4.1, GPT-5.1, DeepSeek V4 Pro, GLM-5.2, Mistral Small 3.2 and K2 Horizon from the UAE, most with tool calling. Their latency on Compass has never been measured.
  - The fastest measured option is self-hosting an open model on a UAE GPU. Qwen3.8-27B with thinking off scored 97.8 % at about 100 ms to first token on a local GPU, on a par with Haiku 4.5's accuracy.
  - Azure UAE North lists H100, RTX PRO 6000 Blackwell and A10 VMs.
- **STT in the UAE:**
  - Azure Speech (uaenorth) is the only managed option, and it is slow: about 1 s to final transcript.
  - Amazon Transcribe streaming is not in me-central-1.
  - Fast STT in the UAE means self-hosting: Deepgram Flux/Nova under an Enterprise contract, or NVIDIA Nemotron plus our own turn detection.
  - The nearest managed fast option is Deepgram's India endpoint, about 30–50 ms away.
- **TTS in the UAE:**
  - Azure Neural TTS (uaenorth) is the only managed option. It has standard en-GB male voices (Ryan, Thomas, Oliver and others) and μ-law 8 kHz output, but no HD voices, mid-table naturalness and unpublished latency.
  - There is no Polly in me-central-1.
  - ElevenLabs has no Middle East region and no self-hosting.
  - Cartesia Sonic-3.6 can be deployed on-prem or in our own Azure/AWS account (Enterprise), as can Deepgram Flux TTS.
- **Telephony:**
  - All-UAE requires an e&/du SIP trunk into our own media server in a UAE region. Candidates are Asterisk `chan_websocket`, FreeSWITCH `mod_audio_fork` or Jambonz `listen`, all bridging to a Python WebSocket.
  - Whether e&/du will deliver a trunk to a cloud VM is unconfirmed. Both are Azure ExpressRoute providers in Dubai/Abu Dhabi, so a private path exists.
  - No CPaaS with confirmed in-UAE media plus a UAE caller ID was found. LiveKit Cloud has a UAE location but brings no numbers.
- **Latency estimate (median voice-to-voice, excluding the mobile network):**
  - Current plan (Twilio IE1 + Dublin + Flux + DeepSeek V4.1 Flash + Cartesia cloud): about 1.4–1.7 s.
  - Best all-UAE (self-hosted Flux + Qwen + Cartesia on-prem in UAE North): about 0.5–0.7 s.
  - All-UAE with Compass GPT-4.1: about 1.0–1.1 s.
  - All-UAE using only Azure managed speech: about 1.7–2.0 s, which is *slower* than today.
  - Geography alone is worth about 120–200 ms; most of the gain is the faster LLM.
- **Going all-UAE reopens ticket 17** (it dropped the self-hosted route) and adds a carrier question to ticket 22: will the trunk land in Azure UAE North or AWS me-central-1? It also brings Enterprise contracts and GPU operations.
- **DeepSeek first-party API:** stores data in China and is far from the UAE (latency unmeasured; above 113 ms round trip, since even Hong Kong is that far). Its peak-price hours fall at 10:00–14:00 Dubai time. Cheap for a v1, but the opposite of low latency.

[findings](../research/25-all-uae-low-latency-stack.md)
