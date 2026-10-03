# Google Calendar API for live availability and booking

Type: research
Status: resolved
Map: ../map.md

## Question

How does a backend check the Manager's availability and book a Discovery Call on Google Calendar in real time during a call? Cover: freeBusy query, events.insert with a Lead as attendee (invite email behaviour), auto-generated Google Meet links, auth for a single owner calendar (OAuth refresh token vs service account with domain-wide delegation, Workspace vs personal Gmail), time zones, rate limits and latency, and appointment-schedule/booking-page options usable as the fallback booking link.

## Answer

- **Checking availability:** `POST /calendar/v3/freeBusy` on `primary` with `timeZone: "Asia/Dubai"` returns busy ranges only. The backend works out free Discovery Call slots from configured working hours, slot length, buffer and minimum notice.
- **Booking:** `events.insert` with `sendUpdates=all` emails the Lead an invite. If `sendUpdates` is left out, no invite is sent. Set `responseStatus` to `needsAction`, and supply our own event `id` (derived from the Connected Call ID) so a retry gets a 409 instead of a double booking.
- **Not atomic:** freeBusy and insert are separate calls with no "book if still free". Re-check freeBusy for the chosen slot just before inserting.
- **Meet link:** `conferenceData.createRequest` (`hangoutsMeet`, unique `requestId`) plus `conferenceDataVersion=1`. Creation can come back `pending`, so read the link from the event before sending our own SMS.
- **Auth:** the Manager's OAuth refresh token works for both Gmail and Workspace. Publish the consent screen "In production", because a Testing-mode refresh token expires after 7 days. A service account needs Workspace domain-wide delegation to add attendees, so it is only an option on Workspace.
- **Scopes:** use the least that works, `calendar.events.owned` (or `calendar.events`) plus `calendar.freebusy`. An unverified app for personal use shows a click-through warning. A Workspace Internal app avoids verification.
- **Limits:** 600 requests/min per user and 10,000/min per project (updated May 2026). That is far above our volume. Back off on 403/429.
- **Latency:** Google publishes no latency figures. Pre-fetch availability when Intent to Buy is detected, keep tokens warm, allow 1-2 short retries, then fall back.
- **Fallback:** a Google Calendar appointment-schedule booking page. Personal Gmail and Business Starter get one page, premium tiers get more. The Manager sets it up by hand because there is no API for it, and we store its URL as config to send by SMS or email.
- **Open:** is the Manager's account Workspace or personal Gmail? The auth path and booking-page features depend on it.

[findings](../research/04-google-calendar-booking-api.md)
