# Discovery Call slot-offering and fallback link rules

Type: grilling
Status: resolved
Blocked by: 04
Map: ../map.md

## Question

What are the booking rules: Discovery Call length, Manager's bookable hours, buffers, minimum notice, how far ahead to offer, how many slots to offer and how to phrase them, time-zone handling, what the calendar invite contains (Meet link, agenda), and which channel (SMS or email) delivers the fallback booking link when no slot is agreed?

Also: is the Manager's calendar on Google Workspace or personal Gmail? This decides the auth approach and booking-page tier (see ticket 04).

## Answer

Settled with the owner 2026-09-28. Every value below is config.

**Calendar account**
- The owner has a personal Gmail and info@hoplonco.com and wasn't sure about Workspace.
- DNS check (2026-09-28): hoplonco.com's primary MX is `smtp.google.com` and its SPF includes `_spf.google.com`, so the domain very likely runs **Google Workspace**. A secondary MX points to the site host.
- Decision: the Manager's calendar is a **Hoplon Workspace account**, not personal Gmail, so invites come from the company domain.
- Auth: an **Internal** OAuth app (no Google verification needed) holding the Manager's refresh token, with the consent screen published so the token doesn't expire after 7 days.
- Owner checks: log in to admin.google.com with the hoplonco.com account to confirm Workspace and see which plan it is on. The plan decides the booking-page tier. If it turns out not to be Workspace, fall back to personal-Gmail OAuth (ticket 04).

**The Discovery Call**
- 30 minutes on Google Meet, with the link created automatically.

**Bookable time**
- Monday-Friday 10:00-18:00 Asia/Dubai. The telemarketing window does not apply to Discovery Calls.
- 15-minute buffer around existing events.
- Earliest slot 2 hours from now; latest 7 days ahead.

**Offering slots**
1. Ask a preference first: earlier or later this week, morning or afternoon.
2. Offer 2 specific slots.
3. If neither works, one more round of 2 slots.
4. Then the fallback: "I'll email you a link to pick any time that suits you."

Never read out more than 2 slots at once. Re-check freeBusy right before booking.

**Fallback link**
- Sent by email only in the MVP: a Google appointment-schedule booking page, created by hand and stored as config.
- SMS comes later (UAE sender-ID registration is legal-team work).

**Invite (visible to the Lead)**
- Title "Discovery Call: Hoplon and Co × {Name}", Meet link, a 3-line agenda. Sent with `sendUpdates=all`.
- Omar's private notes never go in the invite.

**Manager prep brief (private)**
- Post-call summary, Intent to Buy evidence and transcript link.
- Shown in the dashboard and sent as a separate email to the Manager.

**Email confirmation**
- Omar confirms the form email by domain only: "the one at gmail.com, is that still best?"
- A new address is spelled back letter by letter.
