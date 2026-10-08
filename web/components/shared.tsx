"use client";

// Building blocks every theme shares. Each theme styles them through its own CSS variables.

import { useEffect, useRef, useState } from "react";

import { levels } from "@/lib/levels";
import type { Turn } from "@/lib/types";
import type { CallModel, TurnView } from "@/lib/useCall";
import { PARTS, TARGET_MS, partsOf, percentile, type Part } from "@/lib/view";

export const THEMES = [
  { id: "studio", label: "Studio" },
  { id: "console", label: "Console" },
  { id: "enterprise", label: "Enterprise" },
  { id: "showcase", label: "Showcase" },
] as const;
export type Ui = (typeof THEMES)[number]["id"];

export function ThemeSwitch({ ui, setUi }: { ui: Ui; setUi: (u: Ui) => void }) {
  return (
    <div className="ts" role="radiogroup" aria-label="Theme">
      {THEMES.map((t) => (
        <button
          key={t.id}
          type="button"
          role="radio"
          aria-checked={ui === t.id}
          className="ts-opt"
          data-on={ui === t.id || undefined}
          onClick={() => setUi(t.id)}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

// The parts of one wait. With scaleMs the bar sits on a fixed scale with the 0.9 s target tick.
export function PartsBar({
  turn,
  parts,
  scaleMs,
  animate = false,
  className = "",
}: {
  turn?: Turn;
  parts?: Part[];
  scaleMs?: number;
  animate?: boolean;
  className?: string;
}) {
  const ps = parts ?? (turn ? partsOf(turn) : []);
  const total = ps.reduce((a, p) => a + p.ms, 0);
  const label = ps.map((p) => `${p.label} ${p.ms} ms`).join(", ");
  return (
    <div className={`pb ${className}`} role="img" aria-label={`Total ${total} ms. ${label}.`}>
      <div className="pb-rail">
        {ps.map((p, i) => (
          <i
            key={p.key}
            className={`pb-seg p-${p.cls}`}
            data-animate={animate || undefined}
            style={{
              width: scaleMs ? `${Math.min(p.ms / scaleMs, 1) * 100}%` : undefined,
              flexGrow: scaleMs ? undefined : p.ms,
              animationDelay: animate ? `${i * 70}ms` : undefined,
            }}
          />
        ))}
        {scaleMs && <span className="pb-target" style={{ left: `${(TARGET_MS / scaleMs) * 100}%` }} aria-hidden="true" />}
      </div>
    </div>
  );
}

export function PartList({ parts, total, totalLabel = "Total wait" }: { parts: Part[]; total?: number; totalLabel?: string }) {
  const sum = total ?? parts.reduce((a, p) => a + p.ms, 0);
  return (
    <ul className="pl">
      {parts.map((p) => (
        <li key={p.key} title={p.hint}>
          <i className={`pl-sw p-${p.cls}`} aria-hidden="true" />
          <span className="pl-name">{p.label}</span>
          <b className="pl-ms">{p.ms.toLocaleString("en-US")} ms</b>
          <em className="pl-pc">{sum ? Math.round((p.ms / sum) * 100) : 0}%</em>
        </li>
      ))}
      <li className="pl-total">
        <i aria-hidden="true" />
        <span className="pl-name">{totalLabel}</span>
        <b className="pl-ms">{sum.toLocaleString("en-US")} ms</b>
        <em className="pl-pc" />
      </li>
    </ul>
  );
}

// Median of each part over the measured replies.
export function medianParts(turns: TurnView[]): Part[] {
  const ts = turns.filter((r) => r.turn.totalMs != null && !r.turn.scripted).map((r) => r.turn);
  return PARTS.map((p) => {
    const v = ts.map((t) => t[p.key]).filter((x): x is number => typeof x === "number");
    return { ...p, ms: Math.round(percentile(v, 50) ?? 0) };
  }).filter((p) => p.ms > 0);
}

export function Meter({ who, bars = 10 }: { who: "lead" | "omar"; bars?: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    let id = 0;
    const loop = () => {
      const el = ref.current;
      if (el) {
        const lit = Math.round(Math.min(levels[who] * 3, 1) * bars);
        el.querySelectorAll("i").forEach((b, i) => b.toggleAttribute("data-on", i < lit));
      }
      id = requestAnimationFrame(loop);
    };
    id = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(id);
  }, [who, bars]);
  return (
    <span className="meter" ref={ref} aria-hidden="true">
      {Array.from({ length: bars }, (_, i) => (
        <i key={i} />
      ))}
    </span>
  );
}

// Re-renders its user every animation frame while active, for clocks and playheads.
export function useNow(c: CallModel, active: boolean): number {
  const [t, setT] = useState(0);
  useEffect(() => {
    if (!active) {
      setT(c.endedAt ?? c.length);
      return;
    }
    let id = 0;
    const loop = () => {
      setT(c.now());
      id = requestAnimationFrame(loop);
    };
    id = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(id);
  }, [c, active]);
  return t;
}

// A deterministic speech-like waveform path for a region of w x h pixels.
export function wavePath(seed: number, w: number, h: number, step = 3): string {
  let s = (seed * 9301 + 49297) % 233280;
  const rnd = () => (s = (s * 9301 + 49297) % 233280) / 233280;
  const n = Math.max(2, Math.floor(w / step));
  const mid = h / 2;
  let d = "";
  for (let i = 0; i < n; i++) {
    const pos = i / n;
    const env = Math.min(1, Math.sin(Math.PI * pos) * 3) * (0.35 + 0.65 * Math.abs(Math.sin(i / 3.7 + seed)));
    const a = Math.max(0.08, env * (0.45 + rnd() * 0.55)) * (mid - 2);
    const x = i * step + step / 2;
    d += `M${x.toFixed(1)} ${(mid - a).toFixed(1)}V${(mid + a).toFixed(1)}`;
  }
  return d;
}

// The whole call as one recording: the Lead above the line, Nimra below.
export function Waveform({ c, height = 96 }: { c: CallModel; height?: number }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const live = c.busy;
  const { turns, speaking } = c;
  useEffect(() => {
    let id = 0;
    const draw = () => {
      const cv = ref.current;
      if (!cv) return;
      const r = cv.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      if (cv.width !== Math.round(r.width * dpr)) cv.width = Math.round(r.width * dpr);
      if (cv.height !== Math.round(r.height * dpr)) cv.height = Math.round(r.height * dpr);
      const g = cv.getContext("2d");
      if (!g) return;
      g.setTransform(dpr, 0, 0, dpr, 0, 0);
      g.clearRect(0, 0, r.width, r.height);
      const css = getComputedStyle(cv);
      const leadC = css.getPropertyValue("--wave-lead").trim() || "#8b93a7";
      const omarC = css.getPropertyValue("--wave-omar").trim() || "#2f56e0";
      const axis = css.getPropertyValue("--wave-axis").trim() || "#ddd";
      const now = c.now();
      const len = Math.max(live ? now : c.length, 20000);
      const mid = r.height / 2;
      g.fillStyle = axis;
      g.fillRect(0, mid - 0.5, r.width, 1);
      const spans: { who: "lead" | "omar"; a: number; b: number }[] = [];
      for (const t of turns) {
        if (t.leadAt != null && t.leadEnd != null) spans.push({ who: "lead", a: t.leadAt, b: t.leadEnd });
        spans.push({ who: "omar", a: t.omarAt, b: t.omarEnd ?? (speaking?.who === "omar" ? now : t.omarAt + 1500) });
      }
      if (speaking?.who === "lead") spans.push({ who: "lead", a: speaking.since, b: now });
      const bw = 2;
      const gap = 1.25;
      const n = Math.floor(r.width / (bw + gap));
      for (let k = 0; k < n; k++) {
        const t = (k / n) * len;
        const sp = spans.find((s) => t >= s.a && t < s.b);
        if (!sp) continue;
        const pos = (t - sp.a) / Math.max(1, sp.b - sp.a);
        const rnd = Math.abs(Math.sin(k * 12.9898) * 43758.5453) % 1;
        const env = Math.min(1, Math.sin(Math.PI * pos) * 2.4) * (0.35 + 0.65 * Math.abs(Math.sin(k / 2.3)));
        const h = Math.max(2, env * (0.4 + rnd * 0.6) * (mid - 4));
        g.fillStyle = sp.who === "lead" ? leadC : omarC;
        const x = k * (bw + gap);
        if (sp.who === "lead") g.fillRect(x, mid - h - 1, bw, h);
        else g.fillRect(x, mid + 1, bw, h);
      }
      if (live) id = requestAnimationFrame(draw);
    };
    draw();
    const onResize = () => draw();
    window.addEventListener("resize", onResize);
    return () => {
      cancelAnimationFrame(id);
      window.removeEventListener("resize", onResize);
    };
  }, [c, live, turns, speaking]);
  return <canvas ref={ref} className="wave-cv" style={{ height }} aria-hidden="true" />;
}

// Where on the waveform (0..1) a time sits, on the same scale the waveform uses.
export function waveX(c: CallModel, t: number, now: number): number {
  const len = Math.max(c.busy ? now : c.length, 20000);
  return Math.min(1, Math.max(0, t / len));
}
