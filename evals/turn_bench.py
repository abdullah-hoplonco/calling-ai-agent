"""Turn-taking test: a bot Lead speaks to Nimra over a real LiveKit call and times each reply.

The bot knows exactly when its own voice stops, so "reply gap" is ground truth:
the end of the Lead's last sound -> the first sound of Nimra's reply, as the Lead hears it.
It also counts cut-ins: Nimra starting to talk while the Lead is still talking
(some lines have a pause in the middle, to tempt an early end of turn).

Each call uses one turn preset (omar_voice.settings.TURN_PRESETS). Modes are interleaved,
so a slow minute on the network hits every mode alike.

Run a local worker first (Deepgram Aura voice: no ElevenLabs credits; Groq only):
    OMAR_AGENT_NAME=omar-bench TTS_ENGINE=deepgram LLM_PROVIDER=groq uv run omar-agent dev
then:
    uv run python evals/turn_bench.py --modes flux,flux-eager,livekit-v1 --calls 2

Results: voice/logs/bench/<time>.jsonl (one row per Lead turn) and a summary on stdout.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import os
import statistics
import time
from dataclasses import asdict, dataclass, field
from typing import Any

import aiohttp
import numpy as np
from livekit import api, rtc

from omar_core import DEFAULT_LEAD
from omar_voice.settings import REPO_ROOT, TURN_PRESETS

RATE = 48000
FRAME = RATE // 100  # 10 ms
VOICE_DBFS = -42.0
LEAD_VOICE = "aura-2-apollo-en"
OUT_DIR = REPO_ROOT / "voice" / "logs" / "bench"
AUDIO_DIR = REPO_ROOT / "voice" / "logs" / "bench-audio"

# One happy-path call. A float is a pause (s) inside the same Lead turn.
SCRIPT: list[list[str | float]] = [
    ["Yes, speaking."],
    ["Sure, go ahead."],
    ["We have four laundry shops,", 0.8, "and people keep calling to book pickups."],
    ["Mostly regular customers. They want to book and pay by card."],
    ["Hmm,", 0.7, "yes, we want to do this soon."],
    ["Later this week, afternoon is best."],
    ["The first one works."],
    ["Yes, that email is fine."],
]

# The same call in everyday Hindi (--lang hi). Lead audio: ElevenLabs, a male voice.
SCRIPT_HI: list[list[str | float]] = [
    ["जी, बोल रहा हूँ।"],
    ["हाँ जी, बताइए।"],
    ["हमारी चार laundry shops हैं,", 0.8, "और लोग pickup book करने के लिए बहुत call करते हैं।"],
    ["ज़्यादातर पुराने customers हैं। वो book करके card से pay करना चाहते हैं।"],
    ["हम्म,", 0.7, "हाँ, हम ये जल्दी करना चाहते हैं।"],
    ["इस हफ़्ते बाद में, दोपहर में ठीक रहेगा।"],
    ["पहला वाला ठीक है।"],
    ["हाँ, वो email ठीक है।"],
]
LEAD_VOICE_HI = "pNInz6obpgDQGcFmaJgB"  # ElevenLabs "Adam" (premade, male)


def _dbfs(samples: np.ndarray) -> float:
    if samples.size == 0:
        return -120.0
    rms = float(np.sqrt(np.mean(np.square(samples.astype(np.float32))))) / 32768.0
    return 20 * math.log10(max(rms, 1e-6))


def _trim(pcm: np.ndarray) -> np.ndarray:
    """Cut leading and trailing silence, so the clip ends on the last sound."""
    voiced = [i for i in range(0, len(pcm), FRAME) if _dbfs(pcm[i : i + FRAME]) > VOICE_DBFS]
    if not voiced:
        return pcm
    return pcm[voiced[0] : voiced[-1] + FRAME]


async def lead_audio_hi(http: aiohttp.ClientSession, text: str) -> np.ndarray:
    """Hindi Lead words as 48 kHz mono PCM (ElevenLabs v4 turbo at 24 kHz, upsampled)."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    path = AUDIO_DIR / f"{hashlib.sha1(f'{LEAD_VOICE_HI}|{text}'.encode()).hexdigest()[:16]}.pcm"
    if not path.exists():
        async with http.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{LEAD_VOICE_HI}",
            params={"output_format": "pcm_24000"},
            headers={"xi-api-key": os.environ["ELEVEN_API_KEY"]},
            json={"text": text, "model_id": "eleven_v4_turbo"},
        ) as r:
            r.raise_for_status()
            pcm24 = np.frombuffer(await r.read(), dtype=np.int16).astype(np.float32)
        x = np.arange(len(pcm24) * 2) / 2
        pcm48 = np.interp(x, np.arange(len(pcm24)), pcm24).astype(np.int16)
        path.write_bytes(pcm48.tobytes())
    return _trim(np.frombuffer(path.read_bytes(), dtype=np.int16))


