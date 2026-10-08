"use client";

import { IconAlert, IconMute, IconPhone, IconPhoneOff, IconSpeaker, IconStop } from "@/components/icons";
import { LLM_CHOICES, OLD_LEAD_MONTH } from "@/lib/leads";
import { compare } from "@/lib/llmHistory";
import { ENGINE_LABEL, VOICES, type VoiceEngine } from "@/lib/voices";
import type { CallSnapshot, Step } from "@/lib/types";
import type { CallModel } from "@/lib/useCall";
import { initials, ruleWord, stageName, stepWord } from "@/lib/view";
import { shortStatus } from "@/lib/stages";

export function LeadPicker({ c, compact = false }: { c: CallModel; compact?: boolean }) {
  return (
    <fieldset className="lp-set" disabled={c.busy}>
      <legend className="lp-legend">Who Nimra calls</legend>
      {c.leads.map((l) => (
        <label key={l.id} className="lp-opt" data-on={l.id === c.leadId || undefined}>
          <input type="radio" name="lead" value={l.id} checked={l.id === c.leadId} onChange={() => c.setLeadId(l.id)} />
          <span className="lp-av" aria-hidden="true">
            {initials(l.name)}
          </span>
          <span className="lp-body">
            <span className="lp-name">{l.label ?? l.name}</span>
            {!compact && (
              <span className="lp-msg">
                “<bdi>{l.message}</bdi>”
              </span>
            )}
            <span className="lp-note">{l.note}</span>
          </span>
        </label>
      ))}
      <label className="lp-old">
        <input type="checkbox" checked={c.old} onChange={(e) => c.setOld(e.target.checked)} />
        <span>
          Old backlog Lead
          <small>Nimra opens with “you reached out back in {OLD_LEAD_MONTH}”.</small>
        </span>
      </label>
      <label className="lp-old">
        <input type="checkbox" checked={c.hindi} disabled={c.busy} onChange={(e) => c.setHindi(e.target.checked)} />
        <span>
          English + Hindi
          <small>The Lead can speak Hindi; Nimra answers in Hindi.</small>
        </span>
      </label>
      <LlmSwitch c={c} />
      <VoiceSwitch c={c} />
    </fieldset>
  );
}

// Which Cartesia voice speaks on the next call. Top picks and emotive voices are marked.
export function VoiceSwitch({ c }: { c: CallModel }) {
  return (
    <div className="voice-switch">
      <span className="llm-legend" id="voice-legend">
        Voice
      </span>
      <div className="voice-list" role="radiogroup" aria-labelledby="voice-legend">
        {(["elevenlabs", "cartesia"] as VoiceEngine[]).map((engine) => (
          <div key={engine} className="voice-group">
            <small className="voice-engine">{ENGINE_LABEL[engine]}</small>
            {VOICES.filter((v) => v.engine === engine).map((v) => (
              <label key={v.id} data-on={v.id === c.voiceId || undefined} data-top={v.top || v.emotive || undefined}>
                <input
                  type="radio"
                  name="voice"
                  value={v.id}
                  checked={v.id === c.voiceId}
                  disabled={c.busy}
                  onChange={() => c.setVoiceId(v.id)}
                />
                <b>{v.name}</b>
                <span>{v.desc}</span>
                {v.top && <em>default</em>}
                {v.emotive && <em>most expressive</em>}
                {v.paid && <em>paid plan</em>}
              </label>
            ))}
          </div>
        ))}
      </div>
      {VOICES.find((v) => v.id === c.voiceId)?.engine === "elevenlabs" && (
        <label className="voice-stability">
          <span>
            Emotion <b>{c.stability.toFixed(2)}</b>
            <small>{c.stability < 0.2 ? "wild" : c.stability < 0.45 ? "lively" : c.stability < 0.7 ? "natural" : "steady"}</small>
          </span>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={c.stability}
            disabled={c.busy}
            onChange={(e) => c.setStability(Number(e.target.value))}
            aria-label="ElevenLabs stability: lower is more emotion"
          />
          <small className="llm-note">Stability: lower = more emotion. Applies from the next call.</small>
        </label>
      )}
      <small className="llm-note">
        Female voices introduce themselves as Nimra, male voices as Hamza.
      </small>
    </div>
  );
}

