"""LLM cost per request, from the providers' published prices.

DeepSeek: https://api-docs.deepseek.com/quick_start/pricing (read 2026-10-07).
Prices are USD per 1M tokens. Every input token is priced as a CACHE MISS (the worst
case, on purpose): the live cost is then an upper bound the owner can plan with.
Peak hours (2x price): 01:00-04:00 and 06:00-10:00 UTC, Monday to Friday.
Groq: free tier, so 0.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

PRICES_SOURCE = "api-docs.deepseek.com/quick_start/pricing, read 2026-10-07; cache miss assumed"


@dataclass(frozen=True)
class Rate:
    input_off: float  # per 1M input tokens, cache miss, off-peak
    output_off: float
    input_peak: float
    output_peak: float


DEEPSEEK_RATES: dict[str, Rate] = {
    "deepseek-flash": Rate(0.15, 0.60, 0.30, 1.20),  # V4.1 Flash
    "deepseek-v4-pro": Rate(0.66, 1.98, 1.32, 3.96),
}
DEEPSEEK_ALIASES = {
    "deepseek-v4-flash": "deepseek-flash",
    "deepseek-v4-flash-vision-exp": "deepseek-flash",
}
PEAK_UTC_HOURS = ((1, 4), (6, 10))  # [start, end) hours, Monday-Friday


def provider_of(host_or_name: str) -> str:
    """'api.groq.com' -> 'groq', 'api.deepseek.com' -> 'deepseek', else the input."""
    h = (host_or_name or "").lower()
    if "groq" in h:
        return "groq"
    if "deepseek" in h:
        return "deepseek"
    if "cerebras" in h:
        return "cerebras"
    return h or "unknown"


def is_peak(when: datetime) -> bool:
    t = when.astimezone(UTC)
    return t.weekday() < 5 and any(a <= t.hour < b for a, b in PEAK_UTC_HOURS)


@dataclass(frozen=True)
class Cost:
    usd: float
    band: str  # "off-peak" | "peak" | "free tier" | "unknown price"


def request_cost(
    provider: str, model: str, prompt_tokens: int, completion_tokens: int, when: datetime
) -> Cost:
    if provider == "groq":
        return Cost(0.0, "free tier")
    if provider == "deepseek":
        rate = DEEPSEEK_RATES.get(DEEPSEEK_ALIASES.get(model, model))
        if rate is None:
            return Cost(0.0, "unknown price")
        peak = is_peak(when)
        rin = rate.input_peak if peak else rate.input_off
        rout = rate.output_peak if peak else rate.output_off
        usd = (max(prompt_tokens, 0) * rin + max(completion_tokens, 0) * rout) / 1_000_000
        return Cost(round(usd, 8), "peak" if peak else "off-peak")
    return Cost(0.0, "unknown price")
