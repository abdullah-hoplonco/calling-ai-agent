"use client";

// One call, read the same way by every theme: live (LiveKit) or the spoken sample.
// Times on the timeline are ms since the call started, on the browser's clock.

import { Room, RoomEvent } from "livekit-client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { LEADS, type DemoLead } from "@/lib/leads";
import { levels } from "@/lib/levels";
import { playSample } from "@/lib/replay";
import { speechMs } from "@/lib/speech";
import type { CallSnapshot, LatencyMessage, LatencySummary, Step } from "@/lib/types";

export type Phase = "idle" | "connecting" | "live" | "sample" | "ended" | "error";
export type Who = "lead" | "omar";

export type TurnView = {
  turn: LatencyMessage["turn"];
  steps: Step[];
  leadAt: number | null;
  leadEnd: number | null;
  omarAt: number;
  omarEnd: number | null;
  heardMs: number | null;
  fresh: boolean;
};

export type Speaking = { who: Who; since: number } | null;
export type Net = { rttMs: number; jitterMs: number };

export type CallModel = ReturnType<typeof useCall>;

export function useCall() {
  const room = useMemo(() => new Room({ adaptiveStream: true, dynacast: true }), []);
  const [leadId, setLeadId] = useState(LEADS[0]!.id);
  const [old, setOld] = useState(false);
  const [phase, setPhase] = useState<Phase>("idle");
  const [source, setSource] = useState<"live" | "sample" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [snap, setSnap] = useState<CallSnapshot | null>(null);
  const [turns, setTurns] = useState<TurnView[]>([]);
  const [summary, setSummary] = useState<LatencySummary | null>(null);
  const [speaking, setSpeakingState] = useState<Speaking>(null);
  const [agentState, setAgentState] = useState("idle");
  const [endedAt, setEndedAt] = useState<number | null>(null);
  const [muted, setMuted] = useState(false);
  const [net, setNet] = useState<Net | null>(null);

  const t0 = useRef<number | null>(null);
  const snapRef = useRef<CallSnapshot | null>(null);
  const seen = useRef(new Set<string>());
  const speakingRef = useRef<Speaking>(null);
  const pendingLead = useRef<{ start: number; end: number } | null>(null);
  const netRef = useRef<Net | null>(null);
  const stopSample = useRef<(() => void) | null>(null);
  const sourceRef = useRef<"live" | "sample" | null>(null);
  sourceRef.current = source;

  const lead: DemoLead = LEADS.find((l) => l.id === leadId) ?? LEADS[0]!;
  const now = useCallback(() => (t0.current == null ? 0 : performance.now() - t0.current), []);

  const setSpeaking = useCallback((s: Speaking) => {
    speakingRef.current = s;
    setSpeakingState(s);
  }, []);

  const reset = useCallback(() => {
    stopSample.current?.();
    stopSample.current = null;
    t0.current = null;
    snapRef.current = null;
    seen.current.clear();
    pendingLead.current = null;
    setError(null);
    setSnap(null);
    setTurns([]);
    setSummary(null);
    setEndedAt(null);
    setSpeaking(null);
    setAgentState("idle");
    levels.lead = 0;
    levels.omar = 0;
  }, [setSpeaking]);

  const onState = useCallback((s: CallSnapshot) => {
    snapRef.current = s;
    setSnap(s);
  }, []);

  // A reply arrives when Omar's first audio plays; the worker sends the same turn again
  // with final numbers, so rows are updated by turn number, never appended twice.
  const onLatency = useCallback(
    (m: LatencyMessage) => {
      setSummary(m.summary);
      const t = now();
      const sp = speakingRef.current;
      const steps = newSteps(snapRef.current, m.turn.at, seen.current);
      const pend = pendingLead.current;
      pendingLead.current = null;
      setTurns((prev) => {
        const i = prev.findIndex((r) => r.turn.turn === m.turn.turn);
        if (i >= 0) {
          const next = [...prev];
          const r = next[i]!;
          next[i] = { ...r, turn: m.turn, steps: [...r.steps, ...steps], heardMs: heard(m.turn.totalMs, netRef.current) };
          return next;
        }
        const omarAt = sp?.who === "omar" && t - sp.since < 2500 ? sp.since : t;
        const total = m.turn.totalMs;
        let leadEnd: number | null = null;
        let leadAt: number | null = null;
        if (m.turn.lead_text || pend) {
          // live: the worker's measured wait places the end of your speech; sample: the spoken span
          leadEnd = sourceRef.current === "sample" && pend ? pend.end : total != null ? Math.max(0, omarAt - total) : (pend?.end ?? null);
          if (leadEnd != null) {
            const est = Math.max(700, speechMs(m.turn.lead_text));
            leadAt = pend && pend.start < leadEnd - 200 ? pend.start : Math.max(0, leadEnd - est);
          }
        }
        return [
          ...prev.map((r) => (r.fresh ? { ...r, fresh: false } : r)),
          {
            turn: m.turn,
            steps,
            leadAt,
            leadEnd,
            omarAt,
            omarEnd: null,
            heardMs: heard(total, netRef.current),
            fresh: true,
          },
        ];
      });
    },
    [now],
  );

  const closeOmar = useCallback(() => {
    const t = now();
    setTurns((prev) => {
      let i = prev.length - 1;
      while (i >= 0 && prev[i]!.omarEnd != null) i--;
      if (i < 0) return prev;
      const next = [...prev];
      next[i] = { ...next[i]!, omarEnd: Math.max(next[i]!.omarAt + 300, t) };
      return next;
    });
  }, [now]);

  // ---- live signals from LiveBridge ----
  const onAgentState = useCallback(
    (state: string) => {
      setAgentState(state);
      const sp = speakingRef.current;
      if (state === "speaking") {
        if (sp?.who !== "omar") setSpeaking({ who: "omar", since: now() });
      } else if (sp?.who === "omar") {
        setSpeaking(null);
        closeOmar();
      }
    },
    [now, closeOmar, setSpeaking],
  );

  // A light voice-activity check on your microphone, only to draw your speech on the timeline.
  const onMicLevel = useCallback(
    (level: number) => {
      const t = now();
      const sp = speakingRef.current;
      if (sp?.who === "omar" || t0.current == null) return;
      if (level > 0.06) {
        if (!pendingLead.current || t - pendingLead.current.end > 1500) pendingLead.current = { start: t, end: t };
        else pendingLead.current.end = t;
        if (sp?.who !== "lead") setSpeaking({ who: "lead", since: pendingLead.current.start });
      } else if (sp?.who === "lead" && pendingLead.current && t - pendingLead.current.end > 600) {
        setSpeaking(null);
      }
    },
    [now, setSpeaking],
  );

  const onNet = useCallback((v: Net) => {
    netRef.current = v;
    setNet(v);
  }, []);

  const phaseRef = useRef(phase);
  phaseRef.current = phase;

  useEffect(() => {
    const onDisconnected = () => {
      if (phaseRef.current !== "live" && phaseRef.current !== "connecting") return;
      setEndedAt(now());
      setSpeaking(null);
      setPhase("ended");
    };
    const onLeft = () => window.setTimeout(() => room.disconnect(), 600);
    room.on(RoomEvent.Disconnected, onDisconnected);
    room.on(RoomEvent.ParticipantDisconnected, onLeft);
    return () => {
      room.off(RoomEvent.Disconnected, onDisconnected);
      room.off(RoomEvent.ParticipantDisconnected, onLeft);
      room.disconnect();
    };
  }, [room, now, setSpeaking]);

  // ---- sample ----
  const mutedRef = useRef(muted);
  mutedRef.current = muted;

  const hearSample = useCallback(
    (speed = 1) => {
      reset();
      setLeadId(LEADS[0]!.id);
      setOld(false);
      setSource("sample");
      sourceRef.current = "sample";
      setPhase("sample");
      t0.current = performance.now();
      let fake = 0;
      const tick = () => {
        const sp = speakingRef.current;
        levels.lead = sp?.who === "lead" ? 0.15 + Math.random() * 0.2 : 0;
        levels.omar = sp?.who === "omar" ? 0.15 + Math.random() * 0.2 : 0;
        fake = window.setTimeout(tick, 80);
      };
      tick();
      const stop = playSample(
        {
          onState,
          onLeadStart: () => {
            pendingLead.current = { start: now(), end: now() };
            setSpeaking({ who: "lead", since: now() });
            setAgentState("listening");
          },
          onLeadEnd: () => {
            if (pendingLead.current) pendingLead.current.end = now();
            setSpeaking(null);
            setAgentState("thinking");
          },
          onReply: (m) => {
            setSpeaking({ who: "omar", since: now() });
            setAgentState("speaking");
            onLatency(m);
          },
          onOmarEnd: () => {
            setSpeaking(null);
            setAgentState("listening");
            closeOmar();
          },
          onDone: () => {
            window.clearTimeout(fake);
            levels.lead = levels.omar = 0;
            setEndedAt(now());
            setPhase("ended");
            setAgentState("idle");
          },
        },
        { muted: mutedRef.current, speed },
      );
      stopSample.current = () => {
        stop();
        window.clearTimeout(fake);
        levels.lead = levels.omar = 0;
      };
    },
    [reset, onState, onLatency, closeOmar, now, setSpeaking],
  );

  const endSample = useCallback(() => {
    stopSample.current?.();
    stopSample.current = null;
    setSpeaking(null);
    closeOmar();
    setEndedAt(now());
    setAgentState("idle");
    setPhase("ended");
  }, [closeOmar, now, setSpeaking]);

  useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    if (q.has("sample")) hearSample(Number(q.get("speed")) || 1);
    return () => stopSample.current?.();
  }, [hearSample]);

  // ---- live ----
  const call = useCallback(async () => {
    reset();
    setSource("live");
    setPhase("connecting");
    try {
      const res = await fetch("/api/token", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ leadId, old }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? `Token request failed (${res.status}).`);
      await room.connect(data.serverUrl, data.participantToken);
      await room.localParticipant.setMicrophoneEnabled(true);
      t0.current = performance.now();
      setPhase("live");
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(
        /permission|NotAllowed/i.test(msg)
          ? "The browser blocked the microphone. Allow microphone access for this page, then call again."
          : /not set/i.test(msg)
            ? "Live calls are not switched on for this deployment. Hear the sample call instead."
            : msg,
      );
      setPhase("error");
      room.disconnect();
    }
  }, [leadId, old, room, reset]);

  const hangUp = useCallback(() => {
    room.disconnect();
    setSpeaking(null);
    setEndedAt(now());
    setPhase("ended");
  }, [room, now, setSpeaking]);

  const busy = phase === "live" || phase === "connecting" || phase === "sample";
  const measured = turns.filter((r) => r.turn.totalMs != null && !r.turn.scripted);
  const length = Math.max(
    endedAt ?? 0,
    ...turns.map((r) => r.omarEnd ?? r.omarAt + speechMs(r.turn.omar_text)),
  );

  return {
    room,
    phase,
    source,
    error,
    busy,
    lead,
    leads: LEADS,
    leadId,
    setLeadId,
    old,
    setOld,
    snap,
    turns,
    measured,
    summary,
    speaking,
    agentState,
    endedAt,
    length,
    net,
    muted,
    setMuted,
    now,
    call,
    hangUp,
    hearSample,
    endSample,
    stop: phase === "sample" ? endSample : hangUp,
    onState,
    onLatency,
    onAgentState,
    onMicLevel,
    onNet,
  };
}

function heard(total: number | null | undefined, net: Net | null): number | null {
  if (total == null || !net) return null;
  return Math.round(total + net.rttMs + net.jitterMs);
}

// Steps the code recorded up to this reply, each shown once.
function newSteps(snap: CallSnapshot | null, at: number, seen: Set<string>): Step[] {
  const out: Step[] = [];
  for (const s of snap?.steps ?? []) {
    const key = `${s.at}-${s.event}`;
    if (s.at <= at && !seen.has(key)) {
      seen.add(key);
      out.push(s);
    }
  }
  return out;
}
