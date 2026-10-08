// Voices for the agent. The worker accepts only these IDs (voice/src/omar_voice/voices.py).
// Choosing a voice chooses its TTS engine. Female voices introduce themselves as Nimra; male as Hamza.
// "emotive": voices that follow mood tags most strongly (most alive on a call).

export type VoiceEngine = "elevenlabs" | "cartesia";

export type VoiceOption = {
  id: string;
  name: string;
  desc: string;
  agent: "Nimra" | "Hamza";
  engine: VoiceEngine;
  top?: boolean;
  emotive?: boolean;
  paid?: boolean; // ElevenLabs library voice: needs a paid plan (else Jessica speaks)
};

export const ENGINE_LABEL: Record<VoiceEngine, string> = {
  elevenlabs: "ElevenLabs · v4 Turbo",
  cartesia: "Cartesia · Sonic-3",
};

export const VOICES: VoiceOption[] = [
  { id: "cgSgspJ2msm6clMCkdW9", name: "Jessica", desc: "Playful, warm female · free plan", agent: "Nimra", engine: "elevenlabs" },
  { id: "4O1sYUnmtThcBoSBrri7", name: "Maya", desc: "Indian female, cheerful", agent: "Nimra", engine: "elevenlabs", paid: true },
  { id: "56AoDkrOh6qfVPDXZ7Pt", name: "Cassidy", desc: "American female, engaging", agent: "Nimra", engine: "elevenlabs", paid: true },
  { id: "1qEiC6qsybMkmnNdVMbK", name: "Monika", desc: "Indian female, natural", agent: "Nimra", engine: "elevenlabs", paid: true, top: true },
  { id: "6ccbfb76-1fc6-48f7-b71d-91ac6298247b", name: "Tessa", desc: "Warm female", agent: "Nimra", engine: "cartesia", emotive: true },
  { id: "cbaf8084-f009-4838-a096-07ee2e6612b1", name: "Maya", desc: "Easygoing female", agent: "Nimra", engine: "cartesia", emotive: true },
  { id: "0834f3df-e650-4766-a20c-5a93a43aa6e3", name: "Leo", desc: "Warm male", agent: "Hamza", engine: "cartesia", emotive: true },
  { id: "c961b81c-a935-4c17-bfb3-ba2239de8c2f", name: "Kyle", desc: "Friendly male", agent: "Hamza", engine: "cartesia", emotive: true },
  { id: "f8f5f1b2-f02d-4d8e-a40d-fd850a487b3d", name: "Kiara", desc: "Indian female, upbeat", agent: "Nimra", engine: "cartesia" },
  { id: "db408a93-859c-4a0a-b6a2-220c074cc90d", name: "Hana", desc: "Neutral female, easygoing", agent: "Nimra", engine: "cartesia" },
  { id: "8d8ce8c9-44a4-46c4-b10f-9a927b99a853", name: "Connie", desc: "Neutral female, cheery", agent: "Nimra", engine: "cartesia" },
  { id: "f6141af3-5f94-418c-80ed-a45d450e7e2e", name: "Priya", desc: "Indian female", agent: "Nimra", engine: "cartesia" },
  { id: "1259b7e3-cb8a-43df-9446-30971a46b8b0", name: "Devansh", desc: "Indian male", agent: "Hamza", engine: "cartesia" },
  { id: "62ae83ad-4f6a-430b-af41-a9bede9286ca", name: "Gemma", desc: "British female", agent: "Nimra", engine: "cartesia" },
  { id: "ef191366-f52f-447a-a398-ed8c0f2943a1", name: "Archie", desc: "British male", agent: "Hamza", engine: "cartesia" },
];

// Jessica (ElevenLabs premade): works on the free plan. Same as ELEVEN_VOICE_ID on the worker.
export const DEFAULT_VOICE = "1qEiC6qsybMkmnNdVMbK"; // Monika (ElevenLabs, paid plan)

// ElevenLabs stability (0-1): lower = more emotion, higher = steadier. Same default as ELEVEN_STABILITY.
export const DEFAULT_STABILITY = 0.3;
