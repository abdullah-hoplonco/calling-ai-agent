"use client";

// Showcase: a product landing page whose hero is the working demo itself.

import Image from "next/image";
import { useEffect, useRef } from "react";

import { CallButton, ErrorNote, GuardList, LeadPicker, MuteToggle, Opening, SampleButton, StepChips, statusWord } from "@/components/blocks";
import { IconArrow, IconCode, IconShield } from "@/components/icons";
import { PartsBar, Waveform, medianParts } from "@/components/shared";
import { RULE_WORDS, TRACK, trackIndex } from "@/lib/stages";
import type { CallModel } from "@/lib/useCall";
import { PARTS, TARGET_MS, clock, initials, ms, partsOf, sec, stageName, tone } from "@/lib/view";

export function ShowcaseView({ c, switcher }: { c: CallModel; switcher: React.ReactNode }) {
  const tryRef = useRef<HTMLElement>(null);
  return (
    <div className="sc">
      <header className="sc-nav">
        <Image src="/hoplon-logo.png" alt="Hoplon & Co" width={124} height={23} priority />
        <nav className="sc-links" aria-label="Sections">
          <a href="#numbers">The numbers</a>
          <a href="#how">How a reply is made</a>
          <a href="#rules">Rules</a>
          <a href="#try">Try it</a>
        </nav>
        <div className="sc-nav-r">{switcher}</div>
      </header>

      <section className="sc-hero">
        <div className="sc-hero-copy">
          <h1>The AI caller that books the meeting.</h1>
          <p className="sc-lede">
            Omar phones the people who filled in your form, answers what they asked, and books a Discovery Call with your
            manager. The code runs the call. The AI only writes the words.
          </p>
          <div className="sc-cta">
            <SampleButton c={c} className="sc-btn sc-gold" />
            <CallButton c={c} className="sc-btn sc-line" />
            <MuteToggle c={c} />
          </div>
          <p className="sc-small">Every reply is timed on this page. Target: {TARGET_MS / 1000} s for a typical reply.</p>
          <ErrorNote c={c} />
        </div>
        <Window c={c} />
      </section>

      <Numbers c={c} />
      <How c={c} />
      <Rules c={c} />

      <section className="sc-sec sc-try" id="try" ref={tryRef}>
        <div className="sc-try-l">
          <h2>Call one of three test Leads.</h2>
          <p>
            Each Lead is synthetic and tests a different path. Use a headset; the browser asks for your microphone. No
            keys? Hear the sample call instead.
          </p>
          <LeadPicker c={c} />
          <div className="sc-cta">
            <CallButton c={c} className="sc-btn sc-navy" />
            <SampleButton c={c} className="sc-btn sc-outline" />
          </div>
        </div>
        <Transcript c={c} />
      </section>

      <footer className="sc-foot">
        <Image src="/hoplon-logo.png" alt="" width={104} height={19} />
        <p>
          Omar demo, milestone M1. Browser calls only; the calendar is simulated.
          {c.source === "sample" && " The sample call's words and numbers are synthetic."}
        </p>
      </footer>
    </div>
  );
}

function Window({ c }: { c: CallModel }) {
  const lines = c.turns.slice(-2);
  const last = [...c.turns].reverse().find((t) => t.turn.totalMs != null);
  const cur = trackIndex(c.snap?.stage);
  return (
    <div className="sc-win" aria-label="Live call">
      <div className="sc-win-bar">
        <span className="sc-live" data-on={c.busy || undefined} />
        <b>{c.busy ? "Live call" : c.phase === "ended" ? "Call ended" : "Ready to call"}</b>
        <span className="sc-win-who">
          <span className="sc-av">{initials(c.lead.name)}</span>
          {c.lead.name}
        </span>
      </div>
      <div className="sc-win-wave">
        <Waveform c={c} height={88} />
        {!c.busy && c.turns.length === 0 && <p>Press “Hear a sample call”. The call draws here as it is spoken.</p>}
      </div>
      <div className="sc-win-stages">
        {TRACK.map((s, i) => (
          <span key={s.id} data-state={cur < 0 ? "todo" : i < cur || c.snap?.ended ? "done" : i === cur ? "now" : "todo"}>
            {s.label}
          </span>
        ))}
      </div>
      <div className="sc-win-lines" aria-live="polite">
        {lines.length === 0 && <p className="sc-win-ph">{statusWord(c)}</p>}
        {lines.map((t) => (
          <div key={t.turn.turn} className="sc-win-turn" data-fresh={t.fresh || undefined}>
            {t.turn.lead_text && (
              <p data-who="lead">
                <b>{c.lead.name.split(" ")[0]}</b>
                {t.turn.lead_text}
              </p>
            )}
            <p data-who="omar">
              <b>Omar</b>
              {t.turn.omar_text}
            </p>
          </div>
        ))}
      </div>
      <div className="sc-win-foot">
        {last ? (
          <>
            <span>Last reply</span>
            <b data-tone={tone(last.turn.totalMs)}>{ms(last.turn.totalMs)}</b>
            <PartsBar turn={last.turn} scaleMs={2000} animate={last.fresh} className="sc-win-pb" />
          </>
        ) : (
          <span>{c.busy ? statusWord(c) : "The wait before each reply shows here."}</span>
        )}
      </div>
    </div>
  );
}

