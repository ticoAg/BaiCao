from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from pydantic_ai import (
    AgentRunResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    TextPartDelta,
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
        elif isinstance(event, PartDeltaEvent):
            delta = event.delta
            if isinstance(delta, TextPartDelta) and delta.content_delta:
                answer_chunks.append(delta.content_delta)
                yield {"type": "answer_chunk", "data": {"text": delta.content_delta}}
            elif isinstance(delta, ThinkingPartDelta) and delta.content_delta:
                chunk = {"text": delta.content_delta}
                provider_reasoning.append(chunk)
                yield {"type": "provider_reasoning", "data": chunk}
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
