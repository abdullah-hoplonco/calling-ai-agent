# Lead email ingestion mechanism

Type: grilling
Status: resolved
Map: ../map.md

## Question

How are new-Lead form-notification emails pulled from info@hoplonco.com (Google Workspace) and parsed: push vs polling, the parser approach, dedupe, and handling of unparseable emails?

## Answer

Settled with the owner 2026-10-03.

**Fetching**
- Gmail API push notifications (watch + Pub/Sub) on info@hoplonco.com for speed-to-lead, with a 1-minute polling safety net.

**Parsing**
- A strict parser for the known notification format, with an LLM fallback for odd emails.
- Processed emails get a Gmail label.

**Dedupe and failures**
- Dedupe by Gmail message ID.
- Unparseable emails go to a "Needs review" list in the dashboard; they are never dropped silently.
