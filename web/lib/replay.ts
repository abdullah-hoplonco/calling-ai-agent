// A scripted sample call with SYNTHETIC numbers. It lets people see the console
// without API keys. Every number here is made up and labelled as such on screen.

import { say, speechMs, stopSpeech } from "@/lib/speech";
import type { CallSnapshot, LatencyMessage, LatencySummary, PartSummary, Step, Turn } from "@/lib/types";

type Beat =
  | { after: number; kind: "state"; patch: Partial<CallSnapshot>; step?: Omit<Step, "at"> }
  | { after: number; kind: "turn"; turn: Omit<Turn, "turn" | "at"> };

const BASE: CallSnapshot = {
  stage: "DIALING",
  stageLabel: "Dialing",
  status: "Lead (calling)",
  outcome: null,
  ended: false,
  rapportTurns: 0,
  minRapportTurns: 2,
  objections: 0,
  maxObjections: 2,
  offered: [],
  chosen: null,
  bookingConfirmed: false,
  aiDisclosed: false,
  opening: { companyAndPurpose: false, recordingNotice: false, askedToContinue: false },
  steps: [],
  guardHits: [],
  config: { turnMode: "flux", minDelay: 0.1, model: "qwen/qwen3.8-27b", guard: true, preemptive: false },
};

// ms: [turn detect, LLM first token, TTS to first audio] -> six consecutive synthetic parts
const t = (
  stage: string,
  lead: string,
  omar: string,
  ms: [number, number, number] | null,
  extra: Partial<Turn> = {},
): Omit<Turn, "turn" | "at"> => {
  const tool = extra.toolTurn ? 180 : null;
  const parts = ms
    ? { turnDetectMs: ms[0], commitMs: 60, toolMs: tool, llmMs: ms[1], guardMs: 40, ttsMs: ms[2] }
    : {};
  const total = ms ? Object.values(parts).reduce<number>((a, v) => a + (v ?? 0), 0) : null;
  return {
    stage,
    lead_text: lead,
    omar_text: omar,
    ...parts,
    totalMs: total,
    unexplainedMs: ms ? 0 : null,
    userEndSource: ms ? "words" : "none",
    ttsTtfbMs: ms ? ms[2] - 20 : null,
    ttsRealtimeFactor: ms ? 0.32 : null,
    heardMs: total == null ? null : total + 170,
    toolTurn: Boolean(extra.toolTurn),
    scripted: !ms,
    interrupted: false,
    ...extra,
  };
};

const S = (stage: string, stageLabel: string, patch: Partial<CallSnapshot> = {}) => ({ stage, stageLabel, ...patch });

