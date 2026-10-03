# Create dummy Lead data

Type: task
Status: resolved
Map: ../map.md

## Question

AFK (owner decision 2026-09-26: dummy data instead of real samples). The agent generates 2-3 realistic form-notification emails and an Excel backlog file of fake Leads with exactly the fields the website form collects: name, email, phone number, message (plus the submission timestamp from the email). There is no service field; the service must be inferred from the message. Needed so the Lead data model and ingestion can be decided. Record: file locations, fields present, row count, date range, data-quality issues.

## Answer

- Dummy data is in `assets/dummy-leads/`. It contains three notification emails (`01-app-enquiry.eml`, `02-please-call.eml`, `03-arabic-marketing.eml`), the backlog `backlog.xlsx` and a `README.md` describing both.
- The emails are plain text, sent from `no-reply@hoplonco.com` to `info@hoplonco.com` with Subject "New form submission - Contact Us". `Reply-To` is set to the Lead's email and `Date` is in Dubai time (+0400). The body has `Name:`, `Email:`, `Phone Number:` and `Message:` lines, followed by the submitted time and the page URL.
- Fields present: Name, Email, Phone, Message, and Submitted At (Dubai local time, no timezone in the sheet). There is no service, company or source field.
- `backlog.xlsx` has 62 rows dated 2025-04-07 to 2026-09-20. The three emails are newer (24-27 Sep 2026) and are not in the sheet.
- Phone numbers come in at least 8 formats (`+971 50 ...`, `0501234567`, `971...`, dashes, `(0)`). Ingestion must normalise them to E.164 before dialling.
- Deliberate data-quality issues:
  - duplicates: one exact double-submit, plus the same person with a different name case, name variant or name script
  - missing email and a malformed email
  - invalid phones, including `not available`
  - stray whitespace and tabs
  - non-UAE numbers (India, UK)
  - empty messages
  - spam and bot rows
  - timing or "don't call" instructions written inside the message
- The service a Lead wants must be inferred from the free-text Message. Messages may be in English, Arabic or both, and some are too vague to infer anything ("Hi", "please call me"). The Connected Call may be the first place the service is learned.

