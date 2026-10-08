"use client";

// Enterprise: a premium call-intelligence workspace in the Hoplon navy, with compliance and
// pipeline cards beside the conversation.

import Image from "next/image";
import { useEffect, useRef, useState } from "react";

import { CallButton, CodeState, ErrorNote, GuardList, LeadPicker, MuteToggle, Opening, SampleButton, StepChips, statusWord } from "@/components/blocks";
import { IconCheck } from "@/components/icons";
import { Meter, PartList, PartsBar, Waveform, medianParts, useNow } from "@/components/shared";
import { TRACK, shortStatus, trackIndex } from "@/lib/stages";
import type { CallModel, TurnView } from "@/lib/useCall";
import { SLOW_MS, TARGET_MS, clock, initials, ms, num, partsOf, sec, stageName, tone, toneWord } from "@/lib/view";

export function EnterpriseView({ c, switcher }: { c: CallModel; switcher: React.ReactNode }) {
  const [picked, setPicked] = useState<number | null>(null);
  useEffect(() => {
    if (c.busy) setPicked(null);
  }, [c.busy, c.turns.length]);
  const measured = c.turns.map((t, i) => (t.turn.totalMs != null ? i : -1)).filter((i) => i >= 0);
  const sel = picked ?? measured[measured.length - 1] ?? -1;
  const selTurn = sel >= 0 ? c.turns[sel] : undefined;

  return (
    <div className="en">
      <header className="en-nav">
        <div className="en-nav-l">
          <Image src="/hoplon-logo.png" alt="Hoplon & Co" width={120} height={22} priority />
          <span className="en-prod">Call Intelligence</span>
        </div>
        <div className="en-nav-r">
          {switcher}
        </div>
      </header>

      <section className="en-band">
        <div className="en-band-in">
          <div className="en-title">
            <h1>Live call review</h1>
            <p>
              Nimra calling <b>{c.lead.name}</b> · {statusWord(c)}
              {c.source === "sample" && <span className="en-synth">Sample · synthetic numbers</span>}
            </p>
          </div>
          <div className="en-actions">
            <MuteToggle c={c} />
            <SampleButton c={c} className="en-btn en-ghost" />
            <CallButton c={c} className="en-btn en-gold" />
          </div>
        </div>
        <Stepper c={c} />
      </section>

      <div className="en-wrap">
        <ErrorNote c={c} />
        <Kpis c={c} />
        <div className="en-grid">
          <div className="en-col">
            <Conversation c={c} sel={sel} onPick={setPicked} />
          </div>
          <div className="en-col">
            <Card title={c.busy ? "On the line" : "Choose a Lead"} sub={c.busy ? undefined : "3 synthetic Leads"}>
              {c.busy ? <LeadProfile c={c} /> : <LeadPicker c={c} />}
            </Card>
            {selTurn && (
              <Card title="Response time" sub={`Turn ${selTurn.turn.turn}`} feature>
                <Response c={c} t={selTurn} />
              </Card>
            )}
            {c.snap && (
              <>
                <Card title="Compliance" sub="checked by code">
                  <Opening snap={c.snap} />
                  <div className="en-sub-h">Guard</div>
                  <GuardList snap={c.snap} />
                </Card>
                <Card title="Pipeline">
                  <CodeState snap={c.snap} c={c} />
                  {c.snap.outcome && <p className="en-outcome">{c.snap.outcome}</p>}
                </Card>
              </>
            )}
          </div>
        </div>
        <footer className="en-foot">
          Hoplon &amp; Co · Nimra demo, milestone M1. Browser calls only; the calendar is simulated.
          {c.source === "sample" && " The sample call's words and numbers are synthetic."}
        </footer>
      </div>
    </div>
  );
}

