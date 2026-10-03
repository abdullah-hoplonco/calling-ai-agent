# Ask e& and du about a business SIP trunk

Type: task
Status: out-of-scope (legal team)
Owner: legal team (deferred until before go-live; not on the engineering path)
C-suite risk: yes (see ../risks.md, R1)
Map: ../map.md

## Question

The legal team gets a UAE caller ID that complies with Cabinet Resolution 56/2024 Art. 4(3) and 4(13): a local e& or du number registered to the trade licence, delivered into **Twilio via BYOC (Bring Your Own Carrier)**. The telephony route is settled as Twilio (ticket 17), so the only question is how the compliant number reaches Twilio. Ask e& and du business sales:

1. Will you provide a business SIP trunk and local numbers registered to our trade licence for automated outbound marketing calls?
2. Can that trunk connect to Twilio BYOC (Twilio's Ireland region)? If not, what is the closest compliant arrangement?
3. Are there SBC or equipment requirements?
4. What are the monthly and per-minute costs and the setup lead time?
5. Which documents do you need (trade licence, telemarketing approval)?
6. Is our caller ID guaranteed to be presented on calls to UAE mobiles?

Engineering can draft the email on request. Record the answers. If BYOC is refused, escalate to the owner, because the telephony decision in ticket 17 would need to be reopened.

## Note (2026-10-02)

With LiveKit (ADR 0002), there are two ways to connect an e&/du trunk:
- **(a) Via Twilio BYOC:** LiveKit → Twilio → e&.
- **(b) Directly as a LiveKit outbound SIP trunk:** LiveKit → e&, with no Twilio in the path.

Also ask whether e&/du will deliver the trunk to LiveKit SIP hosted in the EU, and later in Azure UAE North (v2). Mind the UAE VoIP restrictions (TDRA licensing).
