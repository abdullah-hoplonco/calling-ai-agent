// The recorded sample call for the Horizon view: Uzair (ElevenLabs v4, our custom voice)
// calls Sara, a café owner. Synthetic people and data. It plays the voices only, measures
// them for the equaliser and follows each word and audio tag from the ElevenLabs timings.

const BASE = "/horizon";
const GAP = 0.45; // seconds between turns, like a real conversation

export type SampleWord = { text: string; t: number };
export type SampleLine = {
  i: number;
  who: "agent" | "lead";
  file: string;
  duration: number;
  chars: string[];
  starts: number[];
  words: SampleWord[];
  cues: { tag: string; t: number }[];
  at: number;
};

export type SampleState = {
  started: boolean;
  ended: boolean;
  who: "agent" | "lead" | null;
  lineIndex: number;
  wordIndex: number;
  level: { agent: number; lead: number };
  bands: Float32Array;
};

type Events = {
  line?: (line: SampleLine, index: number) => void;
  word?: (index: number) => void;
  pause?: () => void;
  tag?: (tag: string) => void;
  end?: () => void;
};

function split(chars: string[], starts: number[]) {
  const words: SampleWord[] = [];
  const cues: { tag: string; t: number }[] = [];
  let i = 0, word = "", start: number | null = null;
  const flush = () => {
    if (word.trim()) words.push({ text: word.trim(), t: start ?? 0 });
    word = "";
    start = null;
  };
  while (i < chars.length) {
    if (chars[i] === "[") {
      flush();
      let j = i + 1, tag = "";
      while (j < chars.length && chars[j] !== "]") tag += chars[j++];
      cues.push({ tag: tag.trim().toLowerCase(), t: starts[i] ?? 0 });
      i = j + 1;
      continue;
    }
    if (/\s/.test(chars[i]!)) {
      flush();
      i++;
      continue;
    }
    if (start === null) start = starts[i] ?? 0;
    word += chars[i++];
  }
  flush();
  return { words, cues };
}

export class SampleCall {
  lines: SampleLine[] = [];
  total = 0;
  state: SampleState = { started: false, ended: false, who: null, lineIndex: -1, wordIndex: -1, level: { agent: 0, lead: 0 }, bands: new Float32Array(32) };
  private ctx: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private sources: AudioBufferSourceNode[] = [];
  private t0 = 0;
  private emotion = "";
  private timeBuf = new Float32Array(1024);
  private freqBuf = new Uint8Array(512);

  constructor(private on: Events) {}

  async load(): Promise<this> {
    const res = await fetch(`${BASE}/timeline.json`);
    if (!res.ok) throw new Error(`The sample call could not load (${res.status}).`);
    const raw = (await res.json()) as Omit<SampleLine, "words" | "cues" | "at">[];
    let at = 0.8;
    this.lines = raw.map((l) => {
      const line = { ...l, ...split(l.chars, l.starts), at };
      at += l.duration + GAP;
      return line;
    });
    this.total = at;
    return this;
  }

  /** Call from a click: browsers only start audio after a user gesture. */
  async start(): Promise<void> {
    const ctx = (this.ctx = new AudioContext());
    if (ctx.state === "suspended") await ctx.resume().catch(() => {});
    const out = ctx.createGain();
    out.connect(ctx.destination);
    this.analyser = ctx.createAnalyser();
    this.analyser.fftSize = 1024;
    this.analyser.smoothingTimeConstant = 0.6;
    out.connect(this.analyser);
    const buffers = await Promise.all(
      this.lines.map(async (l) => ctx.decodeAudioData(await (await fetch(`${BASE}/${l.file.replace(/^audio\//, "")}`)).arrayBuffer())),
    );
    this.t0 = ctx.currentTime + 0.1;
    this.sources = this.lines.map((l, i) => {
      const src = ctx.createBufferSource();
      src.buffer = buffers[i]!;
      src.connect(out);
      src.start(this.t0 + l.at);
      return src;
    });
    this.state.started = true;
  }

  stop(): void {
    for (const s of this.sources) {
      try {
        s.stop();
      } catch {
        /* not started */
      }
    }
    this.sources = [];
    void this.ctx?.close().catch(() => {});
    this.ctx = null;
    this.state.who = null;
    this.state.level.agent = this.state.level.lead = 0;
    this.state.bands.fill(0);
  }

  /** Call every animation frame. */
  tick(): SampleState {
    const s = this.state;
    if (!s.started || !this.ctx || !this.analyser) return s;
    const t = this.ctx.currentTime - this.t0;
    let idx = -1;
    this.lines.forEach((l, i) => {
      if (t >= l.at && t < l.at + l.duration + 0.15) idx = i;
    });
    if (idx !== s.lineIndex && (idx >= 0 || s.who)) {
      if (idx >= 0) {
        const l = this.lines[idx]!;
        s.lineIndex = idx;
        s.who = l.who;
        s.wordIndex = -1;
        this.on.line?.(l, idx);
      } else {
        s.who = null;
        this.on.pause?.();
      }
    }
    if (idx >= 0) {
      const l = this.lines[idx]!;
      const lt = t - l.at;
      let w = -1;
      l.words.forEach((x, i) => {
        if (x.t <= lt) w = i;
      });
      if (w !== s.wordIndex) {
        s.wordIndex = w;
        if (w >= 0) this.on.word?.(w);
      }
      let cue: string | null = null;
      for (const c of l.cues) if (c.t <= lt + 0.05) cue = c.tag;
      if (cue && cue !== this.emotion) {
        this.emotion = cue;
        this.on.tag?.(cue);
      }
    }
    if (!s.ended && t > this.total) {
      s.ended = true;
      s.who = null;
      this.on.end?.();
    }
    // loudness of whoever speaks and 32 log bands
    this.analyser.getFloatTimeDomainData(this.timeBuf);
    let sum = 0;
    for (const v of this.timeBuf) sum += v * v;
    const rms = Math.min(1, Math.sqrt(sum / this.timeBuf.length) * 5.5);
    for (const k of ["agent", "lead"] as const) {
      const target = s.who === k ? rms : 0;
      s.level[k] += (target - s.level[k]) * (target > s.level[k] ? 0.5 : 0.08);
    }
    readBands(this.analyser, this.freqBuf, s.bands);
    return s;
  }
}

/** 32 log-spaced bands from an analyser, smoothed into `bands` (0..1). */
export function readBands(analyser: AnalyserNode, buf: Uint8Array, bands: Float32Array): void {
  analyser.getByteFrequencyData(buf as Uint8Array<ArrayBuffer>);
  const n = buf.length;
  for (let b = 0; b < 32; b++) {
    const lo = Math.floor(Math.pow(n, b / 32));
    const hi = Math.max(lo + 1, Math.floor(Math.pow(n, (b + 1) / 32)));
    let m = 0;
    for (let i = lo; i < hi; i++) m = Math.max(m, buf[i] ?? 0);
    bands[b]! += (m / 255 - bands[b]!) * 0.35;
  }
}