async def lead_audio(http: aiohttp.ClientSession, text: str) -> np.ndarray:
    """The Lead's words as 48 kHz mono PCM (Deepgram Aura), cached on disk."""
    if any("\u0900" <= ch <= "\u097f" for ch in text):
        return await lead_audio_hi(http, text)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    path = AUDIO_DIR / f"{hashlib.sha1(f'{LEAD_VOICE}|{text}'.encode()).hexdigest()[:16]}.pcm"
    if not path.exists():
        async with http.post(
            "https://api.deepgram.com/v1/speak",
            params={
                "model": LEAD_VOICE,
                "encoding": "linear16",
                "sample_rate": str(RATE),
                "container": "none",
            },
            headers={"Authorization": f"Token {os.environ['DEEPGRAM_API_KEY']}"},
            json={"text": text},
        ) as r:
            r.raise_for_status()
            path.write_bytes(await r.read())
    return _trim(np.frombuffer(path.read_bytes(), dtype=np.int16))


@dataclass
class Turn:
    mode: str
    call: int
    line: int
    text: str
    reply_gap_ms: float | None = None  # Lead's last sound -> Nimra's first sound
    cut_in: bool = False  # Nimra spoke while the Lead was still speaking
    no_reply: bool = False
    server: dict[str, Any] = field(default_factory=dict)  # the agent's own breakdown


