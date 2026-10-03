# Google Calendar API for live availability and booking

Ticket: [04-google-calendar-booking-api](../issues/04-google-calendar-booking-api.md)
Researched: 2026-09-25. Sources are Google primary docs unless marked otherwise. (Doc base URL is now `developers.google.com/workspace/calendar/...`.)

## Question

How does a backend check the Manager's availability and book a Discovery Call on Google Calendar in real time during a Qualification Call? Covers freeBusy, events.insert with the Lead as attendee, Meet links, auth for one owner calendar, time zones, rate limits and latency, and appointment schedules as the fallback booking link.

---

## 1. Checking availability: `freeBusy.query`

- Endpoint: `POST https://www.googleapis.com/calendar/v3/freeBusy`. Body fields: `timeMin`, `timeMax` (RFC3339), `timeZone` (optional; "The default is UTC"), `items[].id` (calendar or group IDs), and optional `groupExpansionMax` (max 100) / `calendarExpansionMax` (max 50). [freebusy/query](https://developers.google.com/workspace/calendar/api/v3/reference/freebusy/query)
- Response: `calendars.{id}.busy[]` is a list of `{start, end}` busy ranges. `start` is inclusive and `end` is exclusive. There is also a per-calendar `errors[]` with reasons such as `notFound`, `tooManyCalendarsRequested` and `internalError`, and Google says "clients should gracefully handle additional error statuses". [freebusy/query](https://developers.google.com/workspace/calendar/api/v3/reference/freebusy/query)
- Accepted scopes include the narrow `calendar.freebusy` / `calendar.events.freebusy` and the broader `calendar.readonly` / `calendar`. [freebusy/query](https://developers.google.com/workspace/calendar/api/v3/reference/freebusy/query), [scopes](https://developers.google.com/workspace/calendar/api/auth)
- freeBusy returns **busy blocks only**. It does not know about working hours, slot length, buffers or minimum notice. The backend has to compute free slots itself: working hours in Asia/Dubai, minus the busy ranges, cut into Discovery Call-length slots. (Inference from the response shape above.)

Sample request:

```http
POST https://www.googleapis.com/calendar/v3/freeBusy
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "timeMin": "2026-09-27T00:00:00+04:00",
  "timeMax": "2026-10-04T00:00:00+04:00",
  "timeZone": "Asia/Dubai",
  "items": [{ "id": "primary" }]
}
```

Sample response:

```json
{
  "kind": "calendar#freeBusy",
  "timeMin": "2026-09-26T20:00:00.000Z",
  "timeMax": "2026-10-03T20:00:00.000Z",
  "calendars": {
    "primary": { "busy": [ { "start": "2026-09-28T10:00:00+04:00", "end": "2026-09-28T11:00:00+04:00" } ] }
  }
}
```

## 2. Booking: `events.insert` with the Lead as attendee

- Endpoint: `POST https://www.googleapis.com/calendar/v3/calendars/{calendarId}/events`. `calendarId` can be `"primary"`. [events/insert](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert)
- Scopes: `calendar`, `calendar.events`, `calendar.events.owned` ("See, create, change, and delete events on Google calendars you own") or `calendar.app.created`. [events/insert](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert), [scopes](https://developers.google.com/workspace/calendar/api/auth)
- `attendees[].email` is required for each attendee and must be a valid RFC5322 address. `responseStatus` should be `needsAction` for new events. Setting it to accepted, tentative or declined can hide the event from some guests. [events/insert](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert)
- **Invite emails** are controlled by the `sendUpdates` query parameter:
  - `all`: notifications go to all guests.
  - `externalOnly`: notifications go to "non-Google Calendar guests only".
  - `none`: no notifications. Google warns this "can have significant adverse effects, including events not syncing to external calendars".
  - Leaving it out means no invite email ("The default is false").
  - `sendNotifications` is deprecated.

  [events/insert](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert). "If you set sendUpdates to "all" or "externalOnly" … the corresponding attendees receive an email notification." [create-events guide](https://developers.google.com/workspace/calendar/api/guides/create-events)
- **Idempotency:** the client may supply the event `id` itself. It must use base32hex characters (a-v, 0-9), be 5-1024 characters long and be unique per calendar; Google recommends a UUID. Google says this "prevents duplicate event creation if the operation fails at some point after it is successfully executed". Re-sending the same ID returns `409 duplicate`, which is a permanent error and should not be retried. [events/insert](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert), [create-events guide](https://developers.google.com/workspace/calendar/api/guides/create-events), [errors](https://developers.google.com/workspace/calendar/api/guides/errors)
- Useful optional fields: `guestsCanModify` (default false), `guestsCanInviteOthers` (default true, so consider false), `guestsCanSeeOtherGuests`, `reminders`, `description`. [events/insert](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert)
- **Not atomic:** there is no "book if still free" primitive. freeBusy and insert are separate calls. To reduce the race, re-run freeBusy for the chosen slot just before inserting. (Inference; none of the cited reference pages offers a conditional insert.)

## 3. Auto-generated Google Meet link

- Set `conferenceData.createRequest` with a fresh `requestId` and `conferenceSolutionKey.type: "hangoutsMeet"`, and pass `conferenceDataVersion=1`. With version 0 (the default), conference data is ignored. [events/insert](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert), [create-events guide](https://developers.google.com/workspace/calendar/api/guides/create-events)
- Conference creation is **asynchronous**. "The immediate response … might not yet contain the fully-populated conferenceData; this is indicated by a status code of `pending`". Once it becomes `success`, `entryPoints` holds the video and phone URIs. [create-events guide](https://developers.google.com/workspace/calendar/api/guides/create-events)
- Google warns against reusing conference data across events. Generate a unique conference per event. [events/insert](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert)
- To check which types a calendar supports, read `conferenceProperties.allowedConferenceSolutionTypes` on `calendars` or `calendarList`. [create-events guide](https://developers.google.com/workspace/calendar/api/guides/create-events)

Sample booking request:

```http
POST https://www.googleapis.com/calendar/v3/calendars/primary/events?sendUpdates=all&conferenceDataVersion=1
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "id": "0f3c9a2b7d5e4c1a9b8e6d4c2a0f1e3d",
  "summary": "Discovery Call – <Lead name> / <Agency>",
  "description": "Booked by Calling Agent on Qualification Call <call id>.",
  "start": { "dateTime": "2026-09-28T14:00:00", "timeZone": "Asia/Dubai" },
  "end":   { "dateTime": "2026-09-28T14:30:00", "timeZone": "Asia/Dubai" },
  "attendees": [ { "email": "lead@example.com", "displayName": "Lead Name" } ],
  "guestsCanInviteOthers": false,
  "conferenceData": {
    "createRequest": { "requestId": "<uuid>", "conferenceSolutionKey": { "type": "hangoutsMeet" } }
  },
  "reminders": { "useDefault": true }
}
```

Read `hangoutLink` / `conferenceData.entryPoints` from the response. If `conferenceData.createRequest.status.statusCode` is `pending`, `events.get` again a moment later before putting the link in SMS or email.

## 4. Auth for a single owner calendar

The right option depends on whether the Manager's account is **Google Workspace** or **personal Gmail**.

| Option | Works for | Notes |
|---|---|---|
| OAuth 2.0 user consent + stored refresh token | Personal Gmail and Workspace | One-time consent by the Manager. The backend stores the refresh token and mints access tokens. |
| Service account + domain-wide delegation (DWD), impersonating the Manager | Workspace only | A Workspace super admin grants DWD. "Service accounts need to use domain-wide delegation of authority to populate the attendee list." |
| Service account with the calendar shared to it (no DWD) | Both, but **cannot add attendees** | Useless for our case because the Lead has to be an attendee. |

Sources: [service-account OAuth](https://developers.google.com/identity/protocols/oauth2/service-account) (DWD is granted by a Workspace super admin; service accounts are "not members of your Google Workspace domain"), [events/insert attendees note](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert).

Refresh-token gotchas:

- **7-day expiry in Testing mode:** "A Google Cloud Platform project with an OAuth consent screen configured for an external user type and a publishing status of 'Testing' is issued a refresh token expiring in 7 days". Calendar scopes are not in the exempt profile/email set. [OAuth 2.0 overview](https://developers.google.com/identity/protocols/oauth2)
- **Other ways a refresh token dies:** the user revokes access, the token goes unused for 6 months, the token-count cap is exceeded, time-based access expires, or an admin restricts the scopes. The code must expect a dead refresh token and alert someone to re-consent. [OAuth 2.0 overview](https://developers.google.com/identity/protocols/oauth2), [errors, 401 guidance](https://developers.google.com/workspace/calendar/api/guides/errors)
- **Verification:** an app that requests sensitive scopes and is unverified shows an "unverified app" screen and is capped at 100 users. The **personal-use exception** lets you and a few known users click through without verification. An **internal** app (Workspace org, internal user type) has no unverified screen and no cap. [Unverified apps](https://support.google.com/cloud/answer/7454865?hl=en), [When is verification not needed](https://support.google.com/cloud/answer/13464323?hl=en)
- **What to do:**
  - Personal Gmail: create an External OAuth client, set its status to **In production** (unverified, personal use), have the Manager consent once, and store the refresh token encrypted.
  - Workspace: use an **Internal** OAuth app, or a service account with DWD scoped to `calendar.events` and `calendar.freebusy`.

**Meet with a service account (secondary source):** developers report "Invalid conference type value" errors when a service account creates Meet conferences without DWD impersonation of a real user. Treat this as unconfirmed, but it is another reason to act *as the Manager*, either with an OAuth token or DWD. [googleapis/google-api-nodejs-client#2387](https://github.com/googleapis/google-api-nodejs-client/issues/2387)

## 5. Time zones (Asia/Dubai)

- The API uses IANA time zone IDs. An event's time can be given as a dateTime with an offset, or as a local dateTime plus `timeZone`. [Events & calendars concepts](https://developers.google.com/workspace/calendar/api/concepts/events-calendars)
- For `end.dateTime` / `start.dateTime`: "A time zone offset is required unless a time zone is explicitly specified in timeZone." [events/insert](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert)
- freeBusy returns UTC unless you pass `timeZone`. [freebusy/query](https://developers.google.com/workspace/calendar/api/v3/reference/freebusy/query)
- Asia/Dubai has been fixed at UTC+4 with no DST since 1920 (`Zone Asia/Dubai 3:41:12 - LMT 1920 / 4:00 - %z`). [IANA tzdata `asia` file](https://github.com/eggert/tz/blob/main/asia)
- Always send `timeZone: "Asia/Dubai"` explicitly and speak times to the Lead in Dubai time. The Lead might be outside the UAE, so it is worth confirming. (Recommendation.)

## 6. Rate limits and latency

- Quotas as updated 2026-05-01 for new projects:
  - 10,000 requests per minute per project
  - 600 requests per minute per user per project (sliding window)
  - Daily billing threshold of 1,000,000 requests per project, with charges above it "planned … later in 2026"

  "API calls by a service account are considered to be using a single account." [Usage limits](https://developers.google.com/workspace/calendar/api/guides/quota)
- Rate-limit errors come back as 403 `userRateLimitExceeded` or `rateLimitExceeded`, or as 429. Retry them with truncated exponential backoff. 403 `quotaExceeded` means Calendar usage limits were hit. [errors](https://developers.google.com/workspace/calendar/api/guides/errors), [Usage limits](https://developers.google.com/workspace/calendar/api/guides/quota)
- There are also "operational limits … if you attempt to write to a single calendar in quick succession". [Usage limits](https://developers.google.com/workspace/calendar/api/guides/quota)
- Workspace anti-spam limits: about 10,000 external invites in a short period before throttling, and stricter unpublished limits for trial accounts and for paid accounts in their first 60 days. [Avoid Calendar use limits](https://support.google.com/a/answer/2905486?hl=en)
- Our volume (a handful of bookings a day) is orders of magnitude under every limit.
- **Latency:** none of the cited docs publishes a latency SLA or typical p50/p99 for freeBusy or insert. It has to be measured. Design for it:
  - Run freeBusy (and cache the token) when the call connects or when Intent to Buy is detected, so slot options are ready before the Lead is asked.
  - Keep the access token warm. Access tokens are short-lived, so refresh them proactively.
  - Do one freeBusy re-check and one insert at booking time.
  - Fill the pause with speech ("let me lock that in") while the calls run.
  - Keep backoff inside the call short (1-2 retries), then fall back to the booking link.

## 7. Fallback booking link: Google Calendar appointment schedules

- A personal Google Account or Workspace account can create an appointment schedule on the web (not the mobile apps). It produces a shareable booking page. Settings include duration, weekly availability, scheduling window (maximum advance and minimum notice), buffer time, maximum bookings per day, "Check calendars for availability", Google Meet conferencing, a booking form (first name, last name and email required), email verification, and confirmations and reminders. [Create an appointment schedule](https://support.google.com/calendar/answer/10729749?hl=en)
- **Tier differences:**
  - Personal Gmail and Workspace Business Starter get a **single** booking page.
  - Multiple schedules, automatic email reminders, checking several calendars, payments, email verification and secondary-calendar schedules need Google One Premium / AI Pro / Ultra, Workspace Individual, or Business Standard and higher.
  - Workspace Frontline, Essentials and legacy plans cannot create appointment schedules at all.

  [Compare premium features](https://support.google.com/calendar/answer/16287038?hl=en)
- **No API:** no appointment-schedule or booking-page endpoint appears anywhere in the Calendar API v3 reference pages cited above. The Manager creates the page by hand in the web UI, and its URL is stored as config and sent by SMS or email. Bookings land on the Manager's calendar as normal events, which our backend could read later with `events.list` if needed. (Community threads asking for an API: [thread](https://support.google.com/calendar/thread/231731209?hl=en).)

---

## Implications for the spec

1. **Booking tool contract:**
   - `checkAvailability(window)` calls freeBusy on `primary` with `timeZone=Asia/Dubai`. The backend derives slots from configured working hours, Discovery Call length, buffer and minimum notice, then offers the Lead 2-3 concrete slots.
   - `bookDiscoveryCall(slot, lead)` re-checks freeBusy for that slot, then calls `events.insert` with `sendUpdates=all`, `conferenceDataVersion=1`, a client-generated event `id`, and the Lead as the only attendee.
2. **Idempotency key:** derive the event `id` deterministically from the Qualification Call ID (base32hex/UUID form). A retried tool call then gets a 409 instead of a double booking, and a 409 counts as "already booked".
3. **The Lead's email must be captured and confirmed on the call** before booking. The invite is sent to it, and a misheard email means no invite. If no reliable email is available, book without an attendee, or with `sendUpdates=none` plus our own SMS, and flag it. Alternatively, use the booking-link fallback.
4. **Meet link:** handle the `pending` status. Read the link from the event, not from the first response, before sending our own SMS confirmation. The Google invite email carries the Meet link anyway.
5. **Auth decision is gated on the Manager's account type** (see uncertainties). Default plan: an OAuth refresh token for the Manager with the minimal scopes `calendar.events.owned` (or `calendar.events`) plus `calendar.freebusy`, the consent screen published "In production", and a health check plus alerting on `invalid_grant`.
6. **Fallback triggers:**
   - Calendar API error or timeout beyond budget
   - No slot accepted
   - Lead prefers to choose later
   - Email not captured

   In any of these cases, send the appointment-schedule booking URL by SMS or email. It is a static config value maintained by the Manager.
7. **Record keeping:** store the event id, htmlLink, Meet link and slot on the Lead's record for the Manager and for reschedule/cancel flows later (`events.patch`/`delete` with `sendUpdates=all`).

## Open uncertainties

- **Workspace or personal Gmail?** This decides the auth path (DWD or Internal app vs an External unverified app with the personal-use exception) and the booking-page tier (single page vs premium). Ask the owner.
- **Real latency of freeBusy and insert from our hosting region** (UAE or EU) is unpublished. Benchmark before fixing the in-call latency budget.
- **Whether the Manager's calendar allows `hangoutsMeet`:** check `allowedConferenceSolutionTypes`. It is normally present for Gmail and Workspace, but a Workspace admin can disable Meet.
- **Future billing** of Calendar API usage announced for later in 2026 is negligible at our volume, but the terms are not yet published.
- **Service account + Meet** behaviour rests only on community reports, not primary docs. It is not needed if we use an OAuth token or DWD as the Manager.
- **Working hours, buffer, Discovery Call length and minimum notice** are business config the owner has to supply. Should the Calendar's own "working hours" setting be read instead of config? Not researched.
- **Invite deliverability to Lead email domains** (spam folders) is untested. That is one reason to also send our own SMS or WhatsApp confirmation.
