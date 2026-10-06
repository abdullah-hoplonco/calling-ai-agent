"use client";

// Studio: the call as a two-track recording session. The gap between the tracks is the wait.

import Image from "next/image";
import { useEffect, useMemo, useRef, useState } from "react";

import { CallButton, CodeState, ConfigLine, ErrorNote, GuardList, LeadPicker, MuteToggle, SampleButton, StepChips, statusWord } from "@/components/blocks";
import { Meter, PartList, useNow, wavePath } from "@/components/shared";
import { TRACK, trackIndex } from "@/lib/stages";
import type { CallModel, TurnView } from "@/lib/useCall";
import { SLOW_MS, TARGET_MS, ms, partsOf, stageName, stepWord, timecode, tone, toneWord } from "@/lib/view";

const PPS = 60; // px per second on the arrangement
const px = (t: number) => (t / 1000) * PPS;
const FIXED_H = 30 + 30 + 76 + 56 + 2; // ruler, stages, wait, events, borders

export function StudioView({ c, switcher }: { c: CallModel; switcher: React.ReactNode }) {
  const [picked, setPicked] = useState<number | null>(null);
  const latest = c.turns.length - 1;
  const sel = picked != null && picked <= latest ? picked : latest;
  useEffect(() => {
    if (c.busy) setPicked(null);
  }, [c.busy, c.turns.length]);
  const turn = sel >= 0 ? c.turns[sel] : undefined;

  return (
    <div className="st">
      <Transport c={c} switcher={switcher} />
      <ErrorNote c={c} />
      <div className="st-stage" data-empty={(!c.busy && c.turns.length === 0) || undefined}>
        <Arrangement c={c} sel={sel} onPick={setPicked} />
        {!c.busy && c.turns.length === 0 && <EmptyState c={c} />}
      </div>
      <section className="st-bot">
        <Panel title="Inspector" sub={turn ? `Turn ${turn.turn.turn} · ${stageName(turn.turn.stage)}` : undefined}>
          <Inspector c={c} t={turn} />
        </Panel>
        <Panel title="Wait editor" sub="0 to 2 s, true scale">
          <WaitEditor c={c} t={turn} />
        </Panel>
        <Panel title="Code state" sub="what the code enforces">
          <CodeState snap={c.snap} />
          <h3 className="st-h3">Guard</h3>
          <GuardList snap={c.snap} />
          <ConfigLine snap={c.snap} />
        </Panel>
      </section>
    </div>
  );
}

function Transport({ c, switcher }: { c: CallModel; switcher: React.ReactNode }) {
  const now = useNow(c, c.busy);
  const o = c.summary?.overall;
  const p50 = o?.totalMs.p50 ?? null;
  const p95 = o?.totalMs.p95 ?? null;
  return (
    <header className="st-tp">
      <div className="st-brand">
        <Image src="/hoplon-logo.png" alt="Hoplon & Co" width={112} height={20} priority />
        <span>Talk to Omar</span>
      </div>
      <div className="st-btns">
        <CallButton c={c} className="st-b" />
        <SampleButton c={c} className="st-b st-b2" label="Hear sample" />
        <MuteToggle c={c} />
      </div>
      <div className="st-lcd" aria-live="off">
        <div>
          <label>Position</label>
          <b className="st-tc">{timecode(c.phase === "idle" ? 0 : now)}</b>
        </div>
        <div className="st-lcd-st">
          <label>{c.source === "sample" ? "Status · synthetic sample" : "Status"}</label>
          <b>{statusWord(c)}</b>
        </div>
        <div>
          <label>Typical · p50</label>
          <b data-tone={tone(p50)}>{ms(p50)}</b>
          <small>target {TARGET_MS}</small>
        </div>
        <div className="st-lcd-p95">
          <label>Slow · p95</label>
          <b data-tone={p95 == null ? undefined : p95 <= SLOW_MS ? "good" : "crit"}>{ms(p95)}</b>
          <small>target {SLOW_MS}</small>
        </div>
      </div>
      <div className="st-sw">{switcher}</div>
    </header>
  );
}

type Span = { key: string; i: number; who: "lead" | "omar"; a: number; b: number; text: string; open: boolean };