function Stepper({ c }: { c: CallModel }) {
  const cur = trackIndex(c.snap?.stage);
  const ended = Boolean(c.snap?.ended);
  return (
    <ol className="en-steps" aria-label="Call stages">
      {TRACK.map((s, i) => {
        const st = cur < 0 ? "todo" : i < cur || ended ? "done" : i === cur ? "now" : "todo";
        return (
          <li key={s.id} data-state={st}>
            <span className="en-step-dot">{st === "done" ? <IconCheck /> : i + 1}</span>
            <span className="en-step-l">
              {s.label}
              {st === "now" && c.snap && <small>{stageName(c.snap.stage)}</small>}
              {s.id === "outcome" && ended && c.snap && <small>{shortStatus(c.snap.status)}</small>}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

function Kpis({ c }: { c: CallModel }) {
  const now = useNow(c, c.busy);
  const o = c.summary?.overall;
  const p50 = o?.totalMs.p50 ?? null;
  const p95 = o?.totalMs.p95 ?? null;
  return (
    <section className="en-kpis" aria-label="Call summary">
      <Kpi label="Typical reply" sub="p50 · target 0.9 s" value={sec(p50)} scale={p50} target={TARGET_MS} max={2000} />
      <Kpi label="Slow reply" sub="p95 · target 1.5 s" value={sec(p95)} scale={p95} target={SLOW_MS} max={2000} />
      <div className="en-kpi">
        <span className="en-kpi-l">Replies measured</span>
        <b className="en-kpi-v">{c.measured.length}</b>
        <span className="en-kpi-s">{c.turns.length - c.measured.length} scripted lines not counted</span>
      </div>
      <div className="en-kpi">
        <span className="en-kpi-l">Call length</span>
        <b className="en-kpi-v">{c.phase === "idle" ? "–" : clock(c.busy ? now : c.length)}</b>
        <span className="en-kpi-s">{c.snap ? shortStatus(c.snap.status) : "No call yet"}</span>
      </div>
    </section>
  );
}

function Kpi({ label, sub, value, scale, target, max }: { label: string; sub: string; value: string; scale: number | null; target: number; max: number }) {
  const ok = scale == null ? null : scale <= target;
  return (
    <div className="en-kpi">
      <span className="en-kpi-l">
        {label}
        {ok != null && <em data-tone={ok ? "good" : "crit"}>{ok ? "On target" : "Over target"}</em>}
      </span>
      <b className="en-kpi-v">{value}</b>
      <span className="en-kpi-s">{sub}</span>
      <span className="en-kpi-bar" aria-hidden="true">
        <i style={{ width: `${Math.min((scale ?? 0) / max, 1) * 100}%` }} data-tone={ok == null ? undefined : ok ? "good" : "crit"} />
        <span style={{ left: `${(target / max) * 100}%` }} />
      </span>
    </div>
  );
}

function Card({ title, sub, feature, children }: { title: string; sub?: string; feature?: boolean; children: React.ReactNode }) {
  return (
    <section className="en-card" data-feature={feature || undefined}>
      <div className="en-card-h">
        <h2>{title}</h2>
        {sub && <span className="en-card-sub">{sub}</span>}
      </div>
      {children}
    </section>
  );
}

function Conversation({ c, sel, onPick }: { c: CallModel; sel: number; onPick: (i: number) => void }) {
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (c.busy) end.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [c.turns.length, c.busy]);
  const first = c.lead.name.split(" ")[0] ?? "Lead";
  return (
    <section className="en-card en-conv">
      <div className="en-card-h">
        <h2>Conversation</h2>
        <span className="en-card-sub">{c.turns.length} replies</span>
        <div className="en-meters">
          <span>
            {first} <Meter who="lead" bars={7} />
          </span>
          <span>
            Nimra <Meter who="omar" bars={7} />
          </span>
        </div>
      </div>
      <div className="en-wave">
        <Waveform c={c} height={64} />
      </div>
      {c.turns.length === 0 && !c.busy && (
        <div className="en-empty">
          <h3>Start a call to see it here</h3>
          <p>
            Call {first} and talk to Nimra with your microphone, or hear the sample call first. Each reply shows how long
            the Lead waited, and where the time went.
          </p>
          <div className="en-empty-b">
            <CallButton c={c} className="en-btn en-navy" />
            <SampleButton c={c} className="en-btn en-outline" />
          </div>
        </div>
      )}
      <ol className="en-thread">
        {c.turns.map((t, i) => (
          <Exchange key={t.turn.turn} t={t} first={first} sel={i === sel} onPick={() => onPick(i)} />
        ))}
        {c.speaking?.who === "lead" && (
          <li className="en-x en-live">
            <span className="en-av" data-who="lead">
              {initials(c.lead.name)}
            </span>
            <p className="en-said">{c.source === "live" ? "You are speaking…" : `${first} is speaking…`}</p>
          </li>
        )}
      </ol>
      <div ref={end} />
    </section>
  );
}

function Exchange({ t, first, sel, onPick }: { t: TurnView; first: string; sel: boolean; onPick: () => void }) {
  const total = t.turn.totalMs;
  return (
    <li className="en-x" data-sel={sel || undefined} data-fresh={t.fresh || undefined}>
      {t.turn.lead_text && (
        <div className="en-line" data-who="lead">
          <span className="en-av" data-who="lead">
            {first.slice(0, 1)}
          </span>
          <div>
            <span className="en-who">
              {first} <time>{clock(t.leadAt ?? t.omarAt)}</time>
            </span>
            <p className="en-said">{t.turn.lead_text}</p>
          </div>
        </div>
      )}
      <button type="button" className="en-wait" onClick={onPick} data-tone={tone(total)} disabled={total == null}>
        {total != null ? (
          <>
            <PartsBar turn={t.turn} scaleMs={2000} animate={t.fresh} />
            <span>
              Waited <b>{ms(total)}</b>
              {t.heardMs != null && <> · heard ≈ {ms(t.heardMs)}</>}
            </span>
          </>
        ) : (
          <span>Scripted line · not measured</span>
        )}
      </button>
      <div className="en-line" data-who="omar">
        <span className="en-av" data-who="omar">
          O
        </span>
        <div>
          <span className="en-who">
            Nimra <time>{clock(t.omarAt)}</time>
            <span className="en-stage">{stageName(t.turn.stage)}</span>
            {t.turn.interrupted && <span className="en-cut">Interrupted</span>}
          </span>
          <p className="en-said">{t.turn.omar_text}</p>
          <StepChips steps={t.steps} tool={t.turn.toolTurn} />
        </div>
      </div>
    </li>
  );
}

function Response({ c, t }: { c: CallModel; t: TurnView | undefined }) {
  const med = medianParts(c.turns);
  if (!t || t.turn.totalMs == null)
    return <p className="muted">After Nimra&apos;s first measured reply, this card splits the wait into its parts.</p>;
  const total = t.turn.totalMs;
  return (
    <div className="en-resp">
      <div className="en-resp-top">
        <b>{sec(total)}</b>
        <span className="en-pill" data-tone={tone(total)}>
          {toneWord(tone(total))}
        </span>
      </div>
      <PartsBar turn={t.turn} scaleMs={2000} className="en-resp-bar" animate={t.fresh} />
      <PartList parts={partsOf(t.turn)} total={total} />
      {med.length > 0 && (
        <details className="en-det">
          <summary>Median over the call ({c.measured.length} replies)</summary>
          <PartList parts={med} totalLabel="Sum of medians" />
        </details>
      )}
      <p className="en-src">Measured on the voice worker, from the Lead&apos;s last word to Nimra&apos;s first audio. {num(c.summary?.overall.n)} replies.</p>
    </div>
  );
}

function LeadProfile({ c }: { c: CallModel }) {
  return (
    <div className="en-lead">
      <div className="en-lead-h">
        <span className="en-av en-av-lg" data-who="lead">
          {initials(c.lead.name)}
        </span>
        <div>
          <b>{c.lead.name}</b>
          <small>{c.lead.email}</small>
        </div>
      </div>
      <p className="en-quote">
        “<bdi>{c.lead.message}</bdi>”
      </p>
      <p className="muted">{c.lead.note}</p>
    </div>
  );
}
