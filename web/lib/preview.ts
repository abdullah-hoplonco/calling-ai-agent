// A still model of the sample call, laid out on its spoken timings, so a page can show
// what a call looks like before anyone presses play. Always labelled synthetic on screen.

import { samplePreview } from "@/lib/replay";
import { speechMs } from "@/lib/speech";
import type { CallModel, TurnView } from "@/lib/useCall";

let cache: { turns: TurnView[]; length: number; summary: ReturnType<typeof samplePreview>["summary"] } | null = null;

function build() {
  const { turns, summary } = samplePreview();
  let t = 400;
  const views: TurnView[] = turns.map((turn) => {
    const leadAt = t;
    const leadEnd = leadAt + (turn.lead_text ? speechMs(turn.lead_text) : 1200);
    const omarAt = leadEnd + (turn.totalMs ?? 450);
    const omarEnd = omarAt + speechMs(turn.omar_text) * (turn.interrupted ? 0.72 : 1);
    t = omarEnd + 300;
    return {
      turn,
      steps: [],
      leadAt: turn.lead_text ? leadAt : null,
      leadEnd: turn.lead_text ? leadEnd : null,
      omarAt,
      omarEnd,
      heardMs: null,
      fresh: false,
    };
  });
  return { turns: views, length: t, summary };
}

export function previewModel(c: CallModel): CallModel {
  cache ??= build();
  return {
    ...c,
    turns: cache.turns,
    measured: cache.turns.filter((v) => v.turn.totalMs != null),
    summary: cache.summary,
    length: cache.length,
  };
}