function Arrangement({ c, sel, onPick }: { c: CallModel; sel: number; onPick: (i: number) => void }) {
  const now = useNow(c, c.busy);
  const scroller = useRef<HTMLDivElement>(null);
  const box = useRef<HTMLElement>(null);
  const [vw, setVw] = useState(1200);
  const [vh, setVh] = useState(420);
  useEffect(() => {
    const el = scroller.current;
    const b = box.current;
    if (!el || !b) return;
    const ro = new ResizeObserver(() => {
      setVw(el.clientWidth);
      setVh(b.clientHeight);
    });
    ro.observe(el);
    ro.observe(b);
    return () => ro.disconnect();
  }, []);
  // the two voice lanes take the free height
  const laneH = Math.round(Math.min(170, Math.max(84, (vh - FIXED_H) / 2)));

  const end = c.busy ? now : c.length;
  const width = Math.max(vw, px(end) + vw * 0.5);

  // follow the playhead while the call runs
  useEffect(() => {
    const el = scroller.current;
    if (!el || !c.busy) return;
    const target = px(now) - el.clientWidth * 0.62;
    if (target > el.scrollLeft + 2) el.scrollLeft = target;
  }, [now, c.busy]);

  const spans: Span[] = [];
  c.turns.forEach((t, i) => {
    if (t.leadAt != null && t.leadEnd != null)
      spans.push({ key: `l${i}`, i, who: "lead", a: t.leadAt, b: t.leadEnd, text: t.turn.lead_text || "…", open: false });
    const open = t.omarEnd == null && c.speaking?.who === "omar";
    spans.push({
      key: `o${i}`,
      i,
      who: "omar",
      a: t.omarAt,
      b: t.omarEnd ?? (open ? now : t.omarAt + 1200),
      text: t.turn.omar_text,
      open,
    });
  });
  if (c.speaking?.who === "lead")
    spans.push({ key: "lnow", i: -1, who: "lead", a: c.speaking.since, b: now, text: c.source === "sample" ? "…" : "You", open: true });

  const markers = stageMarkers(c, end);
  // events packed in three rows; a label stops where the next one in its row starts
  const evs = c.turns
    .flatMap((t) => t.steps.map((s, k) => ({ s, x: px(t.omarAt) + k * 10 })))
    .sort((a, b) => a.x - b.x)
    .map((e, i) => ({ ...e, row: i % 3, w: 160 }));
  evs.forEach((e, i) => {
    const next = evs.slice(i + 1).find((n) => n.row === e.row);
    if (next) e.w = Math.max(12, next.x - e.x - 6);
  });

  return (
    <section className="st-arr" aria-label="Call timeline" ref={box}>
      <div className="st-heads" aria-hidden="true">
        <div className="st-th st-th-sm">Time</div>
        <div className="st-th st-th-sm">Stages</div>
        <div className="st-th" style={{ height: laneH }}>
          <span className="st-sw-c" data-who="lead" />
          <div>
            <b>{c.lead.name.split(" ")[0]}</b>
            <small>Lead · {c.source === "live" ? "you" : "caller"}</small>
          </div>
          <Meter who="lead" bars={8} />
        </div>
        <div className="st-th" style={{ height: laneH }}>
          <span className="st-sw-c" data-who="omar" />
          <div>
            <b>Omar</b>
            <small>AI agent · en-GB</small>
          </div>
          <Meter who="omar" bars={8} />
        </div>
        <div className="st-th st-th-gap">
          <span className="st-sw-c" data-who="gap" />
          <div>
            <b>Wait</b>
            <small>Lead stops → Omar speaks</small>
          </div>
        </div>
        <div className="st-th st-th-ev">
          <span className="st-sw-c" data-who="ev" />
          <div>
            <b>Events</b>
            <small>
              <i className="st-k" data-by="code" /> code <i className="st-k" data-by="llm" /> LLM
            </small>
          </div>
        </div>
      </div>
      <div className="st-scroll" ref={scroller}>
        <div className="st-tl" style={{ width }}>
          <Ruler width={width} />
          <div className="st-lane st-lane-sm">
            {markers.map((m) => (
              <div key={m.id + m.a} className="st-mk" data-on={m.now || undefined} style={{ left: px(m.a), width: Math.max(px(m.b - m.a) - 3, 24) }}>
                {m.label}
              </div>
            ))}
          </div>
          {(["lead", "omar"] as const).map((who) => (
            <div key={who} className="st-lane" data-lane={who} style={{ height: laneH }}>
              {spans
                .filter((s) => s.who === who)
                .map((s) => (
                  <Region key={s.key} s={s} h={laneH - 12 - 18} sel={s.i === sel} onPick={onPick} />
                ))}
            </div>
          ))}
          <div className="st-lane st-lane-gap">
            {c.turns.map((t, i) => (
              <Gap key={i} t={t} i={i} sel={i === sel} onPick={onPick} />
            ))}
          </div>
          <div className="st-lane st-lane-ev">
            {evs.map(({ s, x, row, w }) => (
              <span
                key={`${s.at}-${s.event}`}
                className="st-ev"
                data-by={s.by}
                title={stepWord(s)}
                style={{ left: x, top: 6 + row * 15, maxWidth: w }}
              >
                <i />
                <span>{stepWord(s)}</span>
              </span>
            ))}
          </div>
          {c.phase !== "idle" && <div className="st-ph" style={{ left: px(c.busy ? now : end) }} aria-hidden="true" />}
        </div>
      </div>
    </section>
  );
}

