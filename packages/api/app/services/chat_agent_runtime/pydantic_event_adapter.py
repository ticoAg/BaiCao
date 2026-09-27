from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from pydantic_ai import (
    AgentRunResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartEndEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
    ThinkingPart,
    ThinkingPartDelta,
)

from .citations import citations_from_graph_state
from .sse_payloads import (
    base_final_payload,
    merge_graph_patch,
    parse_tool_payload,
    patch_from_tool_payload,
    payload_preview,
    summarize_tool_payload,
)


def _tool_args(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


class _StreamTextCollector:
    """把 part 边界事件与 delta 事件合成一份完整文本。

    pydantic-ai 的 `PartStartEvent` 携带该 part 的首个分片，后续分片才走
    `PartDeltaEvent`；`PartEndEvent.part.content` 是完整内容。只读 delta 会
    丢掉首片，表现为答案开头少字（例如「黄芪」变成「芪」）。这里按 part
    归属缓冲，`PartEndEvent` 时以完整内容为准，算出尚未推送的增量。
    """

    def __init__(self) -> None:
        self._buffer: str = ""
        self._emitted: str = ""

    def append(self, text: str) -> None:
        if text:
            self._buffer += text

    def sync(self, full_text: str) -> None:
        """以 part 的完整内容校准缓冲。"""
        self._buffer = full_text

    def discard(self) -> None:
        self.sync("")

    def flush(self) -> str | None:
        """产出尚未推送的文本；无新增内容时返回 None。"""
        if self._buffer.startswith(self._emitted):
            fresh = self._buffer[len(self._emitted) :]
        else:
            # 上游改写了已推送内容，无法只发增量，只能整体重发。
            fresh = self._buffer
        self._emitted = self._buffer
        return fresh or None


async def adapt_pydantic_stream(
    stream_events: AsyncIterator[Any],
    *,
    session_id: str,
    turn_id: str,
) -> AsyncIterator[dict[str, Any]]:
    tool_calls: list[dict[str, Any]] = []
    tool_calls_by_id: dict[str, dict[str, Any]] = {}
    graph_state: dict[str, Any] = {
        "nodes": {},
        "edges": {},
        "center_node_id": None,
        "actual_depth": 0,
    }
    answer_chunks: list[str] = []
    provider_reasoning: list[dict[str, str]] = []
    text_collector = _StreamTextCollector()
    reasoning_collector = _StreamTextCollector()

    async for event in stream_events:
        if isinstance(event, FunctionToolCallEvent):
            part = event.part
            call_id = event.tool_call_id or getattr(part, "tool_call_id", None) or f"{part.tool_name}-1"
            arguments = _tool_args(getattr(part, "args", None))
            record = {
                "call_id": str(call_id),
                "tool_name": str(part.tool_name),
                "arguments": arguments,
                "summary": "工具调用开始",
                "result_summary": None,
                "status": "running",
            }
            tool_calls.append(record)
            tool_calls_by_id[str(call_id)] = record
            yield {
                "type": "tool_start",
                "data": {
                    "call_id": str(call_id),
                    "tool_name": str(part.tool_name),
                    "arguments": arguments,
                },
            }
        elif isinstance(event, FunctionToolResultEvent):
            part = event.part
            call_id = str(event.tool_call_id or getattr(part, "tool_call_id", "") or "")
            tool_name = str(getattr(part, "tool_name", None) or "tool")
            parsed = parse_tool_payload(event.content if event.content is not None else getattr(part, "content", None))
            summary = summarize_tool_payload(tool_name, parsed)
            record = tool_calls_by_id.get(call_id)
            if record is None:
                record = next((item for item in reversed(tool_calls) if item["status"] == "running"), None)
            if record is None:
                generated = call_id or f"{tool_name}-{len(tool_calls) + 1}"
                record = {
                    "call_id": generated,
                    "tool_name": tool_name,
                    "arguments": {},
                    "summary": "工具调用开始",
                    "result_summary": summary,
                    "status": "completed",
                }
                tool_calls.append(record)
                tool_calls_by_id[generated] = record
            else:
                record["result_summary"] = summary
                record["status"] = "completed"
                tool_name = record["tool_name"]
            yield {
                "type": "tool_result",
                "data": {
                    "call_id": record["call_id"],
                    "tool_name": tool_name,
                    "result_summary": summary,
                    "payload_preview": payload_preview(parsed) if isinstance(parsed, dict) else None,
                },
            }
            patch = patch_from_tool_payload(tool_name, parsed)
            raw_arguments = record.get("arguments")
            merge_graph_patch(
                graph_state,
                patch,
                tool_arguments=raw_arguments if isinstance(raw_arguments, dict) else None,
            )
            if patch:
                yield {"type": "subgraph_patch", "data": patch}
        elif isinstance(event, PartStartEvent):
            if isinstance(event.part, TextPart):
                text_collector.append(event.part.content or "")
            elif isinstance(event.part, ThinkingPart):
                reasoning_collector.append(event.part.content or "")
        elif isinstance(event, PartEndEvent):
            if isinstance(event.part, TextPart):
                # PartStart 可能紧接工具调用（如「我来查询一下」），这类前言不是
                # 最终答案；PartEndEvent 带 next_part_kind，据此决定是否发出。
                if event.next_part_kind != "tool-call":
                    text_collector.sync(event.part.content or "")
                    fresh = text_collector.flush()
                    if fresh:
                        answer_chunks.append(fresh)
                        yield {"type": "answer_chunk", "data": {"text": fresh}}
                else:
                    text_collector.discard()
            elif isinstance(event.part, ThinkingPart):
                reasoning_collector.sync(event.part.content or "")
                fresh = reasoning_collector.flush()
                if fresh:
                    provider_reasoning.append({"text": fresh})
                    yield {"type": "provider_reasoning", "data": {"text": fresh}}
        elif isinstance(event, PartDeltaEvent):
            delta = event.delta
            if isinstance(delta, TextPartDelta) and delta.content_delta:
                text_collector.append(delta.content_delta)
            elif isinstance(delta, ThinkingPartDelta) and delta.content_delta:
                reasoning_collector.append(delta.content_delta)
        elif isinstance(event, AgentRunResultEvent):
            result = event.result
            output = getattr(result, "output", None)
            if isinstance(output, str) and output.strip() and not answer_chunks:
                answer_chunks.append(output.strip())

    final_payload = base_final_payload(session_id, turn_id)
    final_payload["answer"] = "".join(answer_chunks).strip()
    final_payload["provider_reasoning"] = provider_reasoning
    final_payload["tool_calls"] = tool_calls
    final_payload["related_nodes"] = list(graph_state["nodes"].values())
    final_payload["related_edges"] = list(graph_state["edges"].values())
    final_payload["subgraph_meta"] = {
        "center_node_id": graph_state["center_node_id"],
        "actual_depth": graph_state["actual_depth"],
        "fallback_used": False,
        "node_count": len(graph_state["nodes"]),
        "edge_count": len(graph_state["edges"]),
    }
    final_payload["evidence"] = citations_from_graph_state(graph_state)
    final_payload["reasoning_trace"] = [
        {
            "kind": "tool",
            "summary": f'{item["tool_name"]}: {item["result_summary"] or item["summary"]}',
        }
        for item in tool_calls
    ]
    yield {"type": "final", "data": final_payload}
