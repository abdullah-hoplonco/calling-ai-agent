"use client";

// Console: the Hoplon & Co product console. A black call deck (the Lead, the recording, the stage
// track and the measured waits) over a white transcript, with a side panel for latency, call state
// and events. Black, white and one lime, as on hoplonco.com.

import { useEffect, useRef, useState } from "react";

import { CallButton, CodeState, ConfigLine, ErrorNote, GuardList, LlmSwitch, MuteToggle, VoiceSwitch, Opening, SampleButton, statusWord } from "@/components/blocks";
import { HoplonLogo } from "@/components/HoplonLogo";
import { IconCheck, IconChevron } from "@/components/icons";
import { Meter, PartList, PartsBar, Waveform, medianParts, useNow, waveX } from "@/components/shared";
import { LLM_CHOICES } from "@/lib/leads";
import { TRACK, shortStatus, trackIndex } from "@/lib/stages";
import type { CallModel, TurnView } from "@/lib/useCall";
import { SLOW_MS, TARGET_MS, clock, initials, ms, num, partsOf, stageName, stepWord, tone, toneWord, type Tone } from "@/lib/view";
import { VOICES } from "@/lib/voices";

const TABS = [
  ["lat", "Latency"],
  ["state", "Call state"],
  ["ev", "Events"],
] as const;
type Tab = (typeof TABS)[number][0];

// The sample is always Nimra; a live call takes the name of the picked voice.
function agentOf(c: CallModel): string {
  if (c.source === "sample") return "Nimra";
  return VOICES.find((v) => v.id === c.voiceId)?.agent ?? "Nimra";
}

// The verdict as a shape as well as a colour: circle within 0.9 s, diamond over, triangle over 1.5 s.
function Vx({ t }: { t: Tone | undefined }) {
  return <i className="cn-vx" data-tone={t} aria-hidden="true" />;
}