class LeadBot:
    def __init__(self) -> None:
        self.room = rtc.Room()
        self.source = rtc.AudioSource(RATE, 1, queue_size_ms=60)
        self.queue: asyncio.Queue[np.ndarray | asyncio.Event] = asyncio.Queue()
        self.voice_times: list[float] = []  # wall time of each voiced frame from Nimra
        self.rows: list[dict[str, Any]] = []
        self.agent_left = asyncio.Event()
        self._tasks: list[asyncio.Task[Any]] = []

    async def start(self, url: str, token: str) -> None:
        @self.room.on("track_subscribed")
        def _track(track: rtc.Track, _pub: Any, p: rtc.RemoteParticipant) -> None:
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                self._tasks.append(asyncio.create_task(self._listen(track)))

        @self.room.on("data_received")
        def _data(pkt: rtc.DataPacket) -> None:
            if pkt.topic == "omar.latency":
                row = json.loads(pkt.data).get("turn") or {}
                if row.get("lead_text"):
                    self.rows.append(row)

        @self.room.on("participant_disconnected")
        def _left(p: rtc.RemoteParticipant) -> None:
            if p.kind == rtc.ParticipantKind.PARTICIPANT_KIND_AGENT:
                self.agent_left.set()

        await self.room.connect(url, token)
        track = rtc.LocalAudioTrack.create_audio_track("lead-mic", self.source)
        await self.room.local_participant.publish_track(
            track, rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
        )
        self._tasks.append(asyncio.create_task(self._mic()))

    async def _mic(self) -> None:
        """Send audio like a real microphone: speech when queued, silence otherwise."""
        silence = np.zeros(FRAME, dtype=np.int16)
        while True:
            item = silence if self.queue.empty() else self.queue.get_nowait()
            if isinstance(item, asyncio.Event):
                item.set()  # the speech before this marker is now in the send queue
                continue
            for i in range(0, len(item), FRAME):
                chunk = item[i : i + FRAME]
                if len(chunk) < FRAME:
                    chunk = np.pad(chunk, (0, FRAME - len(chunk)))
                frame = rtc.AudioFrame(chunk.tobytes(), RATE, 1, FRAME)
                await self.source.capture_frame(frame)  # paced in real time

    async def _listen(self, track: rtc.Track) -> None:
        async for ev in rtc.AudioStream(track, sample_rate=RATE, num_channels=1):
            f = ev.frame
            if _dbfs(np.frombuffer(f.data, dtype=np.int16)) > VOICE_DBFS:
                self.voice_times.append(time.time())

    async def say(self, parts: list[np.ndarray | float]) -> tuple[float, float]:
        """Speak one Lead turn. Returns (start, end of the last sound), wall time."""
        start = time.time()
        for part in parts:
            if isinstance(part, float):
                self.queue.put_nowait(np.zeros(int(RATE * part), dtype=np.int16))
            else:
                self.queue.put_nowait(part)
        done = asyncio.Event()
        self.queue.put_nowait(done)
        await done.wait()
        # the marker fires when the last frame entered the 60 ms send queue
        return start, time.time() + 0.06

    def voice_after(self, t: float) -> float | None:
        return next((v for v in self.voice_times if v > t), None)

    async def wait_quiet(self, quiet_s: float, timeout: float) -> bool:
        """Wait until Nimra has been silent for quiet_s (after she said something)."""
        end = time.time() + timeout
        while time.time() < end and not self.agent_left.is_set():
            last = self.voice_times[-1] if self.voice_times else None
            if last is not None and time.time() - last > quiet_s:
                return True
            await asyncio.sleep(0.05)
        return False

    async def close(self) -> None:
        for t in self._tasks:
            t.cancel()
        await self.room.disconnect()


async def run_call(
    mode: str, call: int, lines: list[list[np.ndarray | float]], args: argparse.Namespace
) -> list[Turn]:
    room_name = f"bench-{mode}-{call}-{int(time.time())}"
    meta = {
        "llm": args.llm,
        "turn": mode,
        "lang": args.lang,
        "lead": {
            "name": DEFAULT_LEAD.name,
            "email": DEFAULT_LEAD.email,
            "message": DEFAULT_LEAD.message,
            "topic": DEFAULT_LEAD.topic,
            "leadType": "new",
        },
    }
    token = (
        api.AccessToken(os.environ["LIVEKIT_API_KEY"], os.environ["LIVEKIT_API_SECRET"])
        .with_identity(f"lead-{call}")
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .with_room_config(
            api.RoomConfiguration(
                agents=[api.RoomAgentDispatch(agent_name=args.agent, metadata=json.dumps(meta))]
            )
        )
        .to_jwt()
    )
    bot = LeadBot()
    await bot.start(os.environ["LIVEKIT_URL"], token)
    turns: list[Turn] = []
    try:
        if not await bot.wait_quiet(1.2, timeout=25):  # the greeting
            print(f"  {mode} call {call}: no greeting")
            return turns
        for i, (script, parts) in enumerate(zip(SCRIPT, lines, strict=True)):
            if bot.agent_left.is_set():
                break
            text = " ".join(p for p in script if isinstance(p, str))
            seen_rows = len(bot.rows)
            start, end = await bot.say(parts)
            turn = Turn(mode, call, i + 1, text)
            turn.cut_in = any(start + 0.3 < v < end - 0.05 for v in bot.voice_times)
            deadline = time.time() + 12
            while bot.voice_after(end) is None and time.time() < deadline:
                await asyncio.sleep(0.02)
            reply = bot.voice_after(end)
            if reply is None:
                turn.no_reply = True
            else:
                turn.reply_gap_ms = round((reply - end) * 1000, 1)
            await bot.wait_quiet(1.2, timeout=30)
            await asyncio.sleep(0.5)  # the agent sends its timing row after playout starts
            new_rows = bot.rows[seen_rows:]
            if new_rows:
                turn.server = new_rows[-1]
            turns.append(turn)
            flag = " CUT-IN" if turn.cut_in else (" NO REPLY" if turn.no_reply else "")
            print(f"  {mode} call {call} line {i + 1}: {turn.reply_gap_ms} ms{flag}")
            await asyncio.sleep(args.gap)  # stay inside Groq's free-tier tokens per minute
    finally:
        await bot.close()
    return turns


