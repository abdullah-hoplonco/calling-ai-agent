# All-UAE low-latency voice stack: findings

Ticket: [25-all-uae-low-latency-stack](../issues/25-all-uae-low-latency-stack.md)
Researched: 2026-10-02. Builds on [02](02-twilio-uae-outbound.md) (Twilio) and [03](03-realtime-speech-stack-options.md) (STT/TTS/LLM benchmarks); numbers from those are not re-derived here.

**Tags.** **[V]** = vendor-claimed. **[I]** = measured by a third party with a published method (mostly the Pipecat/Daily benchmarks, which are vendor-adjacent; see 03). **[est]** = my estimate, not measured by anyone. **Unconfirmed** = I could not find a primary source saying the service runs in a UAE region.

**Network distances used throughout.** Microsoft publishes P50 (median) round-trip times between its regions, measured on its own backbone over the 30 days to 2026-07-30 ([Azure network latency](https://learn.microsoft.com/en-us/azure/networking/azure-network-latency), source file on [GitHub](https://github.com/MicrosoftDocs/azure-docs/blob/main/articles/networking/azure-network-latency.md)). From UAE North (Dubai):

| To | Round trip (ms) |
|---|---|
| UAE Central (Abu Dhabi) | 6 |
| Qatar Central | 15 |
| Central India (Pune) / South India (Chennai) | 32 / 50 |
| Germany West Central (Frankfurt) | 100 |
| North Europe (Dublin) | 121 |
| East Asia (Hong Kong) | 113 |
| East US / South Central US (Texas) / West US (California) | 176 / 214 / 236 |

And from North Europe (Dublin) to East US 73, South Central US 104, West US 133. These are backbone figures; the public internet and international phone routes are usually slower.

---

## TL;DR

- **"Core42 Compass on Cerebras" is not in the UAE.** Both Cerebras-served models on Compass (`gpt-oss-120b-cerebras`, `k2-think-cerebras`) are listed with location **USA**. A call routed that way goes UAE → Compass gateway (UAE North) → Cerebras in the US → back, about 180–240 ms of extra round trip per LLM call. Neither model appears in Compass's function-calling list.
- **A fully in-UAE chain is technically possible today, but only by self-hosting STT, LLM and TTS on GPUs in Azure UAE North.** The managed (hosted) speech services there are either missing (AWS) or slow (Azure STT measured at about 1 s to final transcript).
- **The best self-hosted all-UAE chain is estimated at about 0.5–0.7 s voice-to-voice median, against about 1.4–1.7 s for the current plan.** Most of that gain comes from a faster LLM and a co-located TTS, not from geography. Geography itself is worth about 120–200 ms per turn.
- **An all-UAE chain needs an e&/du SIP trunk landing on our own media server in the UAE.** That reverses ticket 17's "Twilio all the way" decision and depends on carrier facts nobody has confirmed yet (ticket 22).

---

## 1. LLM: Core42 Compass and other in-UAE options

### 1a. What Compass serves, and where

All from the Compass docs: [Models](https://www.core42.ai/compass/documentation/compass-models), [Overview](https://www.core42.ai/compass/documentation/compass-overview), [Pricing](https://www.core42.ai/compass/documentation/compass-model-pricing), [Function Calling](https://www.core42.ai/compass/documentation/function-calling), [2026 changelog](https://www.core42.ai/compass/documentation/compass-changelog).

| Model on Compass (ID) | Hosting | Location per Compass | Function calling listed? | Price per 1M in / out [V] | Voice-agent benchmark (aiewf, from 03) [I] |
|---|---|---|---|---|---|
| `gpt-oss-120b-cerebras` | Cerebras | **USA** | No | $0.25 / $0.69 | gpt-oss-120b on Groq: 86.3 % pass, 98 ms P50 TTFAT (time to first answer token) |
| `k2-think-cerebras` (K2 Think V2, 70B) | Cerebras | **USA** ("deployed and running on the Cerebras in the US region") | No | $0.15 / $0.50 | Not benchmarked. A reasoning ("thinking") model, so a poor fit for voice |
| `gpt-oss-120b-core42` / `-core42-amd` / `-qualcomm` | Core42 GPUs / AMD / Qualcomm | UAE | No | $0.15–0.30 / $0.37–0.75 | Same model as above; serving speed on these back-ends not measured |
| `gpt-4.1` | Azure OpenAI via Core42 | UAE | Yes | $2.00 / $8.00 | 96.3 %, 536 ms P50 / 1771 ms P95 (measured on OpenAI's own API, not Compass) |
| `gpt-4.1-mini` | same | UAE | Not in the list (the changelog calls it "optimized for … tool calling") | $0.40 / $1.60 | 85.3 %, 851 ms |
| `gpt-5.1` | same | UAE | Not in the list | $1.25 / $10.00 | 98.0 %, 739 ms (OpenAI API) |
| `deepseek-v4-pro` | Core42 | UAE (onboarded 2026-06-25) | Yes | $1.91 / $3.83 | V4 Pro (low reasoning) on Baseten: 97.3 %, 752 ms P50 |
| `glm-5.2` | Core42 | UAE | Yes | $1.54 / $4.84 | glm-5.2 (none) on Baseten: 99.7 %, 936 ms P50 / 2140 ms P95 |
| `mistral-small-3.2` | Core42 | UAE | Yes | $0.12 / $0.36 | Not benchmarked |
| `k2-horizon-375b` | Core42 | UAE (onboarded 2026-09-07) | Yes | $0.15 / $0.50 | Not benchmarked |
| GPT-5.5 / 5.6 Sol / Terra / Luna | Azure | **Sweden Central** | Yes | — | 5.6 Luna (none) 88.3 %, 671 ms |
| Claude Sonnet/Opus 4.6, Opus 4.8 | — | **"Global"** | Yes | — | No Claude Haiku on Compass |
| `gpt-realtime` (speech-to-speech) | Azure | **Sweden Central** | — | — | — |

Benchmark source: [aiewf-eval README](https://github.com/kwindla/aiewf-eval), which measures TTFAT from its own test location to each provider. **No benchmark has measured Compass's serving speed for any model.** The aiewf numbers are for the same model weights on a different host.

**Physical location of Compass.**
- Core42 says "Compass runs in Azure UAE with in-country data residency … and zero customer data logging" ([brochure page](https://www.core42.ai/resources/whitepapers/compass-brochure-download)) [V].
- `api.core42.ai` resolves (DNS lookup on 2026-10-02) to an Azure Traffic Manager name ending `-uan` (UAE North). That is consistent with a UAE North gateway, but is my inference.
- Per-model location still varies (USA, Sweden Central, Global), so "on Compass" does not mean "in the UAE".

**Is Cerebras hardware in the UAE?**
- Cerebras plans to supply the Stargate UAE campus, whose first 200 MW was expected in 2026 ([Investing.com/Reuters](https://www.investing.com/news/stock-market-news/cerebras-aims-to-deploy-ai-infrastructure-for-massive-stargate-uae-data-centre-hub-4289558); [DCD on eased export controls](https://www.datacenterdynamics.com/en/news/us-govt-eases-ai-chip-export-controls-on-uae-following-countrys-support-in-iran-war/)). Secondary reporting said "no systems were deployed in the UAE due to restrictions on export licensing".
- Core42 AI Cloud lists "Cerebras WSE-3 — Price: On Request" ([aicloud.core42.ai](https://aicloud.core42.ai/)) without a location.
- Cerebras's published inference sites are in North America and Europe ([Cerebras press release](https://www.cerebras.ai/press-release/cerebras-announces-six-new-ai-datacenters-across-north-america-and-europe-to-deliver-industry-s)).
- **Cerebras inference inside the UAE: unconfirmed.** Ask Core42 directly.

**Cerebras speed.**
- The Cerebras public catalogue lists `gpt-oss-120b` (~3000 tok/s) and `qwen-3.8-27b` (~1850 tok/s) [V] ([Cerebras model catalog](https://inference-docs.cerebras.ai/models/overview)).
- Artificial Analysis measured gpt-oss-120b on Cerebras at 1,815 tok/s output, with 1.51 s to first token on a 10k-token reasoning (High) workload [I] ([AA providers](https://artificialanalysis.ai/models/gpt-oss-120b/providers)). That workload includes reasoning time, so it is not a voice-mode figure.
- Throughput (tokens per second) barely matters for voice, because replies are short. Time to first token and network distance dominate.

**Access terms for a small company.**
- Self-serve account sign-up. Each model is then subscribed either "via Sales Team" or through Azure Marketplace pay-as-you-go, and "the Compass team will review and approve the subscription" ([Get Started](https://www.core42.ai/compass/documentation/compass-get-started)).
- The FAQ says "You need API key and an active subscription", and that a Core42 AI Cloud subscription "currently provides access to four specific models: gpt-oss-120b, gpt-oss-20b, K2 Think, Grok 2.5" ([API FAQs](https://www.core42.ai/compass/documentation/compass-api-faqs)).
- Rate limits are per-deployment TPM (tokens per minute). Reserved-capacity (TPM) traffic is prioritised over pay-as-you-go (changelog, 2026-04-30). Pay-as-you-go traffic may therefore see worse latency under load (my inference).
- The API is OpenAI-compatible (`base_url="https://api.core42.ai/v1"`).

**Non-thinking modes.** GPT-4.1 and GPT-4.1-mini have no reasoning step ("low-latency responses without a dedicated reasoning step", [overview](https://www.core42.ai/compass/documentation/compass-overview)). For DeepSeek V4 Pro and GLM-5.2, whether Compass exposes a thinking-off or low-effort control is **not documented** on the pages read.

### 1b. Self-hosting an open model on a UAE GPU

This is the fastest in-UAE option found.

- **Measured:** `qwen3.8-27b` with thinking off, NVFP4 quantisation, on one RTX 5090: **97.8 % pass, 101 ms P50 / 318 ms P95 TTFAT** [I]. The test ran over localhost with no network ([aiewf-eval](https://github.com/kwindla/aiewf-eval)). The same model on Baseten H100s scored 98.2 % at 649 ms, which includes the provider's network and queueing.
- **Measured:** `gemma-4-31b-it` locally: 96.2 %, 127 ms P50 [I].
- For comparison, claude-haiku-4-5 scores 98.0 % at 637 ms and DeepSeek V4 Flash (low) 96.7 % at 677 ms ([aiewf-eval](https://github.com/kwindla/aiewf-eval)).
- **GPUs in Azure UAE North.** The official Azure retail price API (`prices.azure.com`, queried 2026-10-02, `armRegionName eq 'uaenorth'`) lists:
  - RTX PRO 6000 Blackwell sizes (`Standard_NC24lds_xl_RTXPRO6000BSE_v6` $1.62/h up to multi-GPU);
  - `Standard_NC40ads_H100_v5` ($9.98/h);
  - ND H100/H200/MI300X 8-GPU nodes;
  - A10 `NV*ads_A10_v5` sizes (fractional A10s).

  A price listing is not a capacity or quota guarantee. A quota request is needed.
- **Benchmark vs our hardware.** The RTX 5090 in the benchmark is a consumer card. RTX PRO 6000 Blackwell is the same generation, so the latency should be of the same order. **Unverified.**
- **GPUs in AWS me-central-1.** Third-party catalogue [instances.vantage.sh](https://instances.vantage.sh/aws/ec2/g6e.xlarge) (built from AWS pricing data) shows g5 (A10G), g6 (L4) and g6e (L40S) as available in me-central-1. It shows g4dn, p4d, p5, p5e, p6-b200 and g7e as not available there. Confirm with `aws ec2 describe-instance-type-offerings --region me-central-1`.
- **Core42 AI Cloud** advertises H100 "from $2.50/hr" and B200 "from $5.00/hr" ([aicloud.core42.ai](https://aicloud.core42.ai/)) [V]. Whether those GPUs are in the UAE is **unconfirmed**: the page says "thousands of GPUs globally".

**Quality fit for a sales conversation (judgement, not measured).**
- The open 27–31B models score on par with Haiku 4.5 on aiewf (multi-turn tool use, instruction following).
- Nobody has measured persuasion, tone or handling of objections. gpt-oss-120b's 13.7 % error rate (mostly instruction errors) makes it the weakest candidate.
- Any choice needs our own evals (ticket 16).

### 1c. DeepSeek first-party API (noted in passing)

- **Model and modes.** `deepseek-flash` = DeepSeek-V4.1-Flash, with non-thinking and thinking (default) modes and tool calls. Base URL `https://api.deepseek.com` ([DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing)).
- **Price** (per 1M tokens): off-peak $0.15 in (cache miss) / $0.60 out. Peak is double: 06:00–10:00 UTC, which is **10:00–14:00 Dubai time, inside our 09:00–18:00 calling window**.
- **Location.** DeepSeek's privacy policy says "we directly collect, process and store your Personal Data in People's Republic of China" ([privacy policy](https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html)). That policy is written for its consumer services; API terms were not read.
- **Latency from the UAE: unmeasured.** UAE North → Hong Kong is 113 ms round trip on Azure's backbone, which is a lower bound for mainland China. Artificial Analysis lists the first-party API at 0.95 s to first token and 209 tok/s [I] ([AA](https://artificialanalysis.ai/models/deepseek-v4-1-flash/providers)), but for the "(Max)" reasoning variant from its own (non-UAE) test site, so it is not a non-thinking figure.
- **Fit.** For a v1 this is a cheap but far-away, non-UAE-resident option. It is the opposite of the low-latency goal.

---

## 2. STT in the UAE

| Option | Runs in UAE? | Latency | 8 kHz telephony | End-of-turn detection |
|---|---|---|---|---|
| **Azure AI Speech, real-time STT** | **Yes: `uaenorth`** has real-time transcription ([Azure Speech regions](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/regions); [GitHub source](https://github.com/MicrosoftDocs/azure-ai-docs/blob/main/articles/ai-services/speech-service/regions.md)). Microsoft: data "is stored or processed only in the region where the resource is created" | **1016 ms median / 1345 P95 TTFS** (time to final segment) [I] ([Pipecat stt-benchmark](https://github.com/pipecat-ai/stt-benchmark)), vs ~250 ms for Deepgram/Soniox. Possibly tunable via the segmentation silence timeout (not tested) | PCM 16-bit at 8,000 or 16,000 Hz ([audio input streams](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-use-audio-input-streams)); μ-law must be decoded to PCM first (trivial) | Silence-based segmentation. "Semantic segmentation" exists but "shouldn't be used in … interactive scenarios" ([docs](https://github.com/MicrosoftDocs/azure-ai-docs/blob/main/articles/ai-services/speech-service/includes/how-to/recognize-speech/python.md)), so bring your own turn model |
| **Amazon Transcribe streaming** | **No.** me-central-1 is not in the streaming endpoint list, nor in the batch list. Bahrain (me-south-1) is batch only ([Transcribe endpoints](https://docs.aws.amazon.com/general/latest/gr/transcribe.html)) | AWS streaming: 1136 ms median TTFS [I] ([stt-benchmark](https://github.com/pipecat-ai/stt-benchmark)) | — | — |
| **Deepgram self-hosted** (Nova-3, Flux) | **Possible**, on our own GPU VM in the UAE. Needs a Deepgram **Enterprise plan**. Containers call a Deepgram licence server, but "no audio, transcripts … are sent to Deepgram" ([self-hosted intro](https://developers.deepgram.com/docs/self-hosted-introduction), via search snippet; page unreachable from here). Docs name AWS, GCP and own data centres; Azure is not named in what I read | Same models as the cloud. Flux EoT about 260 ms P50 [V]; Nova-3 247 ms median TTFS [I] | Yes: mulaw 8000 (cloud API; assumed the same self-hosted) | Flux has model-based EoT built in. Flux self-hosted needs an Ampere-or-newer GPU (A10, L4, L40S, A100, H100, Blackwell; not T4) and **its own dedicated node** ([Flux self-hosted](https://developers.deepgram.com/docs/flux-self-hosted), via search snippet) |
| **Deepgram cloud, regional endpoints** | **No ME region.** EU, Australia and **India** (`api.in.deepgram.com`, AWS ap-south-2 Hyderabad; "no waitlist and no enterprise-only restriction"; supports `/v2/listen` and `/v2/speak`) ([India GA post](https://deepgram.com/learn/deepgram-india-endpoint-now-generally-available); [EU GA post](https://deepgram.com/learn/deepgram-eu-endpoint-now-generally-available)) | UAE → India is about 32–50 ms round trip (Azure figures to Pune/Chennai; Hyderabad not in the table) | Yes | Flux EoT |
| **Other hosted STT vendors** (AssemblyAI, Soniox, Speechmatics, Cartesia Ink) | **No UAE region found** in the sources read for this ticket. Cartesia: regional endpoints US, EU, UK, India, Australia (Enterprise) ([Cartesia regional endpoints](https://docs.cartesia.ai/enterprise/regional-endpoints.md)) | see 03 | see 03 | see 03 |
| **Open-source on a UAE GPU**: NVIDIA Nemotron streaming ASR 0.6B | **Possible** (Azure UAE North GPUs above). NVIDIA Open Model License, "ready for commercial/non-commercial use" ([model card](https://huggingface.co/nvidia/nemotron-speech-streaming-en-0.6b)) | Nemotron 3.0 ASR (en): **221 ms median / 238 P95 / 252 P99** TTFS, the tightest tail in the benchmark, with 1.9 % pooled WER [I] ([stt-benchmark](https://github.com/pipecat-ai/stt-benchmark)) | Model card does not state 8 kHz; trained on en-US. Expect to upsample 8 kHz to 16 kHz; accuracy on narrowband audio untested | None built in. Pair with Silero VAD + Smart Turn v3 (see 03) |
| Compass `whisper-1` / `gpt-4o-transcribe` | Whisper: UAE; gpt-4o-transcribe: Global ([Compass models](https://www.core42.ai/compass/documentation/compass-models)) | File upload only ([Compass Audio](https://www.core42.ai/compass/documentation/audio)); not streaming | — | — |

**Takeaway.** Within the UAE, the only *managed* streaming STT is Azure Speech, and it is about 4× slower to a final transcript than the leaders. Fast STT inside the UAE means self-hosting: Deepgram under an Enterprise contract, or Nemotron plus our own turn detection. The nearest managed fast option is Deepgram India, about 30–50 ms away.

---

## 3. TTS in the UAE

| Option | Runs in UAE? | Time to first audio | Naturalness (Artificial Analysis arena Elo, blind preference, wideband) [I] | Male British / international voices | 8 kHz μ-law out |
|---|---|---|---|---|---|
| **Azure Neural TTS** | **Yes: `uaenorth`** has neural TTS, batch synthesis and custom voice. **No** HD voices, MAI voices, Azure OpenAI voices or Voice Live in uaenorth ([regions](https://github.com/MicrosoftDocs/azure-ai-docs/blob/main/articles/ai-services/speech-service/regions.md)) | **Not published** by Microsoft. It documents how to measure it (`SynthesisFirstByteLatencyMs`) and offers text streaming over `wss://{region}.tts.speech.microsoft.com/cognitiveservices/websocket/v2` ([latency guide](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-lower-speech-synthesis-latency)). Unmeasured | Azure Neural: **1033** (rank 66). Azure HD 2.5: 1129, but HD is not in uaenorth ([AA leaderboard](https://artificialanalysis.ai/text-to-speech/leaderboard), read 2026-10-02) | en-GB male: Ryan, Thomas, Alfie, Elliot, Ethan, Noah, Oliver; OllieMultilingual (multilingual voice; uaenorth availability not confirmed) ([voice list](https://github.com/MicrosoftDocs/azure-ai-docs/blob/main/articles/ai-services/speech-service/includes/language-support/tts.md)) | Yes: `raw-8khz-8bit-mono-mulaw` ([REST formats](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech)) |
| **Amazon Polly** | **No.** me-central-1 is not in the endpoint list. Bahrain (me-south-1) has it ([Polly endpoints](https://docs.aws.amazon.com/general/latest/gr/pol.html)) | — | Polly Generative 1063; Neural 893 | — | — |
| **ElevenLabs** | **No ME region.** Global routing via "USA, Netherlands and Singapore". Data-residency environments are EU, India and Singapore, Enterprise only ([latency guide](https://elevenlabs.io/docs/eleven-api/guides/how-to/best-practices/latency-optimization); [IP allowlisting](https://elevenlabs.io/docs/eleven-api/resources/ip-allowlisting)). No self-hosted option found | Flash v2.5 ~75 ms model time [V]; 100–150 ms TTFB from Europe/SE Asia, 150–200 ms from South Asia [V] | Flash v2.5 1076; v3 Conversational 1200; Eleven v4 1320 (#1) | Large library | `ulaw_8000` |
| **Cartesia Sonic-3.6, on-prem/VPC** | **Possible.** "Sonic-3.6 can be deployed on-prem inside your data center (including air-gapped environments), in your own VPC on AWS/GCP/Azure" ([Sonic FAQ](https://cartesia.ai/sonic)). Enterprise, custom pricing ([pricing FAQ](https://cartesia.ai/pricing)). Hosted regional endpoints: US, EU, UK, India, Australia ([regional endpoints](https://docs.cartesia.ai/enterprise/regional-endpoints.md)) | "sub-90ms model latency" [V]. Coval TTFA over the public API: 297 ms median [I] (see 03) | **1273** (#3) | Voice library (see ticket 24) | `pcm_mulaw` 8000 (cloud API) |
| **Deepgram Flux TTS / Aura-2, self-hosted** | **Possible** under Deepgram Enterprise. Flux TTS needs an L4, L40S, A100, H100 or Blackwell GPU (not T4/A10) and ≥ 64 GB RAM ([search snippet of Deepgram self-hosted docs](https://developers.deepgram.com/docs/deploy-tts-services)) | Flux TTS 80 ms first response [V]; Coval 268 ms over the public API [I] (see 03) | Not on the main board | Aura-2 voices; British male options not checked | mulaw 8000 (v1); unverified for `/v2/speak` |
| **Open source on a UAE GPU** | **Possible** | Kokoro 82M: small and fast (no measured TTFA found here). Breeze TTS 2: "sub-40 millisecond time to first audio" on H100 [V], but **weights are non-commercial** ([MindStudio summary](https://www.mindstudio.ai/blog/breeze-tts-2-open-weight-model); secondary) | Kokoro 1063; Breeze TTS 2 1206 (top open-weights); Fish Audio S2 Pro 1117 | Kokoro has a few British voices (not evaluated) | Resample 24 kHz → 8 kHz μ-law ourselves |
| Compass `gpt-4o-mini-tts` | Global, not UAE | — | — | — | No μ-law output listed ([Compass Audio](https://www.core42.ai/compass/documentation/audio)) |

**Takeaway.** The only *managed* TTS in the UAE is Azure Neural TTS (standard voices, mid-table naturalness, latency unpublished). A top-naturalness voice inside the UAE means a Cartesia or Deepgram Enterprise self-hosted deployment. ElevenLabs cannot run in the UAE.

---

## 4. Telephony in the UAE

**Constraint.** Twilio has no Middle East edge or region; Media Streams run in US1, IE1 and AU1 (see [02](02-twilio-uae-outbound.md)). An all-UAE chain therefore needs call audio to end at a server **in the UAE**:

UAE caller → e& or du network → **SIP trunk** (the carrier's digital phone line, delivered as SIP signalling plus RTP audio) → our **media server / SBC** (session border controller: the machine that accepts the carrier's trunk and handles the audio) in Azure UAE North or AWS me-central-1 → WebSocket audio into our Python voice server.

### 4a. Carriers

| | du Business SIP Trunk | e& (Etisalat) SIP trunk |
|---|---|---|
| Public offer | 10–100 channels; Business SIP 10 = AED 580/month + VAT, AED 1,000 activation; "Unlimited local and national calls", per-second billing, 12-month contract ([du.ae/siptrunk](https://www.du.ae/siptrunk)) | No public price; via account manager ([e& unified communications](https://www.etisalat.ae/en/enterprise-and-government/enterprise-solutions/unified-communications.html)) |
| Equipment | "we don't provide PBX … you can always purchase your own PBX" (same du page) | Delivered as a dedicated line to a PBX WAN port (vendor how-to: [Yeastar](https://support.yeastar.com/hc/en-us/articles/22351844995609-How-to-configure-Ims-etisalat-ae-sip-dedicated-line-to-connected-to-PBX-WAN-port-with-DHCP-mode)) |
| VoIP caveat | du FAQ: "VOIP calls on SIP are currently not permitted in the UAE." This reads as a ban on internet-calling apps over the trunk, not on terminating the trunk on our own server. **Interpretation unconfirmed** | — |
| Can it land in Azure UAE North / AWS me-central-1? | **Unconfirmed.** Indirect evidence that a private path exists: **du datamena** and **Etisalat UAE** are both Azure ExpressRoute connectivity providers (private circuits into Azure) at Dubai/Abu Dhabi peering locations that map to UAE North and UAE Central ([ExpressRoute providers](https://learn.microsoft.com/en-us/azure/expressroute/expressroute-locations-providers)). AWS Direct Connect has UAE locations at Equinix DX1 Dubai and Etisalat SmartHub Fujairah ([AWS Dubai](https://aws.amazon.com/about-aws/whats-new/2018/08/aws-direct-connect-now-in-dubai/); [AWS Fujairah](https://aws.amazon.com/pt/about-aws/whats-new/2018/10/aws-direct-connect-live-in-fujairah-uae/)). Whether e&/du will carry a *voice* trunk over such a circuit, or over the internet to a cloud IP, has to be asked (ticket 22) | same |

Microsoft Teams in the UAE works only through Direct Routing with e&/du SIP connectivity; Operator Connect is not offered there (secondary: [GRIT](https://www.gritservices.ae/blog/microsoft-teams-phone-system-uae-cloud-calling-2025/)). This shows the carriers do hand trunks to customer-run SBCs. It does not show that they will do so in a public cloud.

### 4b. Open-source media / SIP servers that bridge to a Python WebSocket

| Option | How audio reaches our Python | Notes |
|---|---|---|
| **FreeSWITCH** + `mod_audio_fork` or `mod_audio_stream` | WebSocket, L16 PCM, 8–64 kHz, **bidirectional** (playback of returned audio, markers) ([mod_audio_fork](https://github.com/W1ck3dZA/mod_audio_fork); [mod_audio_stream](https://github.com/amigniter/mod_audio_stream)) | Mature SIP stack. The audio modules are community or commercial add-ons, not core FreeSWITCH. One fork claims about 1,000 calls per box ([lazyboson](https://github.com/lazyboson/mod_audio_fork)) [V] |
| **Asterisk** (ARI + `chan_websocket` external media) | WebSocket: binary frames for media, text frames for control. AudioSocket (TCP) and RTP are alternatives that need you to handle packet timing yourself ([Asterisk WebSocket channel](https://docs.asterisk.org/Configuration/Channel-Drivers/WebSocket/); [examples](https://github.com/asterisk/asterisk-websocket-examples)) | First-party, in core Asterisk. Closest in shape to Twilio Media Streams |
| **Jambonz** (open-source CPaaS built on FreeSWITCH + drachtio) | `listen` verb: WebSocket, bidirectional by default, configurable sample rate ([Jambonz listen](https://docs.jambonz.org/verbs/verbs/listen)) | Gives a Twilio-like call-control API (place call, status webhooks). Self-host instructions exist for AWS ([docs](https://www.jambonz.org/docs/webhooks/overview/)) |
| **Kamailio + rtpengine** | Kamailio routes SIP and rtpengine relays RTP audio; neither runs the conversation | Only an edge/SBC layer in front of one of the above. Needed at scale, not for an MVP (my judgement) |
| **LiveKit** (reference) | LiveKit Cloud lists a Middle East region group "Saudi Arabia, UAE" for realtime, and `destination_country` `ae` (Dubai) for outbound SIP. SIP region codes are `eu, india, sa, us, …`; there is **no `ae` SIP region code** ([LiveKit regions](https://docs.livekit.io/deploy/admin/regions/endpoints/); [region pinning](https://docs.livekit.io/telephony/features/region-pinning/)) | Bring-your-own SIP trunk. Whether LiveKit Cloud's UAE presence can terminate an e&/du trunk in-country is **unconfirmed**. Self-hosted LiveKit SIP is another route |

### 4c. CPaaS (hosted call-API platforms) with media in the UAE

- **Twilio:** no (see 02).
- **Azure Communication Services:** resources can be created with UAE data residency, and Call Automation works with Direct Routing (your own SBC) ([Call Automation](https://learn.microsoft.com/en-us/azure/communication-services/concepts/call-automation/call-automation)). Where the real-time media is processed is **unconfirmed**. Voice calling is described as "available globally", and data residency covers stored data.
- **Infobip:** offers WebSocket audio streaming and UAE as a voice destination ([Calls API](https://www.infobip.com/docs/voice-and-video/calls)). A UAE media location is **unconfirmed**.
- **Unifonic:** nothing found on real-time media streaming (see 02).
- **LiveKit Cloud:** has a UAE realtime location (see 4b), the closest thing found to "CPaaS media in the UAE". It is not a carrier, so we still need e&/du for a compliant caller ID.

---

## 5. Per-turn latency budget

**Definition.** Voice-to-voice = from the moment the caller stops speaking to the moment they hear the agent's first audio. **Excluded from both columns:** mobile radio, handset and codec delay inside e&/du's network, which is the same for both. The budget also assumes no speculative tricks (Flux `EagerEndOfTurn`, preemptive LLM), which save a vendor-claimed 200–600 ms in either design (see 03).

| Stage | (A) Current plan: Twilio IE1 + Dublin server + Deepgram Flux + DeepSeek V4.1 Flash on a US/EU host + Cartesia cloud | (B) All-UAE, best found: e&/du trunk → FreeSWITCH/Asterisk in Azure UAE North + self-hosted Flux + self-hosted Qwen3.8-27B + Cartesia on-prem, all in one region | Basis |
|---|---|---|---|
| Caller audio → our media edge | 60–100 (UAE → Ireland over an international route) | 2–10 (in-country) | Half of the 121 ms UAE North ↔ Dublin backbone RTT; PSTN routes are likely slower [est] |
| Media framing / jitter buffer in | 20–40 (Twilio Media Streams) | 20–40 (FreeSWITCH/Asterisk) | [est] |
| Server ↔ STT network | 5–40 (Deepgram EU or US endpoint) | ~1 (same VNet) | Dublin ↔ East US 73 ms RTT; EU endpoint location not stated in sources read |
| End-of-turn + final transcript | ~260 | ~260 | Flux EoT P50 [V]. Alternative B: Nemotron 221 ms median [I] + Smart Turn 10–100 ms |
| LLM to first answer token | **677** (P95 1452) + 10–135 network if the host is in the EU/US | **~101** (P95 318) | aiewf [I]: DeepSeek V4 Flash (low) on Baseten; Qwen3.8-27B NVFP4 on a local RTX 5090 (B uses an RTX PRO 6000 Blackwell; similar but unverified). V4.1 Flash non-thinking itself is unbenchmarked; ticket 23 measures it |
| TTS to first audio | ~297 (Cartesia cloud, Coval median) | ~100–150 (sub-90 ms model latency [V] + local streaming overhead [est]) | |
| Media framing / buffer out | 20–40 | 20–40 | [est] |
| Our edge → caller | 60–100 | 2–10 | [est] |
| **Total, median** | **≈ 1.4–1.7 s** | **≈ 0.5–0.7 s** | Sum of the rows |
| **Tail (P95), rough** | ≥ 2.2 s (the LLM P95 alone is 1.45 s) | ≈ 0.8–1.0 s | [est] |

**Other all-UAE variants (same method):**

| Variant | LLM | STT | TTS | Estimated median |
|---|---|---|---|---|
| B-managed: no self-hosting except the media server | Compass GPT-4.1 (UAE). 536 ms on OpenAI's API; Compass serving unmeasured | Azure Speech uaenorth: 1016 ms TTFS [I] | Azure Neural TTS uaenorth (unmeasured; assume 100–300) | **≈ 1.7–2.0 s: slower than A** |
| B-Compass: self-hosted speech, Compass LLM | Compass GPT-4.1 (UAE) ~536 | self-hosted Flux ~260 | Cartesia on-prem ~125 | ≈ 1.0–1.1 s |
| B-Cerebras: self-hosted speech, Compass Cerebras LLM | gpt-oss-120b-cerebras: ~100–200 [est from Groq's 98 ms] + **176–236 RTT UAE ↔ US** | self-hosted Flux ~260 | Cartesia on-prem ~125 | ≈ 0.75–0.9 s, with the weakest tool accuracy (86 %) and no documented tool calling on Compass |
| Hybrid: UAE media + India speech | self-hosted Qwen in UAE ~101 | Deepgram India (+30–50 RTT) ~300 | Cartesia India regional (Enterprise) or Deepgram India `/v2/speak` (+30–50 RTT) | ≈ 0.65–0.85 s, with no speech GPUs to run |

**Where the gain comes from (A → B, about 0.9 s):**
- LLM: about 580 ms.
- TTS co-location: about 170 ms.
- Network geography: about 120–200 ms.

Most of the LLM gain could also be had without moving to the UAE, by self-hosting the same open model next to a Dublin server. This was not asked, but it bounds what the UAE move itself buys.

---

## What can't be done in the UAE today

1. **Cerebras inference:** Compass's Cerebras models run in the USA. A Cerebras deployment in the UAE is announced but unconfirmed as live.
2. **AWS managed speech in me-central-1:** no Transcribe streaming and no Polly. The nearest are Bahrain (Polly; Transcribe batch only) and Mumbai (streaming).
3. **Managed fast STT or top-naturalness TTS as a hosted API:** Deepgram, ElevenLabs and Cartesia have no Middle East region; the nearest are their India endpoints. Azure is the only managed STT/TTS in UAE North, with slow STT and mid-ranked voices.
4. **Azure premium voice features in UAE North:** no HD voices, MAI voices, Azure OpenAI voices or Voice Live. Azure OpenAI models in uaenorth are "Global standard" only, meaning processing location is not pinned to the UAE.
5. **Twilio media:** no Middle East region or edge.
6. **Some frontier LLMs** on Compass are not UAE-hosted: Claude (Global), GPT-5.5/5.6 (Sweden Central), gpt-realtime (Sweden Central). Claude Haiku is not on Compass at all.
7. **A CPaaS with confirmed in-UAE media and a UAE caller ID:** none found.

## Implications for the spec

These are options for the owner to choose between, not decisions.

1. **Reaching all-UAE reopens ticket 17.** It means the self-hosted route (A: e&/du SIP trunk into our own media server), which ticket 17 dropped in favour of "Twilio all the way". It also depends on the carrier answers in ticket 22, plus one new question: *will e&/du deliver the trunk to a server in Azure UAE North or AWS me-central-1 (internet, ExpressRoute or Direct Connect)?*
2. **"Compass on Cerebras" should not be treated as an in-UAE, low-latency LLM** unless Core42 confirms a UAE Cerebras endpoint. On Compass, the in-UAE LLM candidates with documented tool calling are GPT-4.1, DeepSeek V4 Pro, GLM-5.2, Mistral Small 3.2 and K2 Horizon. None has a measured Compass latency.
3. **The fastest in-UAE design needs self-hosting** STT (and probably TTS and the LLM) on GPU VMs. That brings in:
   - Enterprise contracts (Deepgram, Cartesia);
   - GPU quota in Azure UAE North;
   - on-call ownership of GPU services.

   The telephony port from ticket 17 still fits. A FreeSWITCH, Asterisk or Jambonz adapter replaces the Twilio adapter, and the voice server, turn detection and barge-in logic stay the same.
4. **The latency targets in the spec** (stated as P50/P95, per 03) can be set much tighter if B is chosen (P50 ≲ 0.7 s) than for A (P50 ≈ 1.4 s). They should be confirmed by measured test calls in either case.
5. **Data residency becomes achievable with B** (audio, transcripts and LLM prompts stay in the UAE), whereas A sends all three to the EU/US. Ticket 01 found that the PDPL allows cross-border transfer under conditions (Art. 22–23) rather than requiring in-country storage. So residency is a bonus of B, not a legal driver.
6. **If B is not pursued,** cheap partial gains without leaving Twilio are:
   - a faster LLM next to the Dublin server;
   - Deepgram's EU endpoint;
   - speculative generation.
7. **DeepSeek's first-party API** stores data in China and is far from the UAE. It suits a cheap v1 but not a low-latency v1.

## Open uncertainties

- **Carrier delivery:** whether e&/du will hand a SIP trunk to a public-cloud VM in the UAE, over which kind of link, at what cost and lead time. Also how to read du's "VOIP calls on SIP are currently not permitted" line.
- **Compass serving latency:** time to first token from a UAE North VM for GPT-4.1, DeepSeek V4 Pro and GLM-5.2, and whether thinking can be switched off for the latter two. Measure it, extending ticket 23.
- **Cerebras in the UAE:** ask Core42 whether a UAE-located Cerebras endpoint exists or is planned, and whether gpt-oss-120b-cerebras supports tool calls via Compass.
- **Self-hosted latency on our actual hardware:** Qwen3.8-27B and Flux on RTX PRO 6000 / H100 in UAE North, Cartesia on-prem first-audio time, and Deepgram self-hosted on Azure (Azure not named in the docs read). Deepgram docs pages were unreachable from here (DNS); those claims rest on search snippets of developers.deepgram.com.
- **Azure STT's 1 s TTFS** may partly reflect default silence segmentation. A tuned `Speech_SegmentationSilenceTimeoutMs` was not tested.
- **Azure Neural TTS first-byte latency in uaenorth:** unpublished, so needs measuring.
- **GPU capacity:** Azure retail-price listings and the vantage.sh catalogue show which SKUs exist in the UAE, not whether quota is grantable. AWS me-central-1 GPU availability rests on a third-party catalogue.
- **The international PSTN leg in (A)** (UAE handset → Twilio IE1) has never been measured; the ±100 ms used here is an estimate.
- **Accent accuracy on 8 kHz audio** (from 03) applies equally to every option here, and to self-hosted Nemotron (trained on en-US) in particular.
- **Dates:** the Deepgram India GA date appears inconsistently between search snippet and page; Artificial Analysis leaderboard ranks change continuously (read 2026-10-02).
