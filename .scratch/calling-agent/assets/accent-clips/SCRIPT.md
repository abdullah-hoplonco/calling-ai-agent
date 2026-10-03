# Accent test clips: recording script

**Purpose:** test which speech-to-text (STT, the service that turns the Lead's voice into text) hears UAE-typical English best, on real phone-quality audio. Used by the "Select STT, TTS and LLM providers" ticket.

## Who records

Aim for **5-8 speakers**, at least one from each group. Colleagues, friends and family are fine.

| Group | Target speakers |
|---|---|
| Gulf Arab (Emirati, Saudi, other Gulf) | 1-2 |
| Levantine or Egyptian Arab | 1 |
| South Asian (Indian, Pakistani, Bangladeshi, Sri Lankan) | 2 |
| Filipino | 1 |
| Western (British, American, European) | 1 |

## How to record (phone quality matters)

1. The speaker **calls your phone** from their phone, as a normal mobile call. Record the call on your side with any call-recorder app. Don't record in a studio or through a laptop mic: we need real phone-line audio.
2. The speaker reads each line **naturally, the way they would really say it on a call**. Small mistakes and "umm"s are good.
3. Save one file per speaker, named `<group>-<speakerNo>.m4a` (or .mp3/.wav), e.g. `southasian-1.m4a`. Put the files in this folder.
4. Note each speaker's group in `speakers.md`. **No names needed.**
5. Get each speaker's OK to use the recording for internal testing only.

Leave about **2 seconds of silence** between lines. The lines are numbered so the transcripts can be matched to the expected text.

## Lines to read (about 3 minutes per speaker)

**Names and identity**
1. Yes, speaking. This is Mohammed.
2. My name is Priyanka Venkataraman.
3. It's Abdulrahman Al Mansoori.
4. Who is this? Which company did you say?

**Email addresses (the hardest part)**
5. My email is ahmed dot k at gmail dot com.
6. It's p-r-i-y-a underscore v at outlook dot com.
7. Send it to info at al-noor-trading dot ae.
8. No, that's my old email. Use jhun dot santos eighty-four at yahoo dot com.

**Times and dates**
9. Can you call me tomorrow at four?
10. Thursday afternoon works, maybe around half past two.
11. Not this week, next Monday morning is better.
12. Call me after eight in the evening.

**Intent and objections**
13. Yes, we want to build an app for our restaurant.
14. How much will it cost roughly?
15. Just send me an email, I'm busy right now.
16. I'm just browsing, maybe next year.
17. Not interested, please don't call me again.
18. Can I talk to someone from your team?
19. Wait, am I talking to a bot?

**Business words**
20. We need an e-commerce website with Arabic and English.
21. Mainly SEO and Instagram ads for our clinic.
22. Something like an ERP for our logistics company in Jebel Ali.

**Arabic and English mixed (for speakers who do this naturally)**
23. Yalla, okay, send me the details inshallah.
24. Wallah I'm in a meeting now, call me baad shwaya. (call me a bit later)
25. Assalamu alaikum, yes, speaking.

**Numbers**
26. My number is zero five zero, five five five, one two three four.
27. We have about twenty-five employees.

## What happens next

The same clips go through each candidate STT (Deepgram, AssemblyAI, Soniox, Speechmatics, etc.). We score word errors per group, and especially **emails, names and times**, because those break bookings. The results decide the provider.
