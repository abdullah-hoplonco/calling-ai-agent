"""Call language: English, plus everyday Hindi when the call allows it (CallConfig.hindi).

Hindi here is the spoken Hindustani of Delhi and Mumbai, close to Urdu: common words
like "zaroor", "shukriya", "waqt", never formal Sanskrit-heavy Hindi. It is written in
Devanagari (what Deepgram returns for Hindi speech and what the TTS reads best), with
English business words kept in English letters.

The company name is always "Hoplon and Co" in English letters, in every language:
fix_brand() puts it back if a Hindi sentence spells it in Devanagari.
"""

from __future__ import annotations

import re
from typing import Literal

Lang = Literal["en", "hi"]
BRAND = "Hoplon and Co"

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_LATIN = re.compile(r"[A-Za-z]")
# Hindi written in English letters (some STT output and chat text): common function words
_ROMAN_HINDI = re.compile(
    r"\b(?:hai|hain|nahi|nahin|kya|kaise|mujhe|aap|aapka|aapki|haan|haanji|hoon|hun|"
    r"raha|rahi|karna|karte|kar|bhi|abhi|theek|thik|accha|achha|bataiye|boliye|ji)\b",
    re.IGNORECASE,
)


def detect(text: str) -> Lang | None:
    """The language of one Lead turn, or None when it is too short to tell.

    Devanagari letters mean Hindi, even with English words mixed in ("आपकी website").
    """
    dev = len(_DEVANAGARI.findall(text))
    lat = len(_LATIN.findall(text))
    if dev >= 2 and dev >= lat / 3:
        return "hi"
    if lat >= 3:
        return "hi" if len(_ROMAN_HINDI.findall(text)) >= 2 else "en"
    return None


# "Hoplon" spelled in Devanagari, with an optional "and Co" after it
_BRAND_DEV = re.compile(
    r"(?<![\u0900-\u0963\u0966-\u097F])(?:हो|हॉ|हौ|हा)प्?\s?ल(?:ो|ॉ|ौ|ा)?न्?(?![\u0900-\u0963\u0966-\u097F])"
    r"(?:\s*(?:एंड|ऐंड|एन्ड|&|and)\s*(?:को|कंपनी|कम्पनी|Co\b\.?))?"
)
_BRAND_LATIN = re.compile(r"\bhoplon\s*(?:&|and|n)\s*co\b\.?", re.IGNORECASE)


def fix_brand(text: str) -> str:
    """Keep the company name in English letters so the TTS always says it the same way."""
    out = _BRAND_DEV.sub(BRAND, text)
    out = _BRAND_LATIN.sub(BRAND, out)
    return out.replace(f"{BRAND} {BRAND}", BRAND)


_GENDER = re.compile(r"\{g:([^/{}]*)/([^{}]*)\}")


def gendered(template: str, female: bool) -> str:
    """'{g:रही/रहा}' -> the agent's form. Hindi verbs agree with the speaker."""
    return _GENDER.sub(lambda m: m.group(1) if female else m.group(2), template)


