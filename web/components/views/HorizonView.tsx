"use client";

// Horizon: the default theme. A dark mirror orb over a night sea whose edge is the voice,
// in Hoplon's black and lime. The world changes with each stage of the call. No timing
// numbers on screen: the call is the show. The four older themes sit behind a small switch.

import { useLocalParticipant, useVoiceAssistant } from "@livekit/components-react";
import { type FormEvent, type ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { agentOf } from "@/components/blocks";
import { CHAPTERS, newSignal } from "@/lib/horizon/world";
import { createTap, type Tap } from "@/lib/horizon/liveTap";
import { SampleCall } from "@/lib/horizon/sample";
import { speechMs } from "@/lib/speech";
import { shortStatus, trackIndex } from "@/lib/stages";
import type { CallModel } from "@/lib/useCall";

type Mode = "entry" | "sample" | "live" | "close";
type Line = { who: "agent" | "lead"; words: string[] };

// sample: which chapter each recorded line opens (see public/horizon/timeline.json)
const SAMPLE_CHAPTER = [0, 0, 1, 2, 3, 4, 4, 5, 5];
const SAMPLE_LEAD = "Sara";
// words said with feeling: set in lime italics
const FEEL = new Set(["lovely!", "honestly?", "quiet.", "story!", "really", "wonderful.", "yes.", "booked,"]);

const firstName = (n: string) => n.trim().split(/\s+/)[0] ?? "";
const stripTags = (s: string) => s.replace(/\[[^\]]*\]/g, " ").replace(/\s+/g, " ").trim();

