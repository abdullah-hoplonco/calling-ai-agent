# Web form consent wording and evidence capture

Type: grilling
Status: resolved
Blocked by: 01
C-suite risk: yes (see ../risks.md, R3, R6)
Map: ../map.md

## Question

What does the website form's consent look like so that Connected Calls are lawful under Res 56 and the PDPL: the unticked checkbox wording (phone call, recording, overseas processors, AI assistant), what evidence is stored per Lead (timestamp, IP, form version), and how Leads in the existing backlog who never gave this consent are treated (re-consent, e.g. by email first, or excluded)?

Note: drafted from the ticket 01 research now; UAE counsel (ticket 18) reviews it before go-live. The backlog is treated as callable by owner decision, with the risk flagged to the C-suite.

## Answer

Settled with the owner 2026-09-28.

**Ownership**
- The website belongs to a separate website team. This map owns product, internal engineering and applied AI.
- This ticket's output is therefore a **change request for the website team**. Final consent wording is approved by the legal team (C-suite risks R3 and R6).

**Change request: form fields**
1. An **unticked consent checkbox** (required to submit). Draft wording for the legal team to finalise:
   "I agree that Hoplon & Co may call me on the number above about my enquiry, including by an AI assistant. Calls are recorded. My details and call recordings may be processed by service providers outside the UAE. I can withdraw consent at any time. [Privacy notice]"
2. A **"Service" dropdown**: Website, Mobile app, Digital marketing, Other. This removes the need to guess the service from the message.

**Change request: evidence stored with every submission**
- submission timestamp (Asia/Dubai);
- IP address;
- form version / consent wording version;
- the checkbox state.

**Change request: the notification email**
- The email must carry the new fields in a stable, parseable layout, because ingestion parses it.

**Until the website team ships**
- Ingestion treats Leads without these fields as "no recorded consent" and still calls them. This is the backlog decision, accepted by the owner (risk R3).
- The service is inferred from the message.
