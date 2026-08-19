from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from .citations import citations_from_graph_state
from .event_adapter import (
    _base_final_payload,
    _merge_graph_patch,
    _parse_tool_payload,
    _patch_from_tool_payload,
    _payload_preview,
    _summarize_tool_payload,
)


def _message_output_text(item: Any) -> str:
    try:
        from agents import ItemHelpers

        text = ItemHelpers.text_message_output(item)
        if text:
            return text
    except Exception:
        pass
    raw = getattr(item, "raw_item", None)
    content = getattr(raw, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            text = block.get("text") if isinstance(block, dict) else getattr(block, "text", None)
            if isinstance(text, str):
                parts.append(text)
        return "".join(parts)
    return ""


def _tool_call_fields(item: Any) -> tuple[str, str, dict[str, Any]]:
    raw = getattr(item, "raw_item", None)
    name = getattr(raw, "name", None) or getattr(item, "_resolved_tool_name", None) or "tool"
    call_id = getattr(raw, "call_id", None) or getattr(raw, "id", None) or f"{name}-1"
    arguments = getattr(raw, "arguments", None) or {}
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
            arguments = parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            arguments = {}
    if not isinstance(arguments, dict):
        arguments = {}
    return str(call_id), str(name), arguments


async def adapt_openai_stream(
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

    async for event in stream_events:
        event_type = getattr(event, "type", None)
        if event_type == "raw_response_event":
            continue

        if event_type != "run_item_stream_event":
            continue

        item = getattr(event, "item", None)
        item_type = getattr(item, "type", None)
        if item_type == "tool_call_item":
            call_id, name, arguments = _tool_call_fields(item)
            record = {
                "call_id": call_id,
                "tool_name": name,
                "arguments": arguments,
                "summary": "工具调用开始",
                "result_summary": None,
                "status": "running",
            }
            tool_calls.append(record)
            tool_calls_by_id[call_id] = record
            yield {
                "type": "tool_start",
                "data": {"call_id": call_id, "tool_name": name, "arguments": arguments},
            }
        elif item_type == "tool_call_output_item":
            output = getattr(item, "output", None)
            raw = getattr(item, "raw_item", None)
            call_id = getattr(item, "call_id", None) or getattr(raw, "call_id", None) or getattr(raw, "id", None)
            parsed = _parse_tool_payload(output)
            record = tool_calls_by_id.get(str(call_id)) if call_id else None
            if record is None:
                record = next((item for item in reversed(tool_calls) if item["status"] == "running"), None)
            tool_name = record["tool_name"] if record else "tool"
            summary = _summarize_tool_payload(tool_name, parsed)
            if record is None:
                generated = str(call_id or f"{tool_name}-{len(tool_calls) + 1}")
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
            yield {
                "type": "tool_result",
                "data": {
                    "call_id": record["call_id"],
                    "tool_name": tool_name,
                    "result_summary": summary,
                    "payload_preview": _payload_preview(parsed) if isinstance(parsed, dict) else None,
                },
            }
            patch = _patch_from_tool_payload(tool_name, parsed)
            raw_arguments = record.get("arguments")
            tool_arguments: dict[str, Any] | None = (
                raw_arguments if isinstance(raw_arguments, dict) else None
            )
            _merge_graph_patch(
                graph_state,
                patch,
                tool_arguments=tool_arguments,
            )
            if patch:
                yield {"type": "subgraph_patch", "data": patch}
        elif item_type == "message_output_item":
            text = _message_output_text(item).strip()
            if text:
                answer_chunks = [text]
                yield {"type": "answer_chunk", "data": {"text": text}}

    final_payload = _base_final_payload(session_id, turn_id)
    final_payload["answer"] = "".join(answer_chunks).strip()
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