function Ruler({ width }: { width: number }) {
  const ticks = [];
  for (let s = 0; s * PPS < width; s++) {
    ticks.push(
      s % 5 === 0 ? (
        <span key={s} className="st-tick" style={{ left: s * PPS }}>
          {`${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`}
        </span>
      ) : (
        <span key={s} className="st-tick st-tick-minor" style={{ left: s * PPS }} />
      ),
    );
  }
  return <div className="st-lane st-ruler">{ticks}</div>;
}

function Region({ s, h, sel, onPick }: { s: Span; h: number; sel: boolean; onPick: (i: number) => void }) {
  const w = Math.max(px(s.b - s.a), 6);
  const seed = s.i * 7 + (s.who === "omar" ? 31 : 3);
  const bucket = s.open ? Math.ceil(w / 120) * 120 : Math.round(w);
  const d = useMemo(() => wavePath(seed, bucket, h), [seed, bucket, h]);
  return (
    <button
      type="button"
      className="st-rg"
      data-who={s.who}
      data-sel={sel || undefined}
      data-open={s.open || undefined}
      style={{ left: px(s.a), width: w }}
      onClick={() => s.i >= 0 && onPick(s.i)}
      tabIndex={s.i >= 0 ? 0 : -1}
      aria-label={`${s.who === "lead" ? "Lead" : "Omar"}: ${s.text}`}
    >
      <span className="st-rg-hd">{s.text}</span>
      <svg viewBox={`0 0 ${bucket} ${h}`} width={bucket} height={h} preserveAspectRatio="none" aria-hidden="true">
        <path d={d} />
      </svg>
    </button>
  );
}

function Gap({ t, i, sel, onPick }: { t: TurnView; i: number; sel: boolean; onPick: (i: number) => void }) {
  const total = t.turn.totalMs;
  if (total == null) {
    if (t.leadEnd == null) return null;
    return (
      <span className="st-gap st-gap-scr" style={{ left: px(t.leadEnd), width: Math.max(px(t.omarAt - t.leadEnd), 10) }}>
        {px(t.omarAt - t.leadEnd) >= 40 && <b>script</b>}
      </span>
    );
  }
  const parts = partsOf(t.turn);
  return (
    <button
      type="button"
      className="st-gap"
      data-sel={sel || undefined}
      data-fresh={t.fresh || undefined}
      style={{ left: px(t.leadEnd ?? t.omarAt - total), width: Math.max(px(t.omarAt - (t.leadEnd ?? t.omarAt - total)), 8) }}
      onClick={() => onPick(i)}
      aria-label={`Turn ${t.turn.turn} wait ${total} ms`}
    >
      {parts.map((p) => (
        <i key={p.key} className={`p-${p.cls}`} style={{ flexGrow: p.ms }} />
      ))}
      <b data-tone={tone(total)}>{Math.round(total)}</b>
    </button>
  );
}

function stageMarkers(c: CallModel, end: number) {
  const out: { id: string; label: string; a: number; b: number; now: boolean }[] = [];
  let cur = -1;
  c.turns.forEach((t) => {
    const idx = trackIndex(t.turn.stage);
    if (idx !== cur && idx >= 0) {
      const a = t.leadAt ?? t.omarAt;
      if (out.length) out[out.length - 1]!.b = a;
      out.push({ id: TRACK[idx]!.id, label: TRACK[idx]!.label, a, b: end, now: false });
      cur = idx;
    }
  });
  const live = trackIndex(c.snap?.stage);
  if (live >= 0 && live !== cur && c.turns.length) {
    const a = c.turns[c.turns.length - 1]!.omarEnd ?? end;
    if (out.length) out[out.length - 1]!.b = a;
    out.push({ id: TRACK[live]!.id, label: TRACK[live]!.label, a, b: Math.max(end, a + 2000), now: false });
  }
  if (out.length && c.busy) out[out.length - 1]!.now = true;
  return out;
}

