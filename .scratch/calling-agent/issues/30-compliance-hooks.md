# Compliance hooks in the product

Type: grilling
Status: resolved
Map: ../map.md

## Question

Which compliance mechanisms does engineering build now, so the legal team's rules can be plugged in later: the pre-dial gate (DNCR/opt-out/window/retry), the call register export, PDPL erase/export, and consent evidence storage?

## Answer

Settled with the owner 2026-10-03.

Engineering builds these hooks now; the legal team supplies the rules later.

1. **Pre-dial gate** that every Call Attempt must pass:
   - DNCR (a manual list now; the official check plugs in later);
   - Opted-out Leads;
   - calling window;
   - retry limits.
2. **Call register export:** a CSV generated from the event log.
3. **PDPL requests:** "Erase this Lead" and "Export this Lead's data".
4. **Consent evidence fields:** ready for when the website team ships the checkbox (ticket 20).
