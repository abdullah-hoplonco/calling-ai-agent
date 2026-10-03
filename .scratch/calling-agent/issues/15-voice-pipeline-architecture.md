# Provider adapters and deployment

Type: grilling
Status: resolved
Blocked by: 08, 11, 14, 17, 21, 25
Map: ../map.md

## Question

Given the core architecture (ticket 21), the chosen providers (14), the telephony route (17), the call flow (08) and the booking rules (11): how is each adapter implemented (telephony, STT, TTS, LLM, calendar), which hosting region and infrastructure run each deployable, and what is the latency budget per stage end to end?

## Answer

Settled with the owner 2026-10-02 (Option C v1 on LiveKit; owner chose Azure, reasoning that a full-stack UAE build is easier on Azure).

**Cloud and region**
- **Microsoft Azure**: v1 in **North Europe (Ireland)**, next to Twilio IE1 and the Deepgram and Cartesia EU endpoints.
- v2 moves to **UAE North** (same cloud, region move only). That region has GPU VMs, hosts Core42 Compass, and e& is an Azure ExpressRoute partner in the UAE.

**Infrastructure** (Terraform, azurerm)
- Azure Container Apps for the app API, Celery workers and the Next.js dashboard.
- The LiveKit agent workers and the Qwen GPU server (vLLM or SGLang) run in the same region, ideally the same VNet, so the agent-to-LLM hop is about 1 ms.
- The GPU is an NC-series VM, switched on for calling hours only. Its availability and quota in North Europe must be confirmed in ticket 23.
- Azure Database for PostgreSQL Flexible Server, Azure Managed Redis, Blob Storage for recordings, Key Vault for secrets.
- **LiveKit Cloud** (EU) for media and SIP; Twilio Elastic SIP Trunking into it.

**Deploys**
- LiveKit agent workers drain: no new calls, live calls finish, then shut down.
- The dialer only uses workers that are accepting calls.

**Latency plan**
- Budget per turn:
  - UAE ⇄ Ireland network ~250 ms;
  - end-of-turn ~250-300 ms (Deepgram Flux default, tuned down);
  - LLM first token ~100 ms (own GPU);
  - TTS first audio ~100-200 ms.
- Preemptive generation hides most of the LLM time.
- Target ~0.6-0.8 s, recalibrated from real calls.
- Calendar free/busy is prefetched when an Intent to Buy signal appears; Omar says a short line while the booking is made.

**Configuration**
- Prompts, persona and the knowledge sheet live in git, gated by evals.
- Operational settings (calling hours, pacing, concurrency, slot rules) live in the DB, edited in the dashboard, with every change logged.
- Secrets live in Key Vault.

**Environments**
- Local (Twilio to own phones and the LiveKit web playground), staging (nightly audio evals), production.

**CI/CD**
- GitHub Actions on every PR: lint, type check, unit tests (state machine), text-mode evals.
- On merge: build, deploy to staging, then production with one approval.
- A git repo is created only with the owner's go-ahead.

