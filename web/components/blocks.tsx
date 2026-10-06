"use client";

import { IconAlert, IconMute, IconPhone, IconPhoneOff, IconSpeaker, IconStop } from "@/components/icons";
import { OLD_LEAD_MONTH } from "@/lib/leads";
import type { CallSnapshot, Step } from "@/lib/types";
import type { CallModel } from "@/lib/useCall";
import { initials, ruleWord, stageName, stepWord } from "@/lib/view";
import { shortStatus } from "@/lib/stages";

export function LeadPicker({ c, compact = false }: { c: CallModel; compact?: boolean }) {
  return (
    <fieldset className="lp-set" disabled={c.busy}>
      <legend className="lp-legend">Who Omar calls</legend>
      {c.leads.map((l) => (
        <label key={l.id} className="lp-opt" data-on={l.id === c.leadId || undefined}>
          <input type="radio" name="lead" value={l.id} checked={l.id === c.leadId} onChange={() => c.setLeadId(l.id)} />
          <span className="lp-av" aria-hidden="true">
            {initials(l.name)}
          </span>
          <span className="lp-body">
            <span className="lp-name">{l.name}</span>
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
          <small>Omar opens with “you reached out back in {OLD_LEAD_MONTH}”.</small>
        </span>
      </label>
    </fieldset>
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
  if (c.phase === "live") return c.speaking?.who === "lead" ? "You are speaking" : `Omar · ${AGENT_WORDS[c.agentState] ?? c.agentState}`;
  if (c.phase === "sample")
    return c.speaking?.who === "lead"
      ? `${c.lead.name.split(" ")[0]} is speaking`
      : c.speaking?.who === "omar"
        ? "Omar is speaking"
        : c.turns.length
          ? "Omar is preparing the reply"
          : "Ringing";
  if (c.phase === "ended") return c.snap?.ended ? `Ended · ${shortStatus(c.snap.status)}` : "Call ended";
  if (c.phase === "error") return "Could not connect";
  return "Ready";
}

export function CodeState({ snap }: { snap: CallSnapshot | null }) {
  if (!snap) return <p className="muted">The code&apos;s state appears when the call starts.</p>;
  return (
    <dl className="kv">
      <dt>Stage</dt>
      <dd>{stageName(snap.stage)}</dd>
      <dt>Lead status</dt>
      <dd>{snap.status}</dd>
      <dt>Rapport turns</dt>
      <dd>
        <Pips n={snap.rapportTurns} of={snap.minRapportTurns} />
        {snap.rapportTurns} of {snap.minRapportTurns}
      </dd>
      <dt>Objections handled</dt>
      <dd>
        <Pips n={snap.objections} of={snap.maxObjections} />
        {snap.objections} of {snap.maxObjections}
      </dd>
      <dt>Asked if AI</dt>
      <dd>{snap.aiDisclosed ? "Yes, Omar said he is an AI" : "Not yet"}</dd>
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
    return <p className="muted">No sentence blocked yet. The guard checks every sentence before Omar says it.</p>;
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