# Scripted lines in everyday Hindi. Keys match LINES_EN in state_machine.py.
# {g:female/male} picks the agent's verb form.
LINES_HI: dict[str, str] = {
    "identity": "हेलो, क्या मेरी बात {first_name} से हो रही है?",
    "identity_unclear_1": (
        "मैं " + BRAND + " से {agent} बोल {g:रही/रहा} हूँ। क्या मेरी बात {first_name} से हो रही है?"
    ),
    "identity_unclear_2": "माफ़ कीजिए, बस confirm करना था, क्या मैं {first_name} से बात कर {g:रही/रहा} हूँ?",
    "wrong_number": "माफ़ कीजिए, लगता है गलत नंबर लग गया। आपका दिन अच्छा रहे!",
    "opening_new": (
        "हाय {first_name}, मैं " + BRAND + " से {agent} बोल {g:रही/रहा} हूँ। आपने हमारी website पर "
        "एक form भरा था, तो मैं उसी के बारे में जानकारी देने के लिए call कर {g:रही/रहा} हूँ। "
        "बता दूँ, ये call record हो रही है। क्या अभी दो मिनट बात हो सकती है?"
    ),
    "opening_old": (
        "हाय {first_name}, मैं " + BRAND + " से {agent} बोल {g:रही/रहा} हूँ। आपने {month} में हमसे "
        "बात की थी, तो मैं वही जानकारी लेकर follow up कर {g:रही/रहा} हूँ। "
        "बता दूँ, ये call record हो रही है। क्या अभी दो मिनट बात हो सकती है?"
    ),
    "objects_recording": (
        "बिल्कुल समझ {g:सकती/सकता} हूँ। Recording के बिना मैं आगे नहीं बढ़ {g:सकती/सकता}, लेकिन मैं आपको "
        "सारी जानकारी email कर {g:दूँगी/दूँगा}। आपके वक़्त के लिए शुक्रिया!"
    ),
    "parked_objections": (
        "बिल्कुल ठीक है। मैं आपको details email कर {g:देती/देता} हूँ, और जब भी सही वक़्त हो, "
        "आप हमसे बात कर सकते हैं। शुक्रिया, {first_name}!"
    ),
    "no_intent": (
        "कोई बात नहीं। मैं आपको कुछ जानकारी email कर {g:देती/देता} हूँ, ताकि जब आप तैयार हों "
        "तो आपके पास रहे। शुक्रिया!"
    ),
    "max_callbacks": "कोई बात नहीं। मैं आपको details email कर {g:देती/देता} हूँ। शुक्रिया!",
    "callback_booked": "Perfect, मैं आपको {time} call {g:करूँगी/करूँगा}। तब बात करते हैं!",
    "not_interested": "समझ {g:गई/गया}, मैं दोबारा call नहीं {g:करूँगी/करूँगा}। आपका दिन अच्छा रहे!",
    "no_slots": (
        "अभी मुझे कोई अच्छा time नहीं दिख रहा, तो मैं आपको एक link email कर {g:देती/देता} हूँ, "
        "जो भी time आपको ठीक लगे, चुन लीजिए। शुक्रिया, {first_name}!"
    ),
    "no_slot_agreed": (
        "कोई बात नहीं। मैं आपको एक link email कर {g:देती/देता} हूँ, जो भी time आपको ठीक लगे, "
        "चुन लीजिए। शुक्रिया, {first_name}!"
    ),
    "lock_in": "एक second, मैं इसे पक्का कर {g:रही/रहा} हूँ।",
    "booked": (
        "आपकी call {slot} को मेरे manager के साथ fix हो गई है। Google Meet link के साथ invite "
        "आपको भेज दिया है। शुक्रिया, {first_name}!"
    ),
    "slot_taken": "अरे, लगता है वो time अभी-अभी किसी ने ले लिया, माफ़ कीजिए।",
    "calendar_error": (
        "अभी calendar में थोड़ी दिक्कत आ रही है, तो मैं आपको time चुनने के लिए एक link email "
        "कर {g:देती/देता} हूँ। माफ़ कीजिए!"
    ),
    "no_budget": (
        "ये असल में आपकी ज़रूरत पर depend करता है, और हम budget को आपके हिसाब से adjust कर "
        "सकते हैं। मेरे manager आपके साथ ये सब detail में देख लेंगे।"
    ),
    "no_timeline": (
        "हम timeline को आपकी ज़रूरत के हिसाब से adjust कर सकते हैं। मेरे manager आपके साथ पूरा plan बना लेंगे।"
    ),
    "ai": "सच बताऊँ तो, मैं " + BRAND + " की AI assistant हूँ।",
    "manager": "मैं आपकी बात अपने manager से करवा {g:सकती/सकता} हूँ।",
    "booking_hold": "एक second, मैं calendar पर confirm कर {g:लेती/लेता} हूँ।",
}

# The reply-language rule added to the prompt when the call allows Hindi.
PROMPT_RULE = """Language: the Lead may speak English or Hindi, or mix both.
- Reply in the language given under "Reply language" below. Never mix scripts inside one word.
- Hindi means simple everyday spoken Hindi, the way people talk in Delhi or Mumbai, close to Urdu: use common words like zaroor, shukriya, waqt, mushkil, kaam, baat. Never use formal or Sanskrit-heavy Hindi.
- Write Hindi in Devanagari. Keep English business words in English letters: website, app, budget, manager, meeting, call, email.
- You are {gender_word}: use {gender_word} Hindi verb forms ({example}).
- The company name is always "Hoplon and Co" in English letters, in every language. Never translate or spell it in Devanagari.
- Mood tags stay in English, like [curious]."""


def prompt_rule(female: bool) -> str:
    return PROMPT_RULE.format(
        gender_word="a woman" if female else "a man",
        example="मैं बोल रही हूँ, मैं कर दूँगी" if female else "मैं बोल रहा हूँ, मैं कर दूँगा",
    )


def reply_language_line(lang: Lang) -> str:
    if lang == "hi":
        return "Reply language: Hindi (the Lead is speaking Hindi)."
    return "Reply language: English. Switch to Hindi only when the Lead speaks Hindi."
