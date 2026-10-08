from datetime import UTC, datetime

import pytest

from omar_voice.pricing import is_peak, provider_of, request_cost

MON_OFF = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)  # Monday 12:00 UTC: off-peak
MON_PEAK = datetime(2026, 10, 5, 7, 30, tzinfo=UTC)  # Monday 07:30 UTC: peak
SAT_PEAK_HOUR = datetime(2026, 10, 10, 7, 30, tzinfo=UTC)  # weekend: off-peak


def test_provider_from_host():
    assert provider_of("api.groq.com") == "groq"
    assert provider_of("api.deepseek.com") == "deepseek"


def test_peak_windows():
    assert is_peak(MON_PEAK) and not is_peak(MON_OFF) and not is_peak(SAT_PEAK_HOUR)
    assert is_peak(datetime(2026, 10, 5, 1, 0, tzinfo=UTC))
    assert not is_peak(datetime(2026, 10, 5, 4, 0, tzinfo=UTC))


def test_deepseek_cost_cache_miss_off_peak():
    # 1,300 prompt tokens at $0.15/M + 60 output tokens at $0.60/M
    c = request_cost("deepseek", "deepseek-flash", 1300, 60, MON_OFF)
    assert c.band == "off-peak"
    assert c.usd == pytest.approx(1300 * 0.15e-6 + 60 * 0.60e-6)


def test_deepseek_cost_doubles_at_peak():
    off = request_cost("deepseek", "deepseek-flash", 1000, 100, MON_OFF).usd
    peak = request_cost("deepseek", "deepseek-flash", 1000, 100, MON_PEAK).usd
    assert peak == pytest.approx(2 * off)


def test_groq_free_and_unknown_model():
    assert request_cost("groq", "qwen/qwen3.8-27b", 1000, 100, MON_OFF).band == "free tier"
    assert request_cost("deepseek", "deepseek-future", 1000, 100, MON_OFF).band == "unknown price"
    assert request_cost("deepseek", "deepseek-v4-flash", 1000, 0, MON_OFF).usd > 0  # alias
