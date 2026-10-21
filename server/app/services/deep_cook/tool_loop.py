import json
import time
from dataclasses import dataclass

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage


@dataclass
class LoopStats:
    calls: int = 0
    errors: int = 0

    @property
    def ok(self) -> int:
        return self.calls - self.errors


def _tc_get(tc, key: str):
    if isinstance(tc, dict):
        return tc[key]
    return getattr(tc, key)


def gather_evidence(
    llm, tools, system: str, user: str, *, max_calls: int, timeout_s: int
) -> tuple[list[BaseMessage], LoopStats]:
    """Let the model call tools until it stops or the budget/timeout is hit.
    Every tool_call gets a ToolMessage (providers require the pairing). Tools are read-only."""
    tool_map = {t.name: t for t in tools}
    model = llm.bind_tools(tools)
    messages: list[BaseMessage] = [SystemMessage(system), HumanMessage(user)]
    stats, start = LoopStats(), time.monotonic()
    while True:
        ai = model.invoke(messages)
        messages.append(ai)
        tool_calls = getattr(ai, "tool_calls", None) or []
        if not tool_calls:
            break
        over = False
        for tc in tool_calls:
            if stats.calls >= max_calls or time.monotonic() - start > timeout_s:
                over = True
                messages.append(ToolMessage("SKIPPED: budget exhausted.", tool_call_id=_tc_get(tc, "id")))
                continue
            stats.calls += 1
            try:
                name = _tc_get(tc, "name")
                args = _tc_get(tc, "args")
                out = tool_map[name].invoke(args)
                content = json.dumps(out, ensure_ascii=False, default=str)[:8000]
            except Exception as e:
                stats.errors += 1
                content = f"ERROR: {type(e).__name__}: {e}"
            messages.append(ToolMessage(content, tool_call_id=_tc_get(tc, "id")))
        if over:
            break
    return messages, stats
