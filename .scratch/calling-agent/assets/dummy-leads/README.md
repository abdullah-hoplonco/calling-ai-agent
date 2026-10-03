# Dummy Lead data

Fake data for planning Lead ingestion and the Lead data model (ticket `issues/06-collect-lead-samples.md`). No real people: all emails use reserved `example.*` domains, and UAE phone numbers use the fictional `555 01xx` subscriber range (e.g. `+971 50 555 0101`).

## Files

| File | What it is |
|---|---|
| `01-app-enquiry.eml` | Notification email: detailed mobile app enquiry (English). |
| `02-please-call.eml` | Notification email: vague "please call me". |
| `03-arabic-marketing.eml` | Notification email: Gulf Arabic with an English sign-off (TikTok/Snapchat ads plus a simple website); name in Arabic script. |
| `backlog.xlsx` | Consolidated form-submission sheet (one sheet, "Form Submissions"). |

The three emails are recent submissions (24-27 Sep 2026) that are **not** yet in `backlog.xlsx`. Each email has these headers: `From: Hoplon & Co Website <no-reply@hoplonco.com>`, `To: info@hoplonco.com`, `Reply-To: <lead email>`, `Subject: New form submission - Contact Us`, and a `Date` in Asia/Dubai time (`+0400`). The body is plain text with `Name:`, `Email:`, `Phone Number:` and `Message:` lines, a `Submitted:` time marked "(GST)", and the page URL.

## Fields

The website form collects exactly four fields: **Name, Email, Phone, Message**. The sheet adds **Submitted At**, the submission time from the email (Dubai local time, no timezone stored). There is no service field. The service a Lead wants has to be inferred from the free-text Message.

## backlog.xlsx

- **Rows:** 62 data rows plus a header row.
- **Date range:** 2025-04-07 to 2026-09-20 (about 18 months), sorted by Submitted At.
- **Mix:** Emirati/Arab, South Asian, Filipino and Western names. Messages cover mobile apps, websites, SEO, social media and ads, e-commerce, maintenance and UI/UX. Some messages are vague, three are Arabic-only and one mixes Arabic and English.
- **Phone formats seen:** `+971 50 555 0101`, `+971505550101`, `0501234567`, `050 555 0106`, `050-555-0117`, `971545550103`, `971 55 555 0111`, `+971 (0)50 555 0153`.

## Deliberate data-quality issues

1. **Exact duplicate:** Ahmed Al Mansoori double-submitted, with a second row 2 minutes later.
2. **Same person, different details:** Priya Nair appears again as `priya nair` with `Priya.Nair@example.com` and a differently formatted phone 3 weeks later, sending a follow-up message.
3. **Same person, name variant:** `Rahul Verma` and `Rahul V` share the same email and phone number.
4. **Same person, two scripts:** `خالد الزعابي` and `Khalid Al Zaabi` share the same email and phone number.
5. **Missing email:** Hind Al Mazrouei, Sunil Kumar.
6. **Invalid phone:** `050555014` (too short, Fahad Al Jaberi), `12345` (Chloe Martin), `not available` (Ravi Patel, who also says "don't call").
7. **Malformed email:** `mohamed.ali@example` (no TLD).
8. **Leading/trailing whitespace:** `  Mona Saleh ` (spaces in name, email, phone and message); `Ali Hassan<TAB>` (trailing tab, plus trailing spaces in phone).
9. **Non-UAE numbers:** `+91 98765 00148` (India), `+44 7700 900149` (UK).
10. **Empty message:** Dana Yousef (empty string), Kevin Lim (blank cell).
11. **Low-information messages:** "Hi", "need app", "please call me", "Interested. Please call."
12. **Spam/bot entries:** an SEO-agency sales pitch (`Best SEO Services`, US-style number), and a bot row (`qwerty`, `1111111111`, HTML link, submitted at 03:17).
13. **Timing request inside the message:** "Call me after 6pm please" (Sana Sheikh).