def summarize(turns: list[Turn]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for mode in dict.fromkeys(t.mode for t in turns):
        rows = [t for t in turns if t.mode == mode]
        llm_rows = [t for t in rows if not t.server.get("scripted")]
        gaps = sorted(t.reply_gap_ms for t in llm_rows if t.reply_gap_ms is not None)
        all_gaps = sorted(t.reply_gap_ms for t in rows if t.reply_gap_ms is not None)

        def med(key: str, rows: list[Turn] = llm_rows) -> float | None:
            vals = [t.server[key] for t in rows if isinstance(t.server.get(key), int | float)]
            return round(statistics.median(vals), 1) if vals else None

        out[mode] = {
            "turns": len(rows),
            "llmTurns": len(llm_rows),
            "replyGapMedianMs": round(statistics.median(gaps), 1) if gaps else None,
            "replyGapP90Ms": gaps[max(0, math.ceil(len(gaps) * 0.9) - 1)] if gaps else None,
            "replyGapAllMedianMs": round(statistics.median(all_gaps), 1) if all_gaps else None,
            "cutIns": sum(t.cut_in for t in rows),
            "noReply": sum(t.no_reply for t in rows),
            "preemptiveUsed": sum(bool(t.server.get("preemptive")) for t in llm_rows),
            "serverMedianMs": {
                k: med(k)
                for k in (
                    "turnDetectMs",
                    "commitMs",
                    "eouWaitMs",
                    "llmStartMs",
                    "llmMs",
                    "ttsMs",
                    "headStartMs",
                    "totalMs",
                )
            },
        }
    return out


async def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--modes", default="flux,flux-eager,livekit-v1")
    ap.add_argument("--calls", type=int, default=2)
    ap.add_argument("--llm", default="groq", help="groq | deepseek | cerebras | auto")
    ap.add_argument("--agent", default=os.environ.get("BENCH_AGENT", "omar-bench"))
    ap.add_argument("--gap", type=float, default=12.0, help="seconds between Lead turns")
    ap.add_argument("--lang", default="en", choices=["en", "hi"], help="hi: the Lead speaks Hindi")
    args = ap.parse_args()
    if args.lang == "hi":
        SCRIPT[:] = SCRIPT_HI
    modes = [m for m in args.modes.split(",") if m]
    unknown = [m for m in modes if m not in TURN_PRESETS]
    if unknown:
        raise SystemExit(f"unknown modes {unknown}; known: {list(TURN_PRESETS)}")

    async with aiohttp.ClientSession() as http:
        lines: list[list[np.ndarray | float]] = [
            [p if isinstance(p, float) else await lead_audio(http, p) for p in script]
            for script in SCRIPT
        ]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}.jsonl"
    turns: list[Turn] = []
    for call in range(1, args.calls + 1):
        for mode in modes:
            print(f"{mode} call {call}")
            new = await run_call(mode, call, lines, args)
            turns += new
            with out_path.open("a") as f:
                for t in new:
                    f.write(json.dumps(asdict(t)) + "\n")
            await asyncio.sleep(args.gap)
    summary = summarize(turns)
    with out_path.open("a") as f:
        f.write(json.dumps({"summary": summary}) + "\n")
    print(json.dumps(summary, indent=2))
    print(f"rows: {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