function EmptyState({ c }: { c: CallModel }) {
  return (
    <div className="st-empty">
      <div className="st-empty-card">
        <h1>Talk to Omar</h1>
        <p>
          Omar is an AI calling agent. He phones a warm Lead, answers questions and books a Discovery Call. Every reply is
          timed: this timeline shows each wait, split into its parts.
        </p>
        <LeadPicker c={c} compact />
        <div className="st-empty-btns">
          <CallButton c={c} className="st-b" />
          <SampleButton c={c} className="st-b st-b2" />
        </div>
        <p className="st-hint">Use a headset. The browser asks for the microphone when you call. The sample needs no keys.</p>
      </div>
    </div>
  );
}

function Panel({ title, sub, children }: { title: string; sub?: string; children: React.ReactNode }) {
  return (
    <div className="st-pn">
      <div className="st-pn-h">
        <h2>{title}</h2>
        {sub && <span>{sub}</span>}
      </div>
      <div className="st-pn-b">{children}</div>
    </div>
  );
}

function Inspector({ c, t }: { c: CallModel; t: TurnView | undefined }) {
  if (!t) return <p className="muted">Each reply appears here as Omar speaks. Click any region on the timeline to inspect it.</p>;
  return (
    <div className="st-ins">
      <p className="st-line" data-who="lead">
        <span>{c.lead.name.split(" ")[0]?.toUpperCase()}</span>
        {t.turn.lead_text || <em>(picks up the phone)</em>}
      </p>
      <p className="st-line" data-who="omar">
        <span>OMAR</span>
        <span>
          {t.turn.omar_text}
          {t.turn.interrupted && <span className="st-cut">cut off by the Lead</span>}
        </span>
      </p>
      <StepChips steps={t.steps} tool={t.turn.toolTurn} />
    </div>
  );
}

const SCALE = 2000;
function WaitEditor({ c, t }: { c: CallModel; t: TurnView | undefined }) {
  if (!t) return <p className="muted">The wait before each reply, drawn to scale against the 0.9 s target.</p>;
  const total = t.turn.totalMs;
  if (total == null)
    return (
      <div className="st-we">
        <div className="st-we-top">
          <b className="st-we-total st-we-none">—</b>
          <span className="muted">Scripted line. Spoken by code, so the wait is not measured.</span>
        </div>
      </div>
    );
  const parts = partsOf(t.turn);
  const tn = tone(total);
  const p50 = c.summary?.overall.totalMs.p50;
  return (
    <div className="st-we">
      <div className="st-we-top">
        <b className="st-we-total">
          {Math.round(total).toLocaleString("en-US")}
          <small>ms</small>
        </b>
        <span className="st-pill" data-tone={tn}>
          {toneWord(tn)}
        </span>
        <span className="st-we-note">
          {t.turn.toolTurn ? "With tool call" : "Plain reply"}
          {t.heardMs != null && ` · ≈ heard ${t.heardMs} ms`}
          {p50 != null && ` · call p50 ${Math.round(p50)} ms`}
        </span>
      </div>
      <div className="st-we-scale" key={`${t.turn.turn}-${total}`}>
        <span className="st-we-line" data-k="target" style={{ left: `${(TARGET_MS / SCALE) * 100}%` }}>
          <em>target 0.9 s</em>
        </span>
        <span className="st-we-line" data-k="slow" style={{ left: `${(SLOW_MS / SCALE) * 100}%` }}>
          <em>slow 1.5 s</em>
        </span>
        <div className="st-we-blocks">
          {parts.map((p, i) => (
            <div
              key={p.key}
              className={`st-we-b p-${p.cls}`}
              style={{ width: `${(Math.min(p.ms, SCALE) / SCALE) * 100}%`, animationDelay: `${i * 80}ms` }}
              title={`${p.label}: ${p.ms} ms. ${p.hint}`}
            >
              {p.ms >= 120 && <span>{p.ms}</span>}
            </div>
          ))}
        </div>
        <div className="st-we-axis">
          {[0, 500, 1000, 1500, 2000].map((m) => (
            <span key={m} style={{ left: `${(m / SCALE) * 100}%` }}>
              {m}
            </span>
          ))}
        </div>
      </div>
      <PartList parts={parts} total={total} />
    </div>
  );
}
