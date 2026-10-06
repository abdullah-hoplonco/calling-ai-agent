"""The agency knowledge sheet, cut into small topics for the lookup tool.

The full sheet is about 4,500 tokens. Groq's free tier allows 8,000 tokens a
minute, so Omar never gets the full sheet in his prompt. He calls
`lookup_service(topic)` and gets one section only.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SHEET = REPO_ROOT / ".scratch" / "calling-agent" / "assets" / "agency-knowledge.md"

# topic id -> (how to find it in the sheet, description for the LLM)
_CORE_SERVICES = {
    "branding": "1. Branding",
    "websites": "2. Website Design",
    "mobile_apps": "3. Mobile App",
    "custom_software": "4. Software Development",
    "saas": "5. SaaS",
    "ecommerce": "6. E-Commerce",
    "digital_marketing": "7. Digital Marketing",
    "seo": "8. Search Engine",
    "pr": "9. Public Relations",
}
_SECTIONS = {
    "company": "## 1. Company facts",
    "specialist_services": "### 2b. Specialist services",
    "process": "## 3. Process",
    "differentiators": "## 4. Differentiators",
    "portfolio": "## 5. Portfolio",
    "faqs": "## 6. FAQs",
}

TOPICS: dict[str, str] = {
    "company": "who we are, offices, experience",
    "branding": "logos, brand identity, rebrand",
    "websites": "websites, landing pages, online stores, maintenance",
    "mobile_apps": "iOS and Android apps",
    "custom_software": "CRM, ERP, dashboards, custom systems",
    "saas": "ready-made cloud platforms",
    "ecommerce": "online stores, payments, checkout",
    "digital_marketing": "ads, social media, content, reporting",
    "seo": "Google rankings, audits, local SEO",
    "pr": "press, media, reputation",
    "specialist_services": "Instagram, TikTok, LinkedIn, lead generation, UI/UX and more",
    "process": "how a project runs, first steps",
    "differentiators": "why choose Hoplon",
    "portfolio": "industries and named clients",
    "faqs": "common questions: sizes, Arabic, payment methods, tech",
}


def _strip_noise(text: str) -> str:
    text = re.sub(r"`?\[(?:VERIFY|GAP)\]`?", "", text)
    text = re.sub(r"\(Owner confirmed[^)]*\)", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _section(sheet: str, start: str) -> str:
    i = sheet.find(start)
    if i < 0:
        return ""
    level = start.split(" ", 1)[0]  # '##' or '###'
    rest = sheet[i + len(start) :]
    stops = [rest.find(f"\n{h} ") for h in ("##", "###") if len(h) <= len(level)]
    stops += [rest.find("\n---")]
    stops = [s for s in stops if s >= 0]
    end = min(stops) if stops else len(rest)
    return start.lstrip("# ") + rest[:end]


def _core_service(sheet: str, marker: str) -> str:
    m = re.search(
        rf"\*\*{re.escape(marker)}[^\n]*\*\*\n(.*?)(?=\n\*\*\d+\.|\n### |\n---)", sheet, re.DOTALL
    )
    return (marker + "\n" + m.group(1)) if m else ""


@lru_cache(maxsize=4)
def load(path: str | None = None) -> dict[str, str]:
    sheet = Path(path or DEFAULT_SHEET).read_text(encoding="utf-8")
    out: dict[str, str] = {}
    for topic, marker in _CORE_SERVICES.items():
        out[topic] = _strip_noise(_core_service(sheet, marker))
    for topic, start in _SECTIONS.items():
        out[topic] = _strip_noise(_section(sheet, start))
    return out


def lookup(topic: str, path: str | None = None) -> str:
    sections = load(path)
    text = sections.get(topic)
    if not text:
        return (
            "No information on that. Say: 'Good question. I'll make sure our manager "
            "covers that on the call.'"
        )
    return text
