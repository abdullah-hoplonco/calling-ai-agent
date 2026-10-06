"""A scripted LLM for offline tests: no keys, no network, fully predictable.

`policy(chat_ctx, tool_names)` returns what the "model" does on one call:
a string (Omar's words) or a ("tool", name, args) tuple.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from livekit.agents import APIConnectOptions, llm
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, NOT_GIVEN, NotGivenOr

Action = str | tuple[str, str, dict[str, Any]]
Policy = Callable[[llm.ChatContext, list[str]], Action]


class ScriptedLLM(llm.LLM):
    def __init__(self, policy: Policy) -> None:
        super().__init__()
        self.policy = policy
        self.calls: list[list[str]] = []  # tool names offered on each call

    @property
    def model(self) -> str:
        return "scripted"

    @property
    def provider(self) -> str:
        return "test"

    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        tools: list[llm.Tool] | None = None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        parallel_tool_calls: NotGivenOr[bool] = NOT_GIVEN,
        tool_choice: NotGivenOr[llm.ToolChoice] = NOT_GIVEN,
        extra_kwargs: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
    ) -> llm.LLMStream:
        names = [getattr(t, "id", getattr(t, "name", "")) for t in (tools or [])]
        self.calls.append(names)
        return _Stream(self, chat_ctx=chat_ctx, tools=tools or [], conn_options=conn_options)


class _Stream(llm.LLMStream):
    async def _run(self) -> None:
        names = [getattr(t, "id", "") for t in self._tools]
        action = self._llm.policy(self._chat_ctx, names)  # type: ignore[attr-defined]
        if isinstance(action, tuple):
            _, name, args = action
            call = llm.FunctionToolCall(
                name=name, arguments=json.dumps(args), call_id=f"call_{len(self._chat_ctx.items)}"
            )
            self._event_ch.send_nowait(
                llm.ChatChunk(id="x", delta=llm.ChoiceDelta(role="assistant", tool_calls=[call]))
            )
            return
        for word in action.split(" "):
            self._event_ch.send_nowait(
                llm.ChatChunk(id="x", delta=llm.ChoiceDelta(role="assistant", content=word + " "))
            )


def last_user_text(ctx: llm.ChatContext) -> str:
    for item in reversed(ctx.items):
        if getattr(item, "type", None) == "message" and item.role == "user":
            return (item.text_content or "").lower()
    return ""


def last_is_tool_output(ctx: llm.ChatContext) -> str | None:
    item = ctx.items[-1] if ctx.items else None
    if item is not None and getattr(item, "type", None) == "function_call_output":
        return item.output
    return None