// Which LLM speaks on the next call. Sent with the call; the worker builds it for that call.
export function LlmSwitch({ c }: { c: CallModel }) {
  const current = LLM_CHOICES.find((o) => o.id === c.llm) ?? LLM_CHOICES[0]!;
  return (
    <div className="llm-switch">
      <span className="llm-legend" id="llm-legend">
        LLM
      </span>
      <div className="llm-seg" role="radiogroup" aria-labelledby="llm-legend">
        {LLM_CHOICES.map((o) => (
          <label key={o.id} data-on={o.id === c.llm || undefined}>
            <input
              type="radio"
              name="llm"
              value={o.id}
              checked={o.id === c.llm}
              disabled={c.busy}
              onChange={() => c.setLlm(o.id)}
            />
            {o.label}
          </label>
        ))}
      </div>
      <small className="llm-note">{current.note}</small>
      {c.llm !== "groq" && (
        <div className="llm-key">
          <label>
            <span>DeepSeek API key</span>
            <input
              type="password"
              autoComplete="off"
              spellCheck={false}
              placeholder="sk-…"
              value={c.deepseekKey}
              disabled={c.busy}
              onChange={(e) => c.setDeepseekKey(e.target.value)}
            />
          </label>
          <label className="llm-remember">
            <input type="checkbox" checked={c.rememberKey} disabled={c.busy} onChange={(e) => c.setRememberKey(e.target.checked)} />
            Remember in this browser
          </label>
          <small className="llm-note">
            Sent straight to Nimra for one call and checked with DeepSeek. Not stored on any server.
            {!c.deepseekKey && " Optional: without one, the call uses the server's DeepSeek key."}
          </small>
          {c.keyStatus && (
            <small className="llm-status" data-ok={c.keyStatus.ok || undefined}>
              {c.keyStatus.text}
            </small>
          )}
        </div>
      )}
    </div>
  );
}

const usd = (v: number) => (v === 0 ? "$0" : v < 0.01 ? `$${v.toFixed(5)}` : `$${v.toFixed(4)}`);
const ms = (v: number | null) => (v == null ? "–" : `${Math.round(v)} ms`);
const providerName = (p: string) => (p === "deepseek" ? "DeepSeek" : p === "groq" ? "Groq" : p);

