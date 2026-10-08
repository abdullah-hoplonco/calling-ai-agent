// Groq vs DeepSeek across your calls, kept in THIS browser only (localStorage).
// One entry per measured reply. Used to compare the two LLMs on real calls.

import type { Turn } from "@/lib/types";

const KEY = "omar.llmHistory.v1";
const MAX = 600;

export type LlmSample = {
  at: number;
  provider: string;
  model: string;
  llmMs: number | null; // reply request -> first token
  totalMs: number | null; // Lead's last word -> agent's first audio
  costUsd: number;
  tool: boolean;
};

export function loadHistory(): LlmSample[] {
  try {
    const raw = window.localStorage.getItem(KEY);
    const v = raw ? (JSON.parse(raw) as LlmSample[]) : [];
    return Array.isArray(v) ? v : [];
  } catch {
    return [];
  }
}

export function saveCall(turns: Turn[]): LlmSample[] {
  const rows: LlmSample[] = turns
    .filter((t) => t.totalMs != null && !t.scripted && t.llmProvider)
    .map((t) => ({
      at: Date.now(),
      provider: t.llmProvider as string,
      model: t.llmModel ?? "",
      llmMs: t.llmMs ?? null,
      totalMs: t.totalMs,
      costUsd: t.llmCostUsd ?? 0,
      tool: Boolean(t.toolTurn),
    }));
  const all = [...loadHistory(), ...rows].slice(-MAX);
  try {
    window.localStorage.setItem(KEY, JSON.stringify(all));
  } catch {
    /* storage blocked: the comparison simply stays empty */
  }
  return all;
}

export function clearHistory(): void {
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    /* storage blocked */
  }
}

const pct = (v: number[], p: number) => {
  if (!v.length) return null;
  const s = [...v].sort((a, b) => a - b);
  return s[Math.max(1, Math.ceil((p / 100) * s.length)) - 1]!;
};

export type ProviderStats = {
  provider: string;
  model: string;
  replies: number;
  llmP50: number | null;
  llmP95: number | null;
  totalP50: number | null;
  totalP95: number | null;
  costPerReply: number;
};

export function compare(samples: LlmSample[]): ProviderStats[] {
  const by = new Map<string, LlmSample[]>();
  for (const s of samples) by.set(s.provider, [...(by.get(s.provider) ?? []), s]);
  return [...by.entries()].map(([provider, list]) => {
    const llm = list.map((s) => s.llmMs).filter((x): x is number => x != null);
    const tot = list.map((s) => s.totalMs).filter((x): x is number => x != null);
    return {
      provider,
      model: list[list.length - 1]!.model,
      replies: list.length,
      llmP50: pct(llm, 50),
      llmP95: pct(llm, 95),
      totalP50: pct(tot, 50),
      totalP95: pct(tot, 95),
      costPerReply: list.reduce((a, s) => a + s.costUsd, 0) / list.length,
    };
  });
}
