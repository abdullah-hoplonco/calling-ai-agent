// Messages from the voice worker (voice/src/omar_voice/agent.py).

export type Step = {
  at: number;
  event: string;
  detail: string | null;
  by: "llm" | "code";
  stage_after: string;
};

export type GuardHit = { rule: string; said: string; at: string };

export type CallSnapshot = {
  stage: string;
  stageLabel: string;
  status: string;
  outcome: string | null;
  ended: boolean;
  rapportTurns: number;
  minRapportTurns: number;
  objections: number;
  maxObjections: number;
  offered: string[];
  chosen: string | null;
  bookingConfirmed: boolean;
  aiDisclosed: boolean;
  opening: { companyAndPurpose: boolean; recordingNotice: boolean; askedToContinue: boolean };
  steps: Step[];
  guardHits?: GuardHit[];
  config?: {
    turnMode: "flux" | "livekit";
    minDelay: number;
    model: string;
    guard: boolean;
    preemptive: boolean;
  };
};

export type Turn = {
  turn: number;
  stage: string;
  at: number;
  lead_text: string;
  omar_text: string;
  // one clock, from the end of the Lead's last word (voice/src/omar_voice/timing.py)
  turnDetectMs?: number | null; // last word ends -> final transcript (Flux end-of-turn wait)
  commitMs?: number | null; // final transcript -> turn committed (endpointing, framework)
  toolMs?: number | null; // tool step before the reply (extra LLM request)
  llmMs?: number | null; // reply request -> first token
  guardMs?: number | null; // first token -> first full sentence handed to TTS
  ttsMs?: number | null; // first sentence -> Omar's first audio frame
  totalMs: number | null; // last word ends -> Omar's first audio frame (worker)
  serverTotalMs?: number | null;
  unexplainedMs?: number | null; // total minus the parts; near 0 when all marks exist
  userEndSource?: "audio" | "words" | "window" | "livekit" | "none";
  ttsTtfbMs?: number | null;
  ttsRealtimeFactor?: number | null; // TTS generation time / audio length; above 1 = choppy
  llmRequests?: number;
  toolTurn?: boolean;
  scripted: boolean;
  interrupted: boolean;
  heardMs?: number | null; // browser: your voice ends -> Omar's voice heard (mouth to ear)
};

type Pct = { p50: number | null; p95: number | null };
export type PartSummary = {
  n: number;
  turnDetectMs: Pct;
  commitMs: Pct;
  toolMs: Pct;
  llmMs: Pct;
  guardMs: Pct;
  ttsMs: Pct;
  totalMs: Pct;
  ttsTtfbMs: Pct;
  ttsRealtimeFactor: Pct;
};

export type LatencySummary = {
  overall: PartSummary;
  byStage: Record<string, PartSummary>;
  toolTurns: PartSummary;
  plainTurns: PartSummary;
  scriptedTurns?: PartSummary;
  target: { p50: number; p95: number };
  pass: boolean | null;
};

export type LatencyMessage = { turn: Turn; summary: LatencySummary };
