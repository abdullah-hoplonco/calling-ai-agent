import { AccessToken, RoomAgentDispatch, RoomConfiguration } from "livekit-server-sdk";
import { NextResponse } from "next/server";

import { LEADS, type LlmChoice, leadMetadata } from "@/lib/leads";
import { VOICES } from "@/lib/voices";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

// Makes a one-call room and a token that dispatches Nimra into it with the Lead's details.
export async function POST(req: Request) {
  const { LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET } = process.env;
  const missing = Object.entries({ LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET })
    .filter(([, v]) => !v)
    .map(([k]) => k);
  if (missing.length) {
    return NextResponse.json(
      { error: `${missing.join(", ")} not set. Add the LiveKit keys to the .env file in the repo root.` },
      { status: 503 },
    );
  }

  const body = (await req.json().catch(() => ({}))) as {
    leadId?: string;
    old?: boolean;
    llm?: string;
    voice?: string;
    stability?: number;
    lang?: string;
  };
  const voice = VOICES.find((v) => v.id === body.voice)?.id;
  // ElevenLabs stability 0..1 (lower = more emotion); anything else is ignored
  const stability =
    typeof body.stability === "number" && body.stability >= 0 && body.stability <= 1
      ? Math.round(body.stability * 100) / 100
      : undefined;
  const llm: LlmChoice = body.llm === "groq" || body.llm === "deepseek" ? body.llm : "auto";
  const lang = body.lang === "hi" ? "hi" : "en";
  const lead = LEADS.find((l) => l.id === body.leadId) ?? LEADS[0];
  const agentName = process.env.OMAR_AGENT_NAME ?? "omar";
  const roomName = `omar-${lead.id}-${Date.now().toString(36)}`;
  const identity = `lead-${Math.random().toString(36).slice(2, 8)}`;

  const at = new AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET, {
    identity,
    name: lead.name,
    ttl: "15m",
  });
  at.addGrant({ room: roomName, roomJoin: true, canPublish: true, canSubscribe: true, canPublishData: true });
  if (agentName) {
    at.roomConfig = new RoomConfiguration({
      agents: [
        new RoomAgentDispatch({
          agentName,
          metadata: JSON.stringify(leadMetadata(lead, Boolean(body.old), llm, voice, stability, lang)),
        }),
      ],
    });
  }

  return NextResponse.json({
    serverUrl: LIVEKIT_URL,
    participantToken: await at.toJwt(),
    roomName,
  });
}