export function ConsoleView({ c, switcher }: { c: CallModel; switcher: React.ReactNode }) {
  const [tab, setTab] = useState<Tab>("lat");
  const [picked, setPicked] = useState<number | null>(null);
  useEffect(() => {
    if (c.busy) setPicked(null);
  }, [c.busy, c.turns.length]);
  const measuredIdx = c.turns.map((t, i) => (t.turn.totalMs != null ? i : -1)).filter((i) => i >= 0);
  const sel = picked ?? measuredIdx[measuredIdx.length - 1] ?? -1;
  const agent = agentOf(c);
  const llm = LLM_CHOICES.find((o) => o.id === c.llm)?.label ?? "Auto";
  const voice = VOICES.find((v) => v.id === c.voiceId)?.name;

  // Arrow keys move between tabs (APG tabs pattern); Tab leaves the tab list.
  const onTabKey = (e: React.KeyboardEvent) => {
    const i = TABS.findIndex(([id]) => id === tab);
    const n = e.key === "ArrowRight" ? (i + 1) % TABS.length : e.key === "ArrowLeft" ? (i + TABS.length - 1) % TABS.length : e.key === "Home" ? 0 : e.key === "End" ? TABS.length - 1 : -1;
    if (n < 0) return;
    e.preventDefault();
    const next = TABS[n]![0];
    setTab(next);
    document.getElementById(`cn-tab-${next}`)?.focus();
  };

  return (
    <div className="cn">
      <aside className="cn-side" aria-label="Call setup">
        <div className="cn-ws">
          <HoplonLogo />
          <small>{agent} · AI calling agent</small>
        </div>
        <fieldset className="cn-leads" disabled={c.busy}>
          <legend className="cn-sec">Leads</legend>
          <div className="cn-leads-l">
            {c.leads.map((l) => (
              <label key={l.id} className="cn-lead" data-on={l.id === c.leadId || undefined}>
                <input type="radio" name="cn-lead" value={l.id} checked={l.id === c.leadId} onChange={() => c.setLeadId(l.id)} />
                <span className="cn-av" aria-hidden="true">
                  {initials(l.name)}
                </span>
                <span>
                  <b>{l.label ?? l.name}</b>
                  <small>{l.note}</small>
                </span>
              </label>
            ))}
          </div>
        </fieldset>
        <details className="cn-set">
          <summary>
            <IconChevron />
            <span>
              Call settings
              <small>
                {llm}
                {voice ? ` · ${voice}` : ""}
                {c.old ? " · old Lead" : ""}
              </small>
            </span>
          </summary>
          <div className="cn-set-b">
            <label className="cn-old">
              <input type="checkbox" checked={c.old} disabled={c.busy} onChange={(e) => c.setOld(e.target.checked)} />
              <span>
                Old backlog Lead
                <small>Opens with “you reached out back in March”.</small>
              </span>
            </label>
            <label className="cn-old">
              <input type="checkbox" checked={c.hindi} disabled={c.busy} onChange={(e) => c.setHindi(e.target.checked)} />
              <span>
                English + Hindi
                <small>The Lead can speak Hindi; the agent answers in Hindi.</small>
              </span>
            </label>
            <LlmSwitch c={c} />
            <VoiceSwitch c={c} />
          </div>
        </details>
        <div className="cn-grow" />
        <p className="cn-demo">
          <b>Demo mode.</b> Browser calls only. The calendar is simulated.
        </p>
        <div className="cn-theme">
          <span>Theme</span>
          {switcher}
        </div>
      </aside>

      <main className="cn-main">
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
          <CallButton c={c} className="cn-btn" />
          <SampleButton c={c} className="cn-btn cn-pri" />
        </header>
        <ErrorNote c={c} />

        <div className="cn-content">
          <div className="cn-col">
            <Deck c={c} sel={sel} onPick={setPicked} agent={agent} />
            <Transcript c={c} sel={sel} onPick={setPicked} agent={agent} />
          </div>
          <section className="cn-card cn-panel" aria-label="Call details">
            <div className="cn-tabs" role="tablist" aria-label="Call details" onKeyDown={onTabKey}>
              {TABS.map(([id, label]) => (
                <button
                  key={id}
                  id={`cn-tab-${id}`}
                  type="button"
                  role="tab"
                  aria-selected={tab === id}
                  aria-controls="cn-tabpanel"
                  tabIndex={tab === id ? 0 : -1}
                  className="cn-tab"
                  data-on={tab === id || undefined}
                  onClick={() => setTab(id)}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="cn-pbody" id="cn-tabpanel" role="tabpanel" aria-labelledby={`cn-tab-${tab}`} tabIndex={0}>
              {tab === "lat" && <Latency c={c} sel={sel} onPick={setPicked} agent={agent} />}
              {tab === "state" && (
                <>
                  <Block title="What the code holds">
                    <CodeState snap={c.snap} c={c} />
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
      </main>
    </div>
  );
}

// The black call deck: who is called, the recording, the stage track and the measured waits.
function Deck({ c, sel, onPick, agent }: { c: CallModel; sel: number; onPick: (i: number) => void; agent: string }) {
  const now = useNow(c, c.busy);
  const len = c.busy ? now : c.length;
  const cur = trackIndex(c.snap?.stage);
  const first = c.lead.name.split(" ")[0];
  const o = c.summary?.overall;
  const p50 = o?.totalMs.p50 ?? null;
  const p95 = o?.totalMs.p95 ?? null;
  return (
    <section className="cn-deck" aria-label="Call">
      <div className="cn-hdr">
        <span className="cn-av cn-av-lg" aria-hidden="true">
          {initials(c.lead.name)}
        </span>
        <div className="cn-hdr-t">
          <h1>
            {c.lead.name}
            <span className="cn-chip">Website form</span>
          </h1>
          <p>
            “<bdi>{c.lead.message}</bdi>”
          </p>
        </div>
        <Outcome c={c} />
      </div>

      <div className="cn-rec">
        <div className="cn-prow">
          <div className="cn-ptime">
            {c.busy && <i className="cn-live" aria-hidden="true" />}
            <b>{clock(len)}</b>
            <span>{c.busy ? "recording" : c.phase === "ended" ? "call length" : "no call yet"}</span>
          </div>
          <div className="cn-meters">
            <span>
              <i className="cn-dot" data-who="lead" />
              {first}
              <Meter who="lead" bars={8} />
            </span>
            <span>
              <i className="cn-dot" data-who="omar" />
              {agent}
              <Meter who="omar" bars={8} />
            </span>
          </div>
        </div>
        <div className="cn-wave">
          <Waveform c={c} height={96} />
          {c.busy && <span className="cn-wph" style={{ left: `${waveX(c, now, now) * 100}%` }} aria-hidden="true" />}
          {c.turns.map((t, i) =>
            t.turn.totalMs != null ? (
              <button
                key={i}
                type="button"
                className="cn-mark"
                data-sel={i === sel || undefined}
                style={{ left: `${waveX(c, t.omarAt, now) * 100}%` }}
                onClick={() => onPick(i)}
                aria-pressed={i === sel}
                aria-label={`Turn ${t.turn.turn}: ${t.turn.totalMs} ms, ${toneWord(tone(t.turn.totalMs)).toLowerCase()}`}
                title={`Turn ${t.turn.turn} · ${ms(t.turn.totalMs)}`}
              >
                <Vx t={tone(t.turn.totalMs)} />
              </button>
            ) : null,
          )}
          {c.turns.length === 0 && !c.busy && (
            <p className="cn-wave-empty">
              The recording draws here as the call runs: {first} above the line, {agent} below.
            </p>
          )}
        </div>
        <ol className="cn-stages" aria-label="Call stages">
          {TRACK.map((s, i) => {
            const state = cur < 0 ? "todo" : i < cur || c.snap?.ended ? "done" : i === cur ? "now" : "todo";
            return (
              <li key={s.id} data-state={state} aria-current={state === "now" ? "step" : undefined}>
                {state === "done" && <IconCheck />}
                {s.label}
              </li>
            );
          })}
        </ol>
      </div>

      <dl className="cn-stats">
        <Stat label="Duration" value={c.phase === "idle" ? "–" : clock(len)} />
        <Stat label="Replies measured" value={num(c.measured.length)} unit={`of ${c.turns.length} lines`} />
        <Stat label="Typical reply · p50" value={num(p50)} unit={p50 != null ? "ms" : undefined} badge={p50 == null ? undefined : p50 <= TARGET_MS ? "good" : "crit"} />
        <Stat label="Slow reply · p95" value={num(p95)} unit={p95 != null ? "ms" : undefined} badge={p95 == null ? undefined : p95 <= SLOW_MS ? "good" : "crit"} />
        <Stat label="Lines blocked" value={num(c.snap?.guardHits?.length ?? (c.snap ? 0 : null))} unit="by the guard" />
      </dl>
    </section>
  );
}

// Right of the Lead: the stage while the call runs, the outcome when it ends.
function Outcome({ c }: { c: CallModel }) {
  const snap = c.snap;
  if (snap?.ended) {
    const word = shortStatus(snap.status);
    const won = /booked|Qualified|link sent/i.test(word);
    return (
      <div className="cn-outcome" data-won={won || undefined}>
        <span>Outcome</span>
        <b>
          {won && <IconCheck />}
          {word}
        </b>
      </div>
    );
  }
  if (c.busy && snap)
    return (
      <div className="cn-outcome" data-live>
        <span>Stage now</span>
        <b>
          <i aria-hidden="true" />
          {stageName(snap.stage)}
        </b>
      </div>
    );
  return null;
}

function Stat({ label, value, unit, badge }: { label: string; value: string; unit?: string; badge?: "good" | "crit" }) {
  return (
    <div className="cn-stat">
      <dt>{label}</dt>
      <dd>
        <b>{value}</b>
        {unit && <small>{unit}</small>}
        {badge && <em data-tone={badge}>{badge === "good" ? "Pass" : "Over"}</em>}
      </dd>
    </div>
  );
}

function Transcript({ c, sel, onPick, agent }: { c: CallModel; sel: number; onPick: (i: number) => void; agent: string }) {
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
    <section className="cn-card cn-tr" aria-labelledby="cn-tr-h">
      <div className="cn-trh">
        <h2 id="cn-tr-h">Transcript</h2>
        <span className="cn-tag">
          {c.turns.length} {c.turns.length === 1 ? "reply" : "replies"}
        </span>
        <span className="cn-trh-k">
          <span>
            <Vx t="good" />
            within 0.9 s
          </span>
          <span>
            <Vx t="warn" />
            over 0.9 s
          </span>
          <span>
            <Vx t="crit" />
            over 1.5 s
          </span>
        </span>
      </div>
      <div className="cn-tlist" ref={box} aria-live="polite">
        {c.turns.length === 0 && !c.busy && (
          <div className="cn-tr-empty">
            <h3>Hear a full call in about two minutes</h3>
            <ul>
              <li>
                <b>Listen.</b> {agent} calls {first}, gives the information asked for and tries to book a Discovery Call.
              </li>
              <li>
                <b>Watch the wait.</b> Each of {agent}&apos;s replies shows how long the Lead waited, judged against 0.9 s.
              </li>
              <li>
                <b>Open any reply.</b> The side panel splits that wait into its six parts.
              </li>
            </ul>
            <div>
              <SampleButton c={c} className="cn-btn cn-pri" />
            </div>
            <small>The sample is synthetic. To talk to {agent} yourself, use Call {first} at the top.</small>
          </div>
        )}
        {c.turns.map((t, i) => {
          const div = t.turn.stage !== stage ? stageName(t.turn.stage) : null;
          stage = t.turn.stage;
          return (
            <div key={t.turn.turn}>
              {div && <div className="cn-div">{div}</div>}
              {t.turn.lead_text && <Msg who="lead" name={first ?? "Lead"} at={t.leadAt ?? t.omarAt} text={t.turn.lead_text} />}
              <Msg who="omar" name={agent} at={t.omarAt} text={t.turn.omar_text} t={t} sel={i === sel} onClick={() => onPick(i)} />
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
        {thinking && <Typing name={agent} who="omar" label="thinking" />}
        {c.phase === "connecting" && <Typing name={agent} who="omar" label="joining the call" />}
      </div>
    </section>
  );
}

function Msg({ who, name, at, text, t, sel, onClick }: { who: "lead" | "omar"; name: string; at: number; text: string; t?: TurnView; sel?: boolean; onClick?: () => void }) {
  const total = t?.turn.totalMs;
  return (
    <div className="cn-msg" data-who={who} data-sel={sel || undefined} data-fresh={t?.fresh || undefined} onClick={onClick}>
      <span className="cn-ts">{clock(at)}</span>
      <span className="cn-av" data-who={who} aria-hidden="true">
        {initials(name) || "N"}
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
              <button type="button" className="cn-badge" data-tone={tone(total)} onClick={onClick} aria-pressed={sel} aria-label={`Turn ${t.turn.turn}: waited ${ms(total)}, ${toneWord(tone(total)).toLowerCase()}. Show the breakdown.`}>
                <Vx t={tone(total)} />
                {ms(total)}
              </button>
              <PartsBar turn={t.turn} scaleMs={2000} className="cn-mini" animate={t.fresh} />
            </>
          ) : (
            <span className="cn-tag" title="Said from a script, so there is no LLM wait to measure">
              Scripted
            </span>
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
      <span className="cn-av" data-who={who} aria-hidden="true">
        {initials(name) || "Y"}
      </span>
      <div className="cn-msg-b">
        <div className="cn-who">{name}</div>
        <p>
          <span className="cn-dots" aria-hidden="true">
            <i />
            <i />
            <i />
          </span>
          <span className="cn-typing-l">{label}</span>
        </p>
      </div>
    </div>
  );
}

function Block({ title, sub, children }: { title: React.ReactNode; sub?: React.ReactNode; children: React.ReactNode }) {
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

function Latency({ c, sel, onPick, agent }: { c: CallModel; sel: number; onPick: (i: number) => void; agent: string }) {
  const p50 = c.summary?.overall.totalMs.p50 ?? null;
  const t = sel >= 0 ? c.turns[sel] : undefined;
  const total = t?.turn.totalMs ?? null;
  const med = medianParts(c.turns);
  return (
    <>
      <Block title="Delay per reply" sub={c.measured.length ? "Pick a bar to open it" : undefined}>
        <Chart c={c} sel={sel} onPick={onPick} />
        <div className="cn-key" aria-hidden="true">
          <span data-line="good">0.9 s target</span>
          <span data-line="crit">1.5 s slow</span>
        </div>
      </Block>
      <Block
        title={t && total != null ? `Turn ${t.turn.turn}` : "Reply breakdown"}
        sub={
          total != null && p50 != null ? (
            <span className="cn-delta">
              {total <= p50 ? "−" : "+"}
              {Math.abs(Math.round(total - p50))} ms vs p50
            </span>
          ) : undefined
        }
      >
        {t && total != null ? (
          <>
            <div className="cn-read">
              <b>
                {num(total)}
                <small>ms</small>
              </b>
              <em data-tone={tone(total)}>
                <Vx t={tone(total)} />
                {toneWord(tone(total))}
              </em>
            </div>
            <p className="cn-read-q">
              “<bdi>{t.turn.omar_text}</bdi>”
            </p>
            <PartsBar turn={t.turn} className="cn-stack" animate={t.fresh} />
            <PartList parts={partsOf(t.turn)} total={total} />
            {t.heardMs != null && <p className="muted cn-heard">≈ heard {num(t.heardMs)} ms with network and audio buffer.</p>}
          </>
        ) : (
          <p className="muted">Pick a measured reply in the chart or the transcript.</p>
        )}
      </Block>
      <Block title="Where the time goes" sub={med.length ? `Median of each part, ${c.measured.length} replies` : undefined}>
        {med.length ? (
          <>
            <PartsBar parts={med} className="cn-stack" />
            <PartList parts={med} totalLabel="Sum of medians" />
          </>
        ) : (
          <p className="muted">Appears after {agent}&apos;s first measured reply.</p>
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
                  <td data-tone={tone(v.totalMs.p50)}>
                    <Vx t={tone(v.totalMs.p50)} />
                    {num(v.totalMs.p50)}
                  </td>
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

function Chart({ c, sel, onPick }: { c: CallModel; sel: number; onPick: (i: number) => void }) {
  const W = 340;
  const H = 150;
  const pad = 26;
  const top = 16;
  const max = 2000;
  const n = Math.max(c.turns.length, 8);
  const step = (W - pad) / n;
  const bw = Math.min(20, step * 0.56);
  const y = (v: number) => H - 18 - (Math.min(v, max) / max) * (H - 18 - top);
  return (
    <svg className="cn-chart" viewBox={`0 0 ${W} ${H}`} role="group" aria-label="Delay of each reply in milliseconds">
      {[0, 500, 1000, 1500, 2000].map((m) => (
        <g key={m}>
          <line x1={pad} x2={W} y1={y(m)} y2={y(m)} className="cn-grid" />
          <text x={0} y={y(m) + 3.5} className="cn-axis">
            {m ? `${m / 1000}s` : "0"}
          </text>
        </g>
      ))}
      <line x1={pad} x2={W} y1={y(TARGET_MS)} y2={y(TARGET_MS)} className="cn-target" />
      <line x1={pad} x2={W} y1={y(SLOW_MS)} y2={y(SLOW_MS)} className="cn-slow" />
      {c.turns.map((t, i) => {
        const cx = pad + step * i + step / 2;
        const total = t.turn.totalMs;
        if (total == null) return <line key={i} x1={cx - 6} x2={cx + 6} y1={y(0) - 1} y2={y(0) - 1} className="cn-scr" />;
        let acc = 0;
        const on = i === sel;
        return (
          <g
            key={i}
            className="cn-bar"
            data-dim={(sel >= 0 && !on) || undefined}
            role="button"
            tabIndex={0}
            aria-label={`Turn ${t.turn.turn}: ${total} ms`}
            aria-pressed={on}
            onClick={() => onPick(i)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onPick(i);
              }
            }}
          >
            <title>{`Turn ${t.turn.turn} · ${ms(total)}`}</title>
            <rect x={cx - step / 2} y={0} width={step} height={H} className="cn-hit" />
            {partsOf(t.turn).map((p) => {
              const r = <rect key={p.key} x={cx - bw / 2} y={y(acc + p.ms)} width={bw} height={Math.max(0, y(acc) - y(acc + p.ms))} className={`p-${p.cls}`} />;
              acc += p.ms;
              return r;
            })}
            {on && (
              <text x={cx} y={y(total) - 5} textAnchor="middle" className="cn-val">
                {num(total)}
              </text>
            )}
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
    <>
      <div className="cn-key cn-ev-key" aria-hidden="true">
        <span data-by="code">set by code</span>
        <span data-by="llm">reported by LLM</span>
      </div>
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
    </>
  );
}
