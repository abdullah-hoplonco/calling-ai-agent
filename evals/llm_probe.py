"""Text-only LLM speed probe: TTFT (time to first spoken token) and total time per reply.

Same system prompt as a real call, a short chat, streamed. No audio, no LiveKit.
Run: uv run python evals/llm_probe.py --providers groq,cerebras --runs 8
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time

from dotenv import load_dotenv
from openai import AsyncOpenAI

from omar_core import DEFAULT_LEAD
from omar_core.prompts import base_prompt
from omar_voice.settings import Settings

LINES = [
    "Yes, speaking. Who is this?",
    "Oh right, I filled that form last week. We need a new website for our clinic.",
    "Budget is maybe around fifteen thousand dirhams. Is that okay?",
    "Can you send me some examples of your work first?",
]


def client_for(name: str, s: Settings) -> tuple[AsyncOpenAI, str, dict]:
    import os

    if name == "groq":
        extra = {"extra_body": {"reasoning_effort": s.llm_reasoning_effort}}
        return (
            AsyncOpenAI(base_url=s.groq_base_url, api_key=os.environ["GROQ_API_KEY"]),
            s.groq_model,
            {"max_completion_tokens": s.llm_max_tokens, **extra},
        )
    if name == "cerebras":
        return (
            AsyncOpenAI(base_url="https://api.cerebras.ai/v1", api_key=s.cerebras_api_key),
            s.cerebras_model,
            {
                "max_completion_tokens": s.cerebras_max_tokens,
                "reasoning_effort": s.cerebras_reasoning_effort,
            },
        )
    if name == "cerebras-qwen":  # same Qwen as on Groq, thinking off
        return (
            AsyncOpenAI(base_url="https://api.cerebras.ai/v1", api_key=s.cerebras_api_key),
            "qwen-3.8-27b",
            {"max_completion_tokens": s.llm_max_tokens, "reasoning_effort": "none"},
        )
    if name == "deepseek":
        return (
            AsyncOpenAI(base_url="https://api.deepseek.com/v1", api_key=s.deepseek_api_key),
            s.deepseek_model,
            {
                "max_completion_tokens": s.llm_max_tokens,
                "extra_body": {"thinking": {"type": "disabled"}},
            },
        )
    raise SystemExit(f"unknown provider {name}")


async def one(c: AsyncOpenAI, model: str, opts: dict, msgs: list[dict]) -> dict:
    t0 = time.perf_counter()
    first_any = first_text = None
    text = ""
    usage = None
    stream = await c.chat.completions.create(
        model=model,
        messages=msgs,
        temperature=0.6,
        stream=True,
        stream_options={"include_usage": True},
        **opts,
    )
    async for ch in stream:
        now = time.perf_counter()
        if ch.usage:
            usage = ch.usage
        if not ch.choices:
            continue
        d = ch.choices[0].delta
        if first_any is None and (d.content or getattr(d, "reasoning", None)):
            first_any = now
        if d.content:
            if first_text is None:
                first_text = now
            text += d.content
    t1 = time.perf_counter()
    ms = lambda t: None if t is None else round((t - t0) * 1000)
    return {
        "first_any": ms(first_any),
        "ttft": ms(first_text),
        "total": ms(t1),
        "out": getattr(usage, "completion_tokens", None),
        "inp": getattr(usage, "prompt_tokens", None),
        "text": text.strip().replace("\n", " ")[:90],
    }


async def main() -> None:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--providers", default="groq,cerebras")
    ap.add_argument("--runs", type=int, default=8)
    args = ap.parse_args()
    s = Settings()
    system = base_prompt(DEFAULT_LEAD, s.agent_persona)
    results: dict[str, list[dict]] = {}
    for i in range(args.runs):
        line = LINES[i % len(LINES)]
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": line}]
        for name in args.providers.split(","):  # interleaved, so network drift hits both
            c, model, opts = client_for(name, s)
            try:
                r = await one(c, model, opts, msgs)
            except Exception as e:  # noqa: BLE001
                r = {"error": f"{type(e).__name__}: {str(e)[:120]}"}
            results.setdefault(name, []).append(r)
            print(name, r, flush=True)
    print("\nprovider   ok  ttft_p50  ttft_min  ttft_max  total_p50  out_tok_p50")
    for name, rs in results.items():
        ok = [r for r in rs if r.get("ttft") is not None]
        if not ok:
            print(f"{name:9}  0/{len(rs)}")
            continue
        med = lambda k, ok=ok: round(statistics.median(r[k] for r in ok if r[k] is not None))
        print(
            f"{name:9}  {len(ok)}/{len(rs)}  {med('ttft'):8}  {min(r['ttft'] for r in ok):8}  "
            f"{max(r['ttft'] for r in ok):8}  {med('total'):9}  {med('out'):11}"
        )


if __name__ == "__main__":
    asyncio.run(main())