export const SAMPLE_CALL: Beat[] = [
  { after: 300, kind: "state", patch: S("IDENTITY", "Checking it is the right person"), step: { event: "answered", detail: null, by: "code", stage_after: "IDENTITY" } },
  { after: 600, kind: "turn", turn: t("IDENTITY", "", "Hi, is this Omair?", null) },
  { after: 1400, kind: "state", patch: S("OPENING", "Legal opening given, waiting for 'is now a good time?'", { opening: { companyAndPurpose: true, recordingNotice: true, askedToContinue: true } }), step: { event: "confirm_identity", detail: null, by: "code", stage_after: "OPENING" } },
  { after: 500, kind: "turn", turn: t("IDENTITY", "Yes, speaking.", "Hi Omair, this is Nimra from Hoplon and Co. You filled in a form on our website about a website and maybe an app for your business, so I'm calling with the information you asked for. Just so you know, this call is recorded. Is now a good time for two minutes?", null) },
  { after: 1500, kind: "state", patch: S("INFO", "Getting to know the Lead"), step: { event: "good_time", detail: null, by: "code", stage_after: "INFO" } },
  { after: 500, kind: "turn", turn: t("OPENING", "Sure, go ahead.", "Lovely, thank you. So tell me a bit about the business. What do you do?", [240, 280, 120]) },
  { after: 1600, kind: "state", patch: S("INFO", "Getting to know the Lead", { rapportTurns: 1 }), step: { event: "lead_turn", detail: null, by: "code", stage_after: "INFO" } },
  { after: 400, kind: "turn", turn: t("INFO", "We do corporate catering. Lunches for offices, mostly in Business Bay.", "Oh nice, so you're the reason some offices actually eat well! How do people order from you right now?", [270, 230, 115]) },
  { after: 1600, kind: "state", patch: S("INFO", "Getting to know the Lead", { rapportTurns: 2 }), step: { event: "lead_turn", detail: null, by: "code", stage_after: "INFO" } },
  { after: 400, kind: "turn", turn: t("INFO", "Mostly WhatsApp, honestly. It gets messy on busy days.", "Ha, WhatsApp chaos, I know that feeling. Is it just you handling the orders, or do you ha", [280, 210, 110], { interrupted: true }) },
  { after: 1600, kind: "state", patch: S("INFO", "Getting to know the Lead", { rapportTurns: 3 }), step: { event: "lead_turn", detail: null, by: "code", stage_after: "INFO" } },
  { after: 400, kind: "turn", turn: t("INFO", "Just me on the phone, and two chefs.", "That's a lot on your plate, no pun intended. A simple ordering website could take most of those messages off your hands. What made you reach out now?", [260, 300, 120], { toolTurn: true }) },
  { after: 1600, kind: "state", patch: S("INTENT", "Probing Intent to Buy", { rapportTurns: 4 }), step: { event: "lead_turn", detail: null, by: "code", stage_after: "INTENT" } },
  { after: 400, kind: "turn", turn: t("INFO", "We're getting more clients and I can't keep up.", "That's a good problem to have. Would you like to take it a bit further? My manager could have a relaxed chat with you and shape something around how you work.", [270, 240, 115]) },
  { after: 1500, kind: "state", patch: S("BOOKING_PREF", "Asking for a time preference", { status: "Qualified Lead", guardHits: [{ rule: "no_budget", said: "A simple ordering site usually starts at around AED 15,000.", at: "sample-1" }] }), step: { event: "ask_price", detail: null, by: "llm", stage_after: "BOOKING_PREF" } },
  { after: 500, kind: "turn", turn: t("INTENT", "Sure. Roughly how much are we talking?", "It really depends on what you need, and we can adjust the budget to fit. My manager will go through that with you. Would earlier or later this week suit you, morning or afternoon?", [290, 420, 135], { toolTurn: true }) },
  { after: 1700, kind: "state", patch: S("BOOKING_OFFER", "Offering 2 slots", { offered: ["Wednesday at 3pm", "Thursday at 4:30pm"] }), step: { event: "give_preference", detail: "later this week, afternoon", by: "llm", stage_after: "BOOKING_PREF" } },
  { after: 400, kind: "turn", turn: t("BOOKING_PREF", "Later this week, afternoon.", "I have Wednesday at 3pm or Thursday at 4:30pm. Which suits you better?", [250, 240, 110], { toolTurn: true }) },
  { after: 1500, kind: "state", patch: S("EMAIL_CONFIRM", "Confirming the invite email", { chosen: "Wednesday at 3pm" }), step: { event: "accept_slot", detail: "Wednesday at 3pm", by: "llm", stage_after: "EMAIL_CONFIRM" } },
  { after: 400, kind: "turn", turn: t("BOOKING_OFFER", "Wednesday at three is good.", "Wednesday at 3pm it is. I'll send the invite to the email on your form, the one at example.com. Is that still best?", [260, 300, 120], { toolTurn: true }) },
  { after: 1500, kind: "state", patch: S("ENDED", "Call ended", { status: "Qualified Lead (Discovery Call booked)", outcome: "Discovery Call booked: Wednesday at 3pm. Invite sent.", ended: true, bookingConfirmed: true }), step: { event: "calendar_confirms", detail: null, by: "code", stage_after: "ENDED" } },
  { after: 400, kind: "turn", turn: t("EMAIL_CONFIRM", "Yes, that email is fine.", "One moment while I lock that in. You're booked for Wednesday at 3pm with my manager. The invite with the Google Meet link is on its way. Thanks, Omair!", null, { toolTurn: true }) },
];

function pct(values: number[], p: number): number | null {
  if (!values.length) return null;
  const s = [...values].sort((a, b) => a - b);
  return s[Math.max(1, Math.ceil((p / 100) * s.length)) - 1];
}

