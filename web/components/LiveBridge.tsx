"use client";

// Feeds a live LiveKit call into the call model: worker data messages, Omar's state,
// audio levels and the network numbers for "heard" delay. Renders nothing.

import { useDataChannel, useLocalParticipant, useTrackVolume, useVoiceAssistant } from "@livekit/components-react";
import type { LocalAudioTrack } from "livekit-client";
import { useEffect } from "react";

import { levels } from "@/lib/levels";
import type { CallModel } from "@/lib/useCall";

const decoder = new TextDecoder();

export function LiveBridge({ c }: { c: CallModel }) {
  const { onState, onLatency, onAgentState, onMicLevel, onNet } = c;
  useDataChannel("omar.state", (msg) => onState(JSON.parse(decoder.decode(msg.payload))));
  useDataChannel("omar.latency", (msg) => onLatency(JSON.parse(decoder.decode(msg.payload))));

  const { state, audioTrack } = useVoiceAssistant();
  const { microphoneTrack } = useLocalParticipant();
  const mic = useTrackVolume(microphoneTrack?.track as LocalAudioTrack | undefined);
  const omar = useTrackVolume(audioTrack);

  useEffect(() => onAgentState(state), [state, onAgentState]);
  useEffect(() => {
    levels.lead = mic;
    onMicLevel(mic);
  }, [mic, onMicLevel]);
  useEffect(() => {
    levels.omar = omar;
  }, [omar]);

  // Network between this browser and LiveKit for Omar's audio, from WebRTC statistics:
  // round-trip time of the selected connection and the average jitter-buffer delay.
  const track = audioTrack?.publication?.track;
  useEffect(() => {
    if (!track) return;
    let last = { delay: 0, count: 0 };
    const read = async () => {
      const report = await track.getRTCStatsReport?.();
      if (!report) return;
      let rtt: number | null = null;
      let jitter: number | null = null;
      report.forEach((st: Record<string, unknown>) => {
        if (st.type === "candidate-pair" && st.state === "succeeded" && typeof st.currentRoundTripTime === "number") {
          rtt = st.currentRoundTripTime * 1000;
        }
        if (st.type === "inbound-rtp" && st.kind === "audio") {
          const delay = Number(st.jitterBufferDelay ?? 0);
          const count = Number(st.jitterBufferEmittedCount ?? 0);
          if (count > last.count) jitter = ((delay - last.delay) / (count - last.count)) * 1000;
          last = { delay, count };
        }
      });
      if (rtt !== null) onNet({ rttMs: Math.round(rtt), jitterMs: Math.round(jitter ?? 0) });
    };
    void read();
    const id = window.setInterval(read, 2000);
    return () => window.clearInterval(id);
  }, [track, onNet]);

  return null;
}
