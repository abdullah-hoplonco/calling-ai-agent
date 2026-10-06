import { AccessToken, RoomAgentDispatch, RoomConfiguration } from "livekit-server-sdk";
import { NextResponse } from "next/server";

import { LEADS, leadMetadata } from "@/lib/leads";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

// Makes a one-call room and a token that dispatches Omar into it with the Lead's details.
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

  const body = (await req.json().catch(() => ({}))) as { leadId?: string; old?: boolean };
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
          metadata: JSON.stringify(leadMetadata(lead, Boolean(body.old))),
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