// This call's LLM requests, tokens and cost, live from the agent (cache miss assumed).
export function LlmUsage({ snap }: { snap: CallSnapshot | null }) {
  const u = snap?.llmUsage;
  if (!u) return null;
  const rows = Object.entries(u.byProvider);
  return (
    <div className="llm-usage">
      <p className="llm-usage-head">
        <b>LLM this call</b> {u.label}
      </p>
      {rows.length === 0 ? (
        <p className="muted">No LLM request yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th scope="col">Provider</th>
              <th scope="col">Requests</th>
              <th scope="col">Tokens in / out</th>
              <th scope="col">First token p50</th>
              <th scope="col">Cost</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([p, v]) => {
              const s = [...v.ttftMs].sort((a, b) => a - b);
              return (
                <tr key={p}>
                  <th scope="row">{providerName(p)}</th>
                  <td>{v.requests}</td>
                  <td>
                    {v.promptTokens.toLocaleString()} / {v.completionTokens.toLocaleString()}
                  </td>
                  <td>{ms(s.length ? s[Math.ceil(s.length / 2) - 1]! : null)}</td>
                  <td>{p === "groq" ? "free tier" : usd(v.costUsd)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
      <small className="muted">
        Total {usd(u.totalCostUsd)}. {u.pricing}.
      </small>
    </div>
  );
}

// Groq vs DeepSeek over all your calls in this browser.
export function LlmCompare({ c }: { c: CallModel }) {
  const stats = compare(c.history);
  if (!stats.length) return <p className="muted">Finish a live call to start the Groq vs DeepSeek comparison.</p>;
  return (
    <div className="llm-compare">
      <p className="llm-usage-head">
        <b>Groq vs DeepSeek</b> all your calls in this browser
      </p>
      <table>
        <thead>
          <tr>
            <th scope="col">LLM</th>
            <th scope="col">Replies</th>
            <th scope="col">First token p50 / p95</th>
            <th scope="col">Total p50 / p95</th>
            <th scope="col">Cost per reply</th>
          </tr>
        </thead>
        <tbody>
          {stats.map((s) => (
            <tr key={s.provider}>
              <th scope="row">{providerName(s.provider)}</th>
              <td>{s.replies}</td>
              <td>
                {ms(s.llmP50)} / {ms(s.llmP95)}
              </td>
              <td>
                {ms(s.totalP50)} / {ms(s.totalP95)}
              </td>
              <td>{s.provider === "groq" ? "free tier" : usd(s.costPerReply)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <button type="button" className="llm-clear" onClick={c.resetHistory}>
        Clear comparison
      </button>
    </div>
  );
}

export function CallButton({ c, className = "" }: { c: CallModel; className?: string }) {
  const first = c.lead.name.split(" ")[0];
  if (c.phase === "live" || c.phase === "connecting")
    return (
      <button type="button" className={`b-end ${className}`} onClick={c.hangUp}>
        <IconPhoneOff />
        {c.phase === "connecting" ? "Cancel" : "End call"}
      </button>
    );
  if (c.phase === "sample")
    return (
      <button type="button" className={`b-end ${className}`} onClick={c.endSample}>
        <IconStop />
        Stop sample
      </button>
    );
  return (
    <button type="button" className={`b-call ${className}`} onClick={c.call}>
      <IconPhone />
      Call {first}
    </button>
  );
}

export function SampleButton({ c, className = "", label = "Hear a sample call" }: { c: CallModel; className?: string; label?: string }) {
  if (c.busy) return null;
  return (
    <button type="button" className={`b-sample ${className}`} onClick={() => c.hearSample()}>
      <IconSpeaker />
      {c.source === "sample" && c.phase === "ended" ? "Hear it again" : label}
    </button>
  );
}

export function MuteToggle({ c }: { c: CallModel }) {
  return (
    <button
      type="button"
      className="b-mute"
      aria-pressed={c.muted}
      onClick={() => c.setMuted(!c.muted)}
      title={c.muted ? "Sample plays silent. Click to hear voices." : "Sample plays with voices. Click to mute."}
    >
      {c.muted ? <IconMute /> : <IconSpeaker />}
      <span className="sr-only">{c.muted ? "Sample voices off" : "Sample voices on"}</span>
    </button>
  );
}

export function ErrorNote({ c }: { c: CallModel }) {
  if (!c.error) return null;
  return (
    <p className="err" role="alert">
      <IconAlert />
      {c.error}
    </p>
  );
}

export const AGENT_WORDS: Record<string, string> = {
  disconnected: "Not connected",
  connecting: "Connecting",
  initializing: "Joining the call",
  idle: "Ready",
  listening: "Listening",
  thinking: "Thinking",
  speaking: "Speaking",
};

export function statusWord(c: CallModel): string {
  if (c.phase === "connecting") return "Connecting";
  if (c.phase === "live") return c.speaking?.who === "lead" ? "You are speaking" : `Nimra · ${AGENT_WORDS[c.agentState] ?? c.agentState}`;
  if (c.phase === "sample")
    return c.speaking?.who === "lead"
      ? `${c.lead.name.split(" ")[0]} is speaking`
      : c.speaking?.who === "omar"
        ? "Nimra is speaking"
        : c.turns.length
          ? "Nimra is preparing the reply"
          : "Ringing";
  if (c.phase === "ended") return c.snap?.ended ? `Ended · ${shortStatus(c.snap.status)}` : "Call ended";
  if (c.phase === "error") return "Could not connect";
  return "Ready";
}

export function CodeState({ snap, c }: { snap: CallSnapshot | null; c?: CallModel }) {
  if (!snap)
    return (
      <>
        <p className="muted">The code&apos;s state appears when the call starts.</p>
        {c && <LlmCompare c={c} />}
      </>
    );
  return (
    <>
    <dl className="kv">
      <dt>Stage</dt>
      <dd>{stageName(snap.stage)}</dd>
      <dt>Lead status</dt>
      <dd>{snap.status}</dd>
      <dt>Rapport turns</dt>
      <dd>
        <Pips n={snap.rapportTurns} of={snap.minRapportTurns} />
        {snap.rapportTurns >= snap.minRapportTurns ? `${snap.rapportTurns}, enough` : `${snap.rapportTurns} of ${snap.minRapportTurns}`}
      </dd>
      <dt>Objections handled</dt>
      <dd>
        <Pips n={snap.objections} of={snap.maxObjections} />
        {snap.objections} of {snap.maxObjections}
      </dd>
      <dt>Asked if AI</dt>
      <dd>{snap.aiDisclosed ? "Yes, Nimra said she is an AI" : "Not yet"}</dd>
      {snap.offered.length > 0 && (
        <>
          <dt>Slots offered</dt>
          <dd>{snap.offered.join(" · ")}</dd>
        </>
      )}
      {snap.chosen && (
        <>
          <dt>Slot chosen</dt>
          <dd>
            {snap.chosen}
            {snap.bookingConfirmed ? ", confirmed" : ", not confirmed yet"}
          </dd>
        </>
      )}
    </dl>
      {c?.keyStatus && (
        <small className="llm-status" data-ok={c.keyStatus.ok || undefined}>
          DeepSeek key: {c.keyStatus.text}
        </small>
      )}
      <LlmUsage snap={snap} />
      {c && <LlmCompare c={c} />}
    </>
  );
}

export function Pips({ n, of }: { n: number; of: number }) {
  return (
    <span className="pips" aria-hidden="true">
      {Array.from({ length: of }, (_, i) => (
        <i key={i} data-on={i < n || undefined} />
      ))}
    </span>
  );
}

export function GuardList({ snap }: { snap: CallSnapshot | null }) {
  const hits = snap?.guardHits ?? [];
  if (!hits.length)
    return <p className="muted">No sentence blocked yet. The guard checks every sentence before Nimra says it.</p>;
  return (
    <ul className="guard">
      {hits.map((h) => (
        <li key={h.at}>
          <b>{ruleWord(h.rule)}</b>
          <s>{h.said}</s>
        </li>
      ))}
    </ul>
  );
}

export function Opening({ snap }: { snap: CallSnapshot | null }) {
  const o = snap?.opening;
  const items = [
    { ok: o?.companyAndPurpose, label: "Said company and purpose" },
    { ok: o?.recordingNotice, label: "Gave the recording notice" },
    { ok: o?.askedToContinue, label: "Asked if now is a good time" },
  ];
  return (
    <ul className="checks">
      {items.map((i) => (
        <li key={i.label} data-on={i.ok || undefined}>
          <span className="ck" aria-hidden="true" />
          {i.label}
          <span className="sr-only">{i.ok ? ": done" : ": not yet"}</span>
        </li>
      ))}
    </ul>
  );
}

export function StepChips({ steps, tool }: { steps: Step[]; tool?: boolean }) {
  if (!steps.length && !tool) return null;
  return (
    <ul className="chips" aria-label="What the code recorded">
      {steps.map((s) => (
        <li key={`${s.at}-${s.event}`} data-by={s.by}>
          {stepWord(s)}
          <em>{s.by === "llm" ? "LLM" : "code"}</em>
        </li>
      ))}
      {tool && (
        <li data-by="tool">
          Tool call<em>LLM</em>
        </li>
      )}
    </ul>
  );
}

export function ConfigLine({ snap }: { snap: CallSnapshot | null }) {
  const cf = snap?.config;
  if (!cf) return null;
  return (
    <p className="cfg">
      {cf.turnMode === "flux" ? "Deepgram Flux end of turn" : "LiveKit turn detector"} · {cf.minDelay.toFixed(2)} s
      endpointing · {cf.model}
      {cf.preemptive ? " · preemptive on" : ""}
      {cf.guard ? "" : " · guard off"}
    </p>
  );
}
