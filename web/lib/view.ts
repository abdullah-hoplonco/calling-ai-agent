// Small helpers that every theme uses to read a call the same way.

import { EVENT_WORDS, RULE_WORDS, STAGE_NAME, TRACK, trackIndex } from "@/lib/stages";
import type { Step, Turn } from "@/lib/types";

export const TARGET_MS = 900;
export const SLOW_MS = 1500;

// Consecutive parts on one clock: they add up to the total (voice/src/omar_voice/timing.py).
export const PARTS = [
  { key: "turnDetectMs", label: "Turn detect", hint: "Your last word to the final transcript", cls: "detect" },
  { key: "commitMs", label: "Commit", hint: "Transcript to turn committed", cls: "commit" },
  { key: "toolMs", label: "Tool step", hint: "Extra LLM request before the reply", cls: "tool" },
  { key: "llmMs", label: "LLM first token", hint: "Reply request to first token", cls: "llm" },
  { key: "guardMs", label: "Guard", hint: "First token to first checked sentence", cls: "guard" },
  { key: "ttsMs", label: "Voice (TTS)", hint: "Sentence to Nimra's first audio", cls: "tts" },
] as const;

export type PartKey = (typeof PARTS)[number]["key"];
export type Part = (typeof PARTS)[number] & { ms: number };

export function partsOf(turn: Turn): Part[] {
  return PARTS.filter((p) => turn[p.key] != null).map((p) => ({ ...p, ms: Math.round(turn[p.key] ?? 0) }));
}

export type Tone = "good" | "warn" | "crit";
export function tone(ms: number | null | undefined): Tone | undefined {
  if (ms == null) return undefined;
  if (ms <= TARGET_MS) return "good";
  if (ms <= SLOW_MS) return "warn";
  return "crit";
}

export function toneWord(t: Tone | undefined): string {
  return t === "good" ? "Within target" : t === "warn" ? "Over 0.9 s" : t === "crit" ? "Over 1.5 s" : "Not measured";
}

export const ms = (v: number | null | undefined) => (v == null ? "–" : `${Math.round(v).toLocaleString("en-US")} ms`);
export const sec = (v: number | null | undefined, d = 2) => (v == null ? "–" : `${(v / 1000).toFixed(d)} s`);
export const num = (v: number | null | undefined) => (v == null ? "–" : Math.round(v).toLocaleString("en-US"));

export function clock(v: number): string {
  const s = Math.max(0, Math.floor(v / 1000));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export function timecode(v: number): string {
  const t = Math.max(0, v);
  const m = Math.floor(t / 60000);
  const s = Math.floor(t / 1000) % 60;
  const f = Math.floor(t % 1000);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}.${String(f).padStart(3, "0")}`;
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter((w) => /^[A-Za-z]/.test(w))
    .slice(0, 2)
    .map((w) => w[0]!.toUpperCase())
    .join("");
}

export const stageName = (s: string | undefined) => (s ? (STAGE_NAME[s] ?? s) : "");
export const trackOf = (s: string | undefined) => TRACK[trackIndex(s)] ?? null;
export const stepWord = (s: Step) =>
  `${EVENT_WORDS[s.event] ?? s.event}${s.detail && s.event !== "slots_found" ? `: ${s.detail}` : ""}`;
export const ruleWord = (r: string) => RULE_WORDS[r] ?? r;

export function percentile(values: number[], p: number): number | null {
  if (!values.length) return null;
  const s = [...values].sort((a, b) => a - b);
  return s[Math.max(1, Math.ceil((p / 100) * s.length)) - 1]!;
}
