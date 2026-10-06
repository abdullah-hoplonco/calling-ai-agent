"""Turn latency records, p50/p95 summaries and the JSON-lines log.

The numbers come from omar_voice.timing (one clock, from the end of the Lead's last
word to Omar's first audio frame). The browser adds mouth-to-ear on its side.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SUMMARY_KEYS = (
    "turnDetectMs",
    "commitMs",
    "toolMs",
    "llmMs",
    "guardMs",
    "ttsMs",
    "totalMs",
    "ttsTtfbMs",
    "ttsRealtimeFactor",
)


def percentile(values: list[float], p: float) -> float | None:
    """Nearest-rank percentile. None for no data."""
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(p / 100 * len(ordered)))
    return ordered[rank - 1]


def _summ(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {"n": len(rows)}
    for key in SUMMARY_KEYS:
        vals = [r[key] for r in rows if r.get(key) is not None]
        out[key] = {"p50": percentile(vals, 50), "p95": percentile(vals, 95)}
    return out


@dataclass
class LatencyBook:
    target_p50_ms: float = 900.0
    target_p95_ms: float = 1500.0
    log_path: Path | None = None
    rows: dict[int, dict[str, Any]] = field(default_factory=dict)

    def put(self, row: dict[str, Any], *, final: bool) -> None:
        """Add or replace the row for row["turn"]. Final rows are also written to the log."""
        self.rows[row["turn"]] = row
        if final and self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")

    def measured(self) -> list[dict[str, Any]]:
        """Replies with a full measurement: a Lead turn before them and a total."""
        return [r for r in self.rows.values() if r.get("totalMs") is not None]

    def summary(self) -> dict[str, Any]:
        rows = self.measured()
        overall = _summ(rows)
        p50 = overall["totalMs"]["p50"]
        p95 = overall["totalMs"]["p95"]
        stages = sorted({r["stage"] for r in rows})
        return {
            "overall": overall,
            "byStage": {s: _summ([r for r in rows if r["stage"] == s]) for s in stages},
            "toolTurns": _summ([r for r in rows if r.get("toolTurn")]),
            "plainTurns": _summ(
                [r for r in rows if not r.get("toolTurn") and not r.get("scripted")]
            ),
            "scriptedTurns": _summ([r for r in rows if r.get("scripted")]),
            "target": {"p50": self.target_p50_ms, "p95": self.target_p95_ms},
            "pass": None
            if p50 is None
            else bool(p50 <= self.target_p50_ms and (p95 or 0) <= self.target_p95_ms),
        }
