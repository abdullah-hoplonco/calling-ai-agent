// Reads loudness and 32 frequency bands from live call audio (the agent's track and your
// microphone) for the Horizon equaliser. It only listens: nothing is sent or recorded.

import { readBands } from "@/lib/horizon/sample";

export type Tap = { read: (bands: Float32Array) => number; close: () => void };

export function createTap(ctx: AudioContext, track: MediaStreamTrack): Tap {
  const src = ctx.createMediaStreamSource(new MediaStream([track]));
  const analyser = ctx.createAnalyser();
  analyser.fftSize = 1024;
  analyser.smoothingTimeConstant = 0.6;
  src.connect(analyser); // not connected to the speakers: LiveKit already plays the call
  const time = new Float32Array(analyser.fftSize);
  const freq = new Uint8Array(analyser.frequencyBinCount);
  return {
    read(bands) {
      analyser.getFloatTimeDomainData(time);
      let sum = 0;
      for (const v of time) sum += v * v;
      readBands(analyser, freq, bands);
      return Math.min(1, Math.sqrt(sum / time.length) * 5.5);
    },
    close() {
      src.disconnect();
      analyser.disconnect();
    },
  };
}
