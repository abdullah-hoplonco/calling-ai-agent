// Browser voices for the spoken sample call. Live calls use Omar's real voice from LiveKit.

type Voices = { omar: SpeechSynthesisVoice | null; lead: SpeechSynthesisVoice | null };

let voices: Voices = { omar: null, lead: null };

function pick() {
  if (typeof window === "undefined" || !window.speechSynthesis) return;
  const en = window.speechSynthesis.getVoices().filter((v) => /^en/i.test(v.lang));
  const omar =
    en.find((v) => /Daniel|UK English Male|Arthur|Oliver|George|Ryan/i.test(v.name)) ??
    en.find((v) => /GB/i.test(v.lang)) ??
    en[0] ??
    null;
  const lead =
    en.find((v) => v !== omar && /Rishi|Aaron|Fred|Alex|Tom|Reed|US English|Eddy/i.test(v.name)) ??
    en.find((v) => v !== omar && !/GB/i.test(v.lang)) ??
    en.find((v) => v !== omar) ??
    omar;
  voices = { omar, lead };
}

if (typeof window !== "undefined" && window.speechSynthesis) {
  pick();
  window.speechSynthesis.addEventListener?.("voiceschanged", pick);
}

// About how long a line takes to say, for timers and region sizes.
export function speechMs(text: string): number {
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  return words ? Math.round(words * 330 + 350) : 0;
}

export function stopSpeech() {
  if (typeof window !== "undefined") window.speechSynthesis?.cancel();
}

// Speaks a line and resolves when it ends. cutMs stops it early (an interrupted line).
export function say(
  text: string,
  who: "omar" | "lead",
  opts: { muted: boolean; cutMs?: number; timers: number[] },
): Promise<void> {
  return new Promise((resolve) => {
    let done = false;
    const finish = () => {
      if (!done) {
        done = true;
        resolve();
      }
    };
    const est = speechMs(text);
    const synth = typeof window !== "undefined" ? window.speechSynthesis : undefined;
    if (opts.muted || !synth || !voices[who]) {
      opts.timers.push(window.setTimeout(finish, opts.cutMs ?? est));
      return;
    }
    const u = new SpeechSynthesisUtterance(text);
    const v = voices[who]!;
    u.voice = v;
    u.lang = v.lang;
    u.rate = who === "omar" ? 1.04 : 1.08;
    u.pitch = who === "omar" ? 0.95 : 1.05;
    u.onend = finish;
    u.onerror = finish;
    synth.speak(u);
    opts.timers.push(
      window.setTimeout(
        () => {
          synth.cancel();
          finish();
        },
        opts.cutMs ?? est * 1.8 + 2500,
      ),
    );
  });
}