function summarise(turns: Turn[]): PartSummary {
  const part = (k: keyof Turn) => {
    const v = turns.map((x) => x[k]).filter((x): x is number => typeof x === "number");
    return { p50: pct(v, 50), p95: pct(v, 95) };
  };
  return {
    n: turns.length,
    turnDetectMs: part("turnDetectMs"),
    commitMs: part("commitMs"),
    toolMs: part("toolMs"),
    llmMs: part("llmMs"),
    guardMs: part("guardMs"),
    ttsMs: part("ttsMs"),
    totalMs: part("totalMs"),
    ttsTtfbMs: part("ttsTtfbMs"),
    ttsRealtimeFactor: part("ttsRealtimeFactor"),
  };
}

export function summary(all: Turn[]): LatencySummary {
  const m = all.filter((x) => x.totalMs !== null && !x.scripted);
  const overall = summarise(m);
  const byStage: Record<string, PartSummary> = {};
  for (const st of [...new Set(m.map((x) => x.stage))]) byStage[st] = summarise(m.filter((x) => x.stage === st));
  const p50 = overall.totalMs.p50;
  const p95 = overall.totalMs.p95;
  return {
    overall,
    byStage,
    toolTurns: summarise(m.filter((x) => x.toolTurn)),
    plainTurns: summarise(m.filter((x) => !x.toolTurn)),
    target: { p50: 900, p95: 1500 },
    pass: p50 === null ? null : p50 <= 900 && (p95 ?? 0) <= 1500,
  };
}

export type SampleHandlers = {
  onState: (s: CallSnapshot) => void;
  onLeadStart: (text: string) => void; // Lead starts talking (or the phone rings)
  onLeadEnd: () => void;
  onReply: (m: LatencyMessage) => void; // Nimra's first audio, after the measured wait
  onOmarEnd: () => void;
  onDone: () => void;
};

// Plays the sample call out loud with the browser's voices. Between the Lead's line and Nimra's
// reply it waits the synthetic total, so the wait is heard as well as seen. Returns a stop function.
export function playSample(h: SampleHandlers, opts: { muted: boolean; speed?: number }): () => void {
  const speed = opts.speed && opts.speed > 0 ? opts.speed : 1;
  const muted = opts.muted || speed !== 1;
  const timers: number[] = [];
  let stopped = false;
  const sleep = (ms: number) => new Promise<void>((r) => timers.push(window.setTimeout(r, ms / speed)));
  const speak = (text: string, who: "omar" | "lead", cutMs?: number) =>
    say(text, who, { muted, timers, cutMs: cutMs === undefined ? (muted ? speechMs(text) / speed : undefined) : cutMs / speed });

  void (async () => {
    let snap: CallSnapshot = { ...BASE };
    const turns: Turn[] = [];
    let pending: Extract<Beat, { kind: "state" }>[] = [];
    const apply = () => {
      for (const beat of pending) {
        const steps = beat.step ? [...snap.steps, { ...beat.step, at: Date.now() / 1000 }] : snap.steps;
        snap = { ...snap, ...beat.patch, steps };
        h.onState(snap);
      }
      pending = [];
    };
    await sleep(400);
    for (const beat of SAMPLE_CALL) {
      if (stopped) return;
      if (beat.kind === "state") {
        pending.push(beat);
        continue;
      }
      const line = beat.turn;
      h.onLeadStart(line.lead_text);
      if (line.lead_text) await speak(line.lead_text, "lead");
      else await sleep(1200);
      if (stopped) return;
      h.onLeadEnd();
      apply();
      await sleep(line.totalMs ?? 450);
      if (stopped) return;
      const turn: Turn = { ...line, turn: turns.length + 1, at: Date.now() / 1000 };
      turns.push(turn);
      h.onReply({ turn, summary: summary(turns) });
      const ms = speechMs(line.omar_text);
      await speak(line.omar_text, "omar", line.interrupted ? ms * 0.72 : undefined);
      if (stopped) return;
      h.onOmarEnd();
      await sleep(300);
    }
    apply();
    if (!stopped) h.onDone();
  })();

  return () => {
    stopped = true;
    timers.forEach((id) => window.clearTimeout(id));
    stopSpeech();
  };
}

// The sample call's turns and summary without playing it, for a labelled preview.
export function samplePreview(): { turns: Turn[]; summary: LatencySummary } {
  const turns = SAMPLE_CALL.flatMap((b) => (b.kind === "turn" ? [b.turn] : [])).map(
    (t, i) => ({ ...t, turn: i + 1, at: 0 }) as Turn,
  );
  return { turns, summary: summary(turns) };
}
