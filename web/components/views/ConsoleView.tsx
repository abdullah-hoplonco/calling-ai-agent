"use client";

// Console: a clean product console. Recording on top, transcript with a delay on every reply,
// and a side panel for latency, call state and events.

import { useEffect, useRef, useState } from "react";

import { CallButton, CodeState, ConfigLine, ErrorNote, GuardList, MuteToggle, Opening, SampleButton, statusWord } from "@/components/blocks";
import { IconCheck } from "@/components/icons";
import { Meter, PartList, PartsBar, Waveform, medianParts, useNow, waveX } from "@/components/shared";
import { TRACK, trackIndex } from "@/lib/stages";
import type { CallModel, TurnView } from "@/lib/useCall";
import { SLOW_MS, TARGET_MS, clock, initials, ms, num, partsOf, stageName, stepWord, tone } from "@/lib/view";

type Tab = "lat" | "state" | "ev";

export function ConsoleView({ c, switcher }: { c: CallModel; switcher: React.ReactNode }) {
  const [tab, setTab] = useState<Tab>("lat");
  const [picked, setPicked] = useState<number | null>(null);
  useEffect(() => {
    if (c.busy) setPicked(null);
  }, [c.busy, c.turns.length]);
  const measuredIdx = c.turns.map((t, i) => (t.turn.totalMs != null ? i : -1)).filter((i) => i >= 0);
  const sel = picked ?? measuredIdx[measuredIdx.length - 1] ?? -1;

  return (
    <div className="cn">
      <aside className="cn-side">
        <div className="cn-ws">
          <span className="cn-logo" aria-hidden="true">
            h
          </span>
          <div>
            <b>Hoplon &amp; Co</b>
            <small>Omar · calling agent</small>
          </div>
        </div>
        <div className="cn-sec">Leads</div>
        <div className="cn-leads" role="radiogroup" aria-label="Who Omar calls">
          {c.leads.map((l) => (
            <button
              key={l.id}
              type="button"
              role="radio"
              aria-checked={l.id === c.leadId}
              className="cn-lead"
              data-on={l.id === c.leadId || undefined}
              disabled={c.busy}
              onClick={() => c.setLeadId(l.id)}
            >
              <span className="cn-av">{initials(l.name)}</span>
              <span>
                <b>{l.name}</b>
                <small>{l.note}</small>
              </span>
            </button>
          ))}
        </div>
        <label className="cn-old">
          <input type="checkbox" checked={c.old} disabled={c.busy} onChange={(e) => c.setOld(e.target.checked)} />
          <span>
            Old backlog Lead
            <small>Opens with “you reached out back in March”.</small>
          </span>
        </label>
        <div className="cn-grow" />
        <div className="cn-demo">
          <b>Demo mode</b>
          Browser calls only. The calendar is simulated.
        </div>
        <div className="cn-theme">
          <span>Theme</span>
          {switcher}
        </div>
      </aside>

      <div className="cn-main">
        <header className="cn-top">
          <div className="cn-crumb">
            Calls <span aria-hidden="true">/</span> <b>{c.lead.name}</b>
          </div>
          <span className="cn-status" data-phase={c.phase}>
            <i />
            {statusWord(c)}
          </span>
          {c.source === "sample" && <span className="cn-tag">Sample · synthetic data</span>}
          <div className="cn-sp" />
          <MuteToggle c={c} />
          <SampleButton c={c} className="cn-btn" label="Hear sample call" />
          <CallButton c={c} className="cn-btn cn-pri" />
        </header>
        <ErrorNote c={c} />

        <div className="cn-content">
          <div className="cn-col">
            <Header c={c} />
            <Player c={c} sel={sel} onPick={setPicked} />
            <Transcript c={c} sel={sel} onPick={setPicked} />
          </div>
          <section className="cn-card cn-panel">
            <div className="cn-tabs" role="tablist">
              {(
                [
                  ["lat", "Latency"],
                  ["state", "Call state"],
                  ["ev", "Events"],
                ] as const
              ).map(([id, label]) => (
                <button key={id} type="button" role="tab" aria-selected={tab === id} className="cn-tab" data-on={tab === id || undefined} onClick={() => setTab(id)}>
                  {label}
                </button>
              ))}
            </div>
            <div className="cn-pbody">
              {tab === "lat" && <Latency c={c} sel={sel} onPick={setPicked} />}
              {tab === "state" && (
                <>
                  <Block title="What the code holds">
                    <CodeState snap={c.snap} />
                  </Block>
                  <Block title="Legal opening">
                    <Opening snap={c.snap} />
                  </Block>
                  <Block title="Blocked before speech">
                    <GuardList snap={c.snap} />
                  </Block>
                  <Block title="Configuration">
                    <ConfigLine snap={c.snap} />
                    {!c.snap?.config && <p className="muted">Shown when the call starts.</p>}
                  </Block>
                </>
              )}
              {tab === "ev" && <Events c={c} />}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function Header({ c }: { c: CallModel }) {
  const now = useNow(c, c.busy);
  const o = c.summary?.overall;
  const p50 = o?.totalMs.p50 ?? null;
  const p95 = o?.totalMs.p95 ?? null;
  return (
    <section className="cn-card">
      <div className="cn-hdr">
        <span className="cn-av cn-av-lg">{initials(c.lead.name)}</span>
        <div className="cn-hdr-t">
          <h1>
            {c.lead.name}
            <span className="cn-tag">Website form</span>
          </h1>
          <p>
            “<bdi>{c.lead.message}</bdi>”
          </p>
        </div>
      </div>
      <div className="cn-stats">
        <Stat label="Duration" value={c.phase === "idle" ? "–" : clock(c.busy ? now : c.length)} />
        <Stat label="Replies measured" value={num(c.measured.length)} unit={`of ${c.turns.length} lines`} />
        <Stat label="Typical reply · p50" value={num(p50)} unit={p50 != null ? "ms" : undefined} badge={p50 == null ? undefined : p50 <= TARGET_MS ? "good" : "crit"} />
        <Stat label="Slow reply · p95" value={num(p95)} unit={p95 != null ? "ms" : undefined} badge={p95 == null ? undefined : p95 <= SLOW_MS ? "good" : "crit"} />
        <Stat label="Lines blocked" value={num(c.snap?.guardHits?.length ?? (c.snap ? 0 : null))} unit="by the guard" />
      </div>
    </section>
  );
}

function Stat({ label, value, unit, badge }: { label: string; value: string; unit?: string; badge?: "good" | "crit" }) {
  return (
    <div className="cn-stat">
      <span>{label}</span>
      <b>
        {value}
        {unit && <small>{unit}</small>}
        {badge && <em data-tone={badge}>{badge === "good" ? "Pass" : "Over"}</em>}
      </b>
    </div>
  );
}

function Player({ c, sel, onPick }: { c: CallModel; sel: number; onPick: (i: number) => void }) {
  const now = useNow(c, c.busy);
  const len = c.busy ? now : c.length;
  const cur = trackIndex(c.snap?.stage);
  return (
    <section className="cn-card cn-player">
      <div className="cn-prow">
        <div className="cn-ptime">
          <b>{clock(len)}</b>
          <span>{c.busy ? "recording" : c.phase === "ended" ? "call length" : "no call yet"}</span>
        </div>
        <div className="cn-meters">
          <span>
            <i className="cn-dot" data-who="lead" />
            {c.lead.name.split(" ")[0]}
            <Meter who="lead" bars={8} />
          </span>
          <span>
            <i className="cn-dot" data-who="omar" />
            Omar
            <Meter who="omar" bars={8} />
          </span>
        </div>
      </div>
      <div className="cn-wave">
        <Waveform c={c} height={92} />
        {c.busy && <span className="cn-wph" style={{ left: `${waveX(c, now, now) * 100}%` }} aria-hidden="true" />}
        {c.turns.map((t, i) =>
          t.turn.totalMs != null ? (
            <button
              key={i}
              type="button"
              className="cn-mark"
              data-tone={tone(t.turn.totalMs)}
              data-sel={i === sel || undefined}
              style={{ left: `${waveX(c, t.omarAt, now) * 100}%` }}
              onClick={() => onPick(i)}
              aria-label={`Turn ${t.turn.turn}: ${t.turn.totalMs} ms`}
            />
          ) : null,
        )}
        {c.turns.length === 0 && !c.busy && <p className="cn-wave-empty">The recording draws here as the call runs: the Lead above the line, Omar below.</p>}
      </div>
      <div className="cn-stages">
        {TRACK.map((s, i) => (
          <span key={s.id} data-state={cur < 0 ? "todo" : i < cur || c.snap?.ended ? "done" : i === cur ? "now" : "todo"}>
            {(i < cur || c.snap?.ended) && <IconCheck />}
            {s.label}
          </span>
        ))}
      </div>
    </section>
  );
}

function Transcript({ c, sel, onPick }: { c: CallModel; sel: number; onPick: (i: number) => void }) {
  const box = useRef<HTMLDivElement>(null);
  const first = c.lead.name.split(" ")[0];
  useEffect(() => {
    const el = box.current;
    if (el && c.busy) el.scrollTop = el.scrollHeight;
  }, [c.turns.length, c.speaking, c.busy]);
  let stage = "";
  const last = c.turns[c.turns.length - 1];
  const thinking = c.busy && !c.speaking && c.turns.length > 0 && last?.omarEnd != null;
  return (
    <section className="cn-card cn-tr">
      <div className="cn-trh">
        <h2>Transcript</h2>
        <span className="cn-tag">{c.turns.length} replies</span>
      </div>
      <div className="cn-tlist" ref={box} aria-live="polite">
        {c.turns.length === 0 && !c.busy && (
          <div className="cn-tr-empty">
            <p>
              <b>No call yet.</b> Call {first} to talk to Omar with your microphone, or hear the sample call. Each of
              Omar&apos;s replies shows how long the Lead waited for it.
            </p>
            <div>
              <CallButton c={c} className="cn-btn cn-pri" />
              <SampleButton c={c} className="cn-btn" />
            </div>
          </div>
        )}
        {c.turns.map((t, i) => {
          const div = t.turn.stage !== stage ? stageName(t.turn.stage) : null;
          stage = t.turn.stage;
          return (
            <div key={t.turn.turn}>
              {div && <div className="cn-div">{div}</div>}
              {t.turn.lead_text && (
                <Msg who="lead" name={first ?? "Lead"} at={t.leadAt ?? t.omarAt} text={t.turn.lead_text} />
              )}
              <Msg
                who="omar"
                name="Omar"
                at={t.omarAt}
                text={t.turn.omar_text}
                t={t}
                sel={i === sel}
                onClick={() => onPick(i)}
              />
              {t.steps.map((s) => (
                <div key={`${s.at}-${s.event}`} className="cn-sys" data-by={s.by}>
                  <i />
                  <span>
                    <b>{stepWord(s)}</b> · {s.by === "llm" ? "reported by LLM" : "set by code"}
                  </span>
                </div>
              ))}
            </div>
          );
        })}
        {c.speaking?.who === "lead" && <Typing name={c.source === "live" ? "You" : (first ?? "Lead")} who="lead" />}
        {thinking && <Typing name="Omar" who="omar" label="thinking" />}
        {c.phase === "connecting" && <Typing name="Omar" who="omar" label="joining the call" />}
      </div>
    </section>
  );
}

function Msg({ who, name, at, text, t, sel, onClick }: { who: "lead" | "omar"; name: string; at: number; text: string; t?: TurnView; sel?: boolean; onClick?: () => void }) {
  const total = t?.turn.totalMs;
  return (
    <div className="cn-msg" data-who={who} data-sel={sel || undefined} data-fresh={t?.fresh || undefined} onClick={onClick}>
      <span className="cn-ts">{clock(at)}</span>
      <span className="cn-av" data-who={who}>
        {who === "omar" ? "O" : initials(name)}
      </span>
      <div className="cn-msg-b">
        <div className="cn-who">
          {name}
          {t?.turn.toolTurn && <small>tool call</small>}
          {t?.turn.interrupted && <span className="cn-cut">Interrupted</span>}
        </div>
        <p>{text}</p>
      </div>
      {t && (
        <div className="cn-lp">
          {total != null ? (
            <>
              <button type="button" className="cn-badge" data-tone={tone(total)} onClick={onClick}>
                {ms(total)}
              </button>
              <PartsBar turn={t.turn} scaleMs={2000} className="cn-mini" animate={t.fresh} />
            </>
          ) : (
            <span className="cn-tag">Scripted</span>
          )}
        </div>
      )}
    </div>
  );
}

function Typing({ name, who, label = "speaking" }: { name: string; who: "lead" | "omar"; label?: string }) {
  return (
    <div className="cn-msg cn-typing" data-who={who}>
      <span className="cn-ts" />
      <span className="cn-av" data-who={who}>
        {who === "omar" ? "O" : initials(name) || "Y"}
      </span>
      <div className="cn-msg-b">
        <div className="cn-who">{name}</div>
        <p>
          <span className="cn-dots" aria-hidden="true">
            <i />
            <i />
            <i />
          </span>
          <span className="sr-only">{label}</span>
          <span className="cn-typing-l">{label}</span>
        </p>
      </div>
    </div>
  );
}

function Block({ title, sub, children }: { title: string; sub?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="cn-block">
      <div className="cn-bh">
        <h3>{title}</h3>
        {sub && <span>{sub}</span>}
      </div>
      {children}
    </div>
  );
}

function Latency({ c, sel, onPick }: { c: CallModel; sel: number; onPick: (i: number) => void }) {
  const o = c.summary?.overall;
  const p50 = o?.totalMs.p50 ?? null;
  const p95 = o?.totalMs.p95 ?? null;
  const t = sel >= 0 ? c.turns[sel] : undefined;
  const med = medianParts(c.turns);
  return (
    <>
      <div className="cn-block">
        <div className="cn-kpis">
          <Kpi label="Typical reply · p50" v={p50} target={TARGET_MS} />
          <Kpi label="Slow reply · p95" v={p95} target={SLOW_MS} />
        </div>
      </div>
      <Block title="Delay per reply" sub="dashed line: 0.9 s target">
        <Chart c={c} sel={sel} onPick={onPick} />
      </Block>
      <Block
        title={t ? `Turn ${t.turn.turn} breakdown` : "Reply breakdown"}
        sub={
          t?.turn.totalMs != null && p50 != null ? (
            <span className="cn-delta" data-tone={t.turn.totalMs <= p50 ? "good" : "warn"}>
              {t.turn.totalMs <= p50 ? "" : "+"}
              {Math.round(t.turn.totalMs - p50)} ms vs p50
            </span>
          ) : undefined
        }
      >
        {t?.turn.totalMs != null ? (
          <>
            <PartsBar turn={t.turn} className="cn-stack" animate={t.fresh} />
            <PartList parts={partsOf(t.turn)} total={t.turn.totalMs} />
            {t.heardMs != null && <p className="muted">≈ heard {t.heardMs} ms with network and audio buffer.</p>}
          </>
        ) : (
          <p className="muted">Pick a measured reply in the chart or the transcript.</p>
        )}
      </Block>
      <Block title="Where the time goes" sub={med.length ? `median of each part, ${c.measured.length} replies` : undefined}>
        {med.length ? (
          <>
            <PartsBar parts={med} className="cn-stack" />
            <PartList parts={med} totalLabel="Sum of medians" />
          </>
        ) : (
          <p className="muted">Appears after Omar&apos;s first measured reply.</p>
        )}
      </Block>
      {c.summary && Object.keys(c.summary.byStage).length > 0 && (
        <Block title="By call stage">
          <table className="cn-table">
            <thead>
              <tr>
                <th scope="col">Stage</th>
                <th scope="col">n</th>
                <th scope="col">p50</th>
                <th scope="col">p95</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(c.summary.byStage).map(([s, v]) => (
                <tr key={s}>
                  <th scope="row">{stageName(s)}</th>
                  <td>{v.n}</td>
                  <td data-tone={tone(v.totalMs.p50)}>{num(v.totalMs.p50)}</td>
                  <td>{num(v.totalMs.p95)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Block>
      )}
      {c.source === "sample" && <p className="cn-note">Sample call. Words, outcome and every number are synthetic. Voices are your browser&apos;s own.</p>}
    </>
  );
}

function Kpi({ label, v, target }: { label: string; v: number | null; target: number }) {
  const ok = v == null ? null : v <= target;
  return (
    <div className="cn-kpi">
      <span>{label}</span>
      <b>
        {num(v)}
        {v != null && <small>ms</small>}
      </b>
      <em>
        Target {target.toLocaleString("en-US")} ms
        {ok != null && <i data-tone={ok ? "good" : "crit"}>{ok ? "Pass" : "Over"}</i>}
      </em>
    </div>
  );
}

function Chart({ c, sel, onPick }: { c: CallModel; sel: number; onPick: (i: number) => void }) {
  const W = 340;
  const H = 132;
  const pad = 26;
  const max = 2000;
  const n = Math.max(c.turns.length, 8);
  const step = (W - pad) / n;
  const bw = Math.min(22, step * 0.6);
  const y = (v: number) => H - 18 - (Math.min(v, max) / max) * (H - 28);
  return (
    <svg className="cn-chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Delay of each reply in milliseconds">
      {[0, 500, 1000, 1500, 2000].map((m) => (
        <g key={m}>
          <line x1={pad} x2={W} y1={y(m)} y2={y(m)} className="cn-grid" />
          <text x={0} y={y(m) + 3.5} className="cn-axis">
            {m ? `${m / 1000}s` : "0"}
          </text>
        </g>
      ))}
      <line x1={pad} x2={W} y1={y(TARGET_MS)} y2={y(TARGET_MS)} className="cn-target" />
      {c.turns.map((t, i) => {
        const cx = pad + step * i + step / 2;
        if (t.turn.totalMs == null)
          return <line key={i} x1={cx - 6} x2={cx + 6} y1={y(0) - 1} y2={y(0) - 1} className="cn-scr" />;
        let acc = 0;
        return (
          <g key={i} className="cn-bar" data-dim={(sel >= 0 && sel !== i) || undefined} onClick={() => onPick(i)}>
            {partsOf(t.turn).map((p) => {
              const r = <rect key={p.key} x={cx - bw / 2} y={y(acc + p.ms)} width={bw} height={Math.max(0, y(acc) - y(acc + p.ms))} className={`p-${p.cls}`} />;
              acc += p.ms;
              return r;
            })}
            <rect x={cx - step / 2} y={0} width={step} height={H} fill="transparent" />
          </g>
        );
      })}
      {c.turns.map((t, i) => (
        <text key={`t${i}`} x={pad + step * i + step / 2} y={H - 3} textAnchor="middle" className="cn-axis" data-sel={i === sel || undefined}>
          {t.turn.turn}
        </text>
      ))}
    </svg>
  );
}

function Events({ c }: { c: CallModel }) {
  const all = c.turns.flatMap((t) => t.steps.map((s) => ({ s, at: t.omarAt, n: t.turn.turn })));
  if (!all.length) return <p className="muted">Events the code records, and the ones the LLM reports, appear here.</p>;
  return (
    <ul className="cn-evl">
      {all.map(({ s, at, n }) => (
        <li key={`${s.at}-${s.event}`} data-by={s.by}>
          <span className="cn-ts">{clock(at)}</span>
          <i />
          <span>
            {stepWord(s)}
            <small>
              Turn {n} · {s.by === "llm" ? "reported by LLM" : "set by code"}
            </small>
          </span>
        </li>
      ))}
    </ul>
  );
}