export function HorizonView({ c, switcher }: { c: CallModel; switcher: ReactNode }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const signal = useMemo(newSignal, []);
  const [noGl, setNoGl] = useState(false);
  const [mode, setMode] = useState<Mode>("entry");
  const [kind, setKind] = useState<"sample" | "live">("live");
  const [line, setLine] = useState<Line | null>(null);
  const [shown, setShown] = useState(-1);
  const [out, setOut] = useState(false);
  const [chapter, setChapter] = useState(0);
  const [sr, setSr] = useState("");
  const [sampleError, setSampleError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const sample = useRef<SampleCall | null>(null);
  const audio = useRef<AudioContext | null>(null);

  const agent = agentOf(c);
  const leadFirst = firstName(c.lead.name);
  const you = firstName(c.name) || leadFirst;
  const speaker = kind === "sample" ? SAMPLE_LEAD : you;

  // ---- the world ----
  useEffect(() => {
    let dead = false;
    let world: { dispose: () => void } | null = null;
    import("@/lib/horizon/world")
      .then(({ createWorld }) => {
        if (dead || !canvas.current) return;
        try {
          world = createWorld(canvas.current, signal);
        } catch {
          setNoGl(true); // no WebGL: the page still works over a plain night background
        }
      })
      .catch(() => setNoGl(true));
    return () => {
      dead = true;
      world?.dispose();
    };
  }, [signal]);

  const toChapter = useCallback(
    (i: number) => {
      signal.chapter = i;
      setChapter(i);
    },
    [signal],
  );

  const resetWorld = useCallback(() => {
    Object.assign(signal, { started: false, ended: false, who: null, agent: 0, lead: 0, chapter: 0, laugh: 0 });
    signal.bands.fill(0);
    setLine(null);
    setShown(-1);
    setOut(false);
    setChapter(0);
    setSr("");
  }, [signal]);

  // ---- sample: the recorded call ----
  const playSample = useCallback(async () => {
    setSampleError(null);
    setStarting(true);
    resetWorld();
    const s = new SampleCall({
      line: (l, i) => {
        const words = l.words.map((w) => w.text);
        setLine({ who: l.who, words });
        setShown(-1);
        setOut(false);
        setSr(`${l.who === "agent" ? "Uzair" : SAMPLE_LEAD}: ${words.join(" ")}`);
        toChapter(Math.max(signal.chapter, SAMPLE_CHAPTER[i] ?? 0));
      },
      word: (i) => setShown(i),
      pause: () => setOut(true),
      tag: (t) => {
        if (t === "laughs") signal.laugh = 1;
      },
      end: () => {
        signal.ended = true;
        toChapter(CHAPTERS.length - 1);
        setOut(true);
        setMode("close");
      },
    });
    sample.current = s;
    try {
      await s.load();
      await s.start();
      setKind("sample");
      signal.started = true;
      setMode("sample");
    } catch (e) {
      s.stop();
      sample.current = null;
      setSampleError(`The sample call could not play. ${e instanceof Error ? e.message : ""} Reload the page and try again.`);
    } finally {
      setStarting(false);
    }
  }, [resetWorld, signal, toChapter]);

  // ---- live: the real call ----
  const startLive = useCallback(async () => {
    resetWorld();
    setKind("live");
    setMode("live");
    try {
      audio.current ??= new AudioContext(); // made in the click, so the browser lets it run
      await audio.current.resume();
    } catch {
      /* the equaliser stays still; the call still works */
    }
    await c.call();
  }, [c, resetWorld]);

  // the call model drives the live mode
  useEffect(() => {
    if (kind !== "live") return;
    if (mode === "live" && c.phase === "live") signal.started = true;
    if (mode === "live" && c.phase === "error") {
      resetWorld();
      setMode("entry");
    }
    if (mode === "live" && c.phase === "ended") {
      signal.ended = true;
      signal.who = null;
      toChapter(CHAPTERS.length - 1);
      setOut(true);
      setMode("close");
    }
  }, [c.phase, kind, mode, resetWorld, signal, toChapter]);

  // live chapter: the stage the code has reached, never backwards
  useEffect(() => {
    if (kind !== "live" || mode !== "live") return;
    const i = trackIndex(c.snap?.stage);
    if (i >= 0) toChapter(Math.max(signal.chapter, Math.min(i, CHAPTERS.length - 1)));
  }, [c.snap?.stage, kind, mode, signal, toChapter]);

  // live captions: the agent's newest reply, revealed at speaking pace
  const lastTurn = c.turns.at(-1);
  const replyAt = useRef(0);
  useEffect(() => {
    if (kind !== "live" || !lastTurn) return;
    const text = lastTurn.turn.omar_text;
    if (!text) return;
    const words = stripTags(text).split(" ").filter(Boolean);
    replyAt.current = performance.now();
    setLine({ who: "agent", words });
    setShown(0);
    setOut(false);
    setSr(`${agent}: ${words.join(" ")}`);
    if (/\[laughs?\]/i.test(text)) signal.laugh = 1;
  }, [lastTurn?.turn.turn, lastTurn?.turn.omar_text, kind, agent, signal]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (kind === "live" && c.speaking?.who === "lead") setOut(true);
  }, [c.speaking, kind]);

  // ---- the frame loop: read the voices into the signal ----
  const { audioTrack } = useVoiceAssistant();
  const { microphoneTrack } = useLocalParticipant();
  const agentStream = audioTrack?.publication?.track?.mediaStreamTrack;
  const micStream = microphoneTrack?.track?.mediaStreamTrack;
  const speakingRef = useRef(c.speaking);
  speakingRef.current = c.speaking;
  const lineRef = useRef(line);
  lineRef.current = line;

  useEffect(() => {
    if (mode !== "sample" && mode !== "live") return;
    const ctx = audio.current;
    const taps: { agent: Tap | null; lead: Tap | null } = { agent: null, lead: null };
    if (mode === "live" && ctx) {
      try {
        if (agentStream) taps.agent = createTap(ctx, agentStream);
        if (micStream) taps.lead = createTap(ctx, micStream);
      } catch {
        /* no analyser: the orb still moves with the call state */
      }
    }
    const aBands = new Float32Array(32), lBands = new Float32Array(32);
    let raf = 0, lastShown = -1;
    const loop = () => {
      raf = requestAnimationFrame(loop);
      if (mode === "sample" && sample.current) {
        const s = sample.current.tick();
        signal.who = s.who;
        signal.agent = s.level.agent;
        signal.lead = s.level.lead;
        signal.bands.set(s.bands);
        return;
      }
      const sp = speakingRef.current?.who;
      const who = sp === "omar" ? "agent" : sp === "lead" ? "lead" : null;
      const a = taps.agent?.read(aBands) ?? 0;
      const l = taps.lead?.read(lBands) ?? 0;
      signal.who = who;
      signal.agent += ((who === "agent" ? a : a * 0.5) - signal.agent) * 0.3;
      signal.lead += ((who === "lead" ? l : 0) - signal.lead) * 0.3;
      signal.bands.set(who === "lead" ? lBands : aBands);
      // reveal the reply word by word at about speaking pace
      const ln = lineRef.current;
      if (ln && ln.who === "agent") {
        const per = speechMs(ln.words.join(" ")) / Math.max(1, ln.words.length);
        const n = Math.min(ln.words.length - 1, Math.floor((performance.now() - replyAt.current) / per));
        if (n !== lastShown) {
          lastShown = n;
          setShown(n);
        }
      }
    };
    raf = requestAnimationFrame(loop);
    return () => {
      cancelAnimationFrame(raf);
      taps.agent?.close();
      taps.lead?.close();
    };
  }, [mode, agentStream, micStream, signal]);

  // stop everything when the view goes away
  useEffect(
    () => () => {
      sample.current?.stop();
      void audio.current?.close().catch(() => {});
    },
    [],
  );

  const endCall = () => {
    if (mode === "sample") {
      sample.current?.stop();
      sample.current = null;
      signal.ended = true;
      setMode("close");
    } else c.hangUp();
  };

  const backToStart = () => {
    sample.current?.stop();
    sample.current = null;
    resetWorld();
    setMode("entry");
  };

  const callAgain = () => (kind === "sample" ? void playSample() : void startLive());

  // ---- entry: eyes that follow you ----
  const eyes = useRef<HTMLDivElement>(null);
  const enter = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (mode !== "entry") return;
    const move = (e: PointerEvent) => {
      const box = eyes.current;
      if (!box) return;
      box.querySelectorAll<HTMLElement>(".hz-eye b").forEach((b) => {
        const r = b.parentElement!.getBoundingClientRect();
        const dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2);
        const k = Math.min(1, Math.hypot(dx, dy) / 200), ang = Math.atan2(dy, dx);
        b.style.transform = `translate(${Math.cos(ang) * 8 * k}px, ${Math.sin(ang) * 8 * k}px)`;
      });
      const r = enter.current?.getBoundingClientRect();
      if (r) box.toggleAttribute("data-wide", Math.hypot(e.clientX - (r.left + r.width / 2), e.clientY - (r.top + r.height / 2)) < 160);
    };
    window.addEventListener("pointermove", move);
    return () => window.removeEventListener("pointermove", move);
  }, [mode]);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    void startLive();
  };

  // ---- words for the chrome ----
  const inCall = mode === "sample" || mode === "live";
  const C = CHAPTERS[chapter]!;
  const connecting = mode === "live" && c.phase === "connecting";
  const sampleWho = kind === "sample" && line && !out ? line.who : null;
  const agentTalks = kind === "sample" ? sampleWho === "agent" : c.speaking?.who === "omar";
  const leadTalks = kind === "sample" ? sampleWho === "lead" : c.speaking?.who === "lead";
  const stateText = connecting
    ? "Connecting"
    : mode === "close"
      ? kind === "sample" || c.snap?.bookingConfirmed
        ? "Booked"
        : "Call ended"
      : agentTalks
        ? `${kind === "sample" ? "Uzair" : agent} is speaking`
        : leadTalks
          ? `${speaker} is speaking`
          : "Listening";

  const booked = kind === "sample" || Boolean(c.snap?.bookingConfirmed);
  const outcome = kind === "sample" ? "" : c.snap?.chosen ?? shortStatus(c.snap?.status ?? "") ?? "";

  return (
    <div className="hz" data-mode={mode} data-nogl={noGl || undefined}>
      <canvas ref={canvas} className="hz-canvas" aria-hidden="true" />

      {mode !== "entry" && (
        <div className="hz-chrome">
          <span className="hz-logo">
            hoplon &amp; co<b>.</b>
          </span>
          <div className="hz-top">
            <span className="hz-state">
              <i data-on={stateText.endsWith("speaking") || undefined} />
              {stateText}
            </span>
            {inCall && (
              <button type="button" className="hz-end" onClick={endCall}>
                End call
              </button>
            )}
          </div>
          <div className="hz-speech" data-who={line?.who} data-out={out || mode === "close" || undefined} aria-hidden="true">
            {line && (
              <>
                <small>{line.who === "agent" ? `${kind === "sample" ? "Uzair" : agent} · Hoplon & Co` : speaker}</small>
                <p>
                  {line.words.map((w, i) => (
                    <span key={i} className={FEEL.has(w.toLowerCase()) ? "feel" : undefined} data-on={i <= shown || undefined}>
                      {w}{" "}
                    </span>
                  ))}
                </p>
              </>
            )}
          </div>
          <p className="hz-sr" aria-live="polite">
            {sr}
          </p>
          {inCall && !connecting && (
            <span className="hz-chapter">
              <b>{C.label}</b> · {C.title}
            </span>
          )}
          <span className="hz-note">{kind === "sample" ? "Sample call · synthetic voices" : "Live call · AI agent"}</span>
        </div>
      )}

      {mode === "close" && (
        <section className="hz-close" aria-live="polite">
          <small>{booked ? "Booked" : "Call ended"}</small>
          {kind === "sample" ? (
            <h2>
              Thursday, <span>11:00.</span>
            </h2>
          ) : booked && c.snap?.chosen ? (
            <h2>
              <span>{c.snap.chosen}.</span>
            </h2>
          ) : (
            <h2>{outcome || "Thank you."}</h2>
          )}
          <ul>
            <li>
              With <b>{speaker}</b>
              {kind === "sample" ? ", café owner" : ""}
            </li>
            {kind === "sample" ? (
              <li>
                Heard <b>“People queue for the buns”</b>
              </li>
            ) : (
              c.lead.topic && (
                <li>
                  About <b>{c.lead.topic}</b>
                </li>
              )
            )}
            <li>
              Next <b>{booked ? "a call with the manager, invite sent" : (c.snap?.status ?? "we follow up")}</b>
            </li>
          </ul>
        </section>
      )}
      {mode === "close" && (
        <div className="hz-again">
          <button type="button" className="hz-primary" onClick={callAgain}>
            {kind === "sample" ? "Play it again" : "Call me again"}
          </button>
          <button type="button" className="hz-quiet" onClick={backToStart}>
            Back to the start
          </button>
        </div>
      )}

      {mode === "entry" && (
        <section className="hz-entry">
          <form className="hz-card" onSubmit={submit}>
            <div className="hz-eyes" ref={eyes} aria-hidden="true">
              <span className="hz-eye">
                <b />
              </span>
              <span className="hz-eye">
                <b />
              </span>
            </div>
            <h1>
              {agent} would like to <span>call you.</span>
            </h1>
            <p className="hz-lede">
              A short call from Hoplon &amp; Co&apos;s AI agent. The world around you changes with every turn of it.
            </p>
            <div className="hz-fields">
              <label>
                Your name
                <input
                  value={c.name}
                  onChange={(e) => c.setName(e.target.value)}
                  placeholder={leadFirst}
                  autoComplete="given-name"
                  name="given-name"
                  maxLength={40}
                />
                <small>Leave it empty and {agent} calls you {leadFirst}.</small>
              </label>
              <label>
                Who are you today?
                <select value={c.leadId} onChange={(e) => c.setLeadId(e.target.value)} name="scenario">
                  {c.leads.map((l) => (
                    <option key={l.id} value={l.id}>
                      {l.scenario}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="hz-go">
              <button type="submit" className="hz-primary" ref={enter}>
                Start the call
              </button>
              <span className="hz-hint">Uses your microphone · about two minutes</span>
              <button type="button" className="hz-quiet" onClick={() => void playSample()} disabled={starting}>
                {starting ? "Loading the sample…" : "Hear a sample call first"}
              </button>
            </div>
            {(c.error || sampleError) && (
              <p className="hz-error" role="alert">
                {sampleError ?? c.error}
              </p>
            )}
          </form>
        </section>
      )}

      <details className="hz-themes">
        <summary>Theme</summary>
        {switcher}
      </details>
    </div>
  );
}