function Numbers({ c }: { c: CallModel }) {
  const o = c.summary?.overall;
  const p50 = o?.totalMs.p50 ?? null;
  const p95 = o?.totalMs.p95 ?? null;
  const measured = c.turns.filter((t) => t.turn.totalMs != null);
  return (
    <section className="sc-sec sc-num" id="numbers">
      <h2 className="sc-big">
        {p50 != null ? (
          <>
            On this call, Omar&apos;s typical reply came in <em data-tone={tone(p50)}>{sec(p50)}</em> after the Lead
            stopped talking. The slowest took <em data-tone={tone(p95)}>{sec(p95)}</em>.
          </>
        ) : (
          <>Start a call above. This line fills with the delay measured on it, reply by reply.</>
        )}
      </h2>
      {measured.length > 0 && (
        <ol className="sc-rows">
          {measured.map((t) => (
            <li key={t.turn.turn} data-fresh={t.fresh || undefined}>
              <span className="sc-rows-n">
                Reply {t.turn.turn}
                <small>{stageName(t.turn.stage)}</small>
              </span>
              <PartsBar turn={t.turn} scaleMs={2000} animate={t.fresh} />
              <b data-tone={tone(t.turn.totalMs)}>{ms(t.turn.totalMs)}</b>
            </li>
          ))}
        </ol>
      )}
      {c.source === "sample" && <p className="sc-small">Sample call: synthetic numbers, to show how the page reads.</p>}
    </section>
  );
}

const PLAIN: Record<string, string> = {
  detect: "Hears that you finished. Deepgram decides your turn is over.",
  commit: "Commits the turn and hands your words to the call logic.",
  tool: "When the call logic needs it, one extra LLM step first.",
  llm: "The LLM starts writing Omar's reply.",
  guard: "The guard checks the first sentence against the rules.",
  tts: "The voice engine turns that sentence into Omar's first audio.",
};

function How({ c }: { c: CallModel }) {
  const med = medianParts(c.turns);
  const byKey = new Map(med.map((p) => [p.key, p.ms]));
  const total = med.reduce((a, p) => a + p.ms, 0);
  return (
    <section className="sc-sec sc-how" id="how">
      <div className="sc-how-h">
        <h2>Anatomy of one wait.</h2>
        <p>
          From your last word to Omar&apos;s first sound, six steps run one after another. The page measures each one on
          every reply{total ? `; below is the median for this call, ${total.toLocaleString("en-US")} ms in all.` : "."}
        </p>
      </div>
      <div className="sc-anat">
        <div className="sc-anat-bar" aria-hidden="true">
          {PARTS.map((p) => (
            <i key={p.key} className={`p-${p.cls}`} style={{ flexGrow: byKey.get(p.key) ?? 1 }} />
          ))}
        </div>
        <ol className="sc-anat-list">
          {PARTS.map((p) => (
            <li key={p.key}>
              <i className={`p-${p.cls}`} aria-hidden="true" />
              <b>{p.label}</b>
              <span>{PLAIN[p.cls]}</span>
              <em>{byKey.has(p.key) ? `${byKey.get(p.key)} ms` : "–"}</em>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

function Rules({ c }: { c: CallModel }) {
  const hits = c.snap?.guardHits ?? [];
  return (
    <section className="sc-sec sc-rules" id="rules">
      <div className="sc-rules-l">
        <span className="sc-ic">
          <IconCode />
        </span>
        <h2>The code owns the call.</h2>
        <p>
          A state machine decides the stage, the next question and when the call ends. The LLM writes the sentences, and
          every sentence passes the guard before Omar says it. When a rule blocks a sentence, you see it here.
        </p>
        <h3>Legal opening</h3>
        <Opening snap={c.snap} />
      </div>
      <div className="sc-rules-r">
        <h3>
          <IconShield /> Rules the guard enforces
        </h3>
        <ul className="sc-rule-list">
          {Object.entries(RULE_WORDS).map(([k, v]) => {
            const n = hits.filter((h) => h.rule === k).length;
            return (
              <li key={k} data-hit={n > 0 || undefined}>
                {v}
                <span>{n ? `Blocked ${n} on this call` : "Enforced"}</span>
              </li>
            );
          })}
        </ul>
        {hits.length > 0 && (
          <>
            <h3>Blocked on this call</h3>
            <GuardList snap={c.snap} />
          </>
        )}
      </div>
    </section>
  );
}

function Transcript({ c }: { c: CallModel }) {
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = box.current;
    if (el && c.busy) el.scrollTop = el.scrollHeight;
  }, [c.turns.length, c.busy]);
  return (
    <div className="sc-tr" ref={box}>
      <div className="sc-tr-h">
        <b>Transcript</b>
        <span>{c.turns.length ? `${c.turns.length} replies · ${clock(c.length)}` : "Empty"}</span>
      </div>
      {c.turns.length === 0 && <p className="sc-tr-empty">The full call appears here, with the wait before each reply.</p>}
      {c.turns.map((t) => (
        <div key={t.turn.turn} className="sc-tr-t">
          {t.turn.lead_text && (
            <p data-who="lead">
              <b>{c.lead.name.split(" ")[0]}</b>
              {t.turn.lead_text}
            </p>
          )}
          <p data-who="omar">
            <b>
              Omar
              {t.turn.totalMs != null ? <em data-tone={tone(t.turn.totalMs)}>{ms(t.turn.totalMs)}</em> : <em>scripted</em>}
            </b>
            {t.turn.omar_text}
          </p>
          {partsOf(t.turn).length > 0 && <PartsBar turn={t.turn} scaleMs={2000} />}
          <StepChips steps={t.steps} tool={t.turn.toolTurn} />
        </div>
      ))}
      {c.busy && (
        <p className="sc-tr-now">
          <IconArrow />
          {statusWord(c)}
        </p>
      )}
    </div>
  );
}
