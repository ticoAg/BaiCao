import ast
import json
from collections import deque
from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

from .provider_reasoning import extract_provider_reasoning_chunks


def _base_final_payload(session_id: str, turn_id: str) -> dict[str, Any]:
    return {
        "answer": "",
        "provider_reasoning": [],
        "tool_calls": [],
        "related_nodes": [],
        "related_edges": [],
        "subgraph_meta": {
            "center_node_id": None,
            "actual_depth": 0,
            "fallback_used": False,
            "node_count": 0,
            "edge_count": 0,
        },
        "evidence": [],
        "reasoning_trace": [],
        "session_id": session_id,
        "turn_id": turn_id,
    }


def _content_items(message: BaseMessage | None) -> list[dict[str, Any]]:
    content = getattr(message, "content", None)
    if not isinstance(content, list):
        return []
    return [item for item in content if isinstance(item, dict)]


def _extract_messages(output: Any) -> list[BaseMessage]:
    if isinstance(output, dict):
        messages = output.get("messages")
        if isinstance(messages, list):
            return [message for message in messages if isinstance(message, BaseMessage)]

    if isinstance(output, list):
        collected: list[BaseMessage] = []
        for item in output:
            update = getattr(item, "update", None)
            if isinstance(update, dict):
                messages = update.get("messages")
                if isinstance(messages, list):
                    collected.extend(message for message in messages if isinstance(message, BaseMessage))
        return collected

    return []


def _extract_answer_from_messages(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if not isinstance(message, AIMessage):
            continue
        parts = [
            item.get("text", "")
            for item in _content_items(message)
            if item.get("type") == "text" and isinstance(item.get("text"), str)
        ]
        answer = "".join(parts).strip()
        if answer:
            return answer
    return ""


def _parse_tool_payload(value: Any) -> Any:
    if isinstance(value, ToolMessage):
        value = value.content

    if isinstance(value, dict) and value.get("type") == "text" and isinstance(value.get("text"), str):
        return _parse_tool_payload(value["text"])

    if isinstance(value, (dict, list)):
        return value

    if not isinstance(value, str):
        return value

    text = value.strip()
    if not text:
        return ""

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    if text.startswith(("{", "[")):
        try:
            return ast.literal_eval(text)
        except (SyntaxError, ValueError):
            pass

    return text


def _coerce_dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _node_id(node: dict[str, Any]) -> str | None:
    for key in ("id", "标识", "name"):
        value = node.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _edge_id(edge: dict[str, Any]) -> str | None:
    edge_id = edge.get("id")
    if isinstance(edge_id, str) and edge_id:
        return edge_id

    source = edge.get("source")
    target = edge.get("target")
    rel_type = edge.get("rel_type") or edge.get("type") or "related"

    source_id = source if isinstance(source, str) else source.get("id") if isinstance(source, dict) else None
    target_id = target if isinstance(target, str) else target.get("id") if isinstance(target, dict) else None
    if isinstance(source_id, str) and isinstance(target_id, str):
        return f"{source_id}:{rel_type}:{target_id}"
    return None


def _merge_graph_patch(
    graph_state: dict[str, Any],
    patch: dict[str, Any] | None,
    *,
    tool_arguments: dict[str, Any] | None = None,
) -> None:
    if not patch:
        return

    for node in patch.get("nodes", []):
        if not isinstance(node, dict):
            continue
        node_key = _node_id(node)
        if not node_key:
            continue
        graph_state["nodes"][node_key] = node

    for edge in patch.get("edges", []):
        if not isinstance(edge, dict):
            continue
        edge_key = _edge_id(edge)
        if not edge_key:
            continue
        graph_state["edges"][edge_key] = edge

    center_node_id = patch.get("center_node_id")
    if isinstance(center_node_id, str) and center_node_id:
        graph_state["center_node_id"] = center_node_id

    depth = tool_arguments.get("depth") if isinstance(tool_arguments, dict) else None
    if isinstance(depth, int):
        graph_state["actual_depth"] = max(graph_state["actual_depth"], depth)


def _items_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return _coerce_dict_list(payload["items"])
    return _coerce_dict_list(payload)


def _patch_from_tool_payload(tool_name: str, payload: Any) -> dict[str, Any] | None:
    if tool_name in {"search_nodes", "lookup_nodes"}:
        nodes = _items_from_payload(payload)
        if nodes:
            return {"nodes": nodes}
        return None

    if tool_name == "expand_neighbors" and isinstance(payload, dict):
        center = payload.get("center")
        center_node_id = None
        if isinstance(center, dict):
            center_node_id = _node_id(center)
        elif isinstance(payload.get("center_node_id"), str):
            center_node_id = payload["center_node_id"]
        return {
            "nodes": _coerce_dict_list(payload.get("nodes")),
            "edges": _coerce_dict_list(payload.get("edges")),
            "center_node_id": center_node_id,
        }

    if tool_name == "search_edges":
        edges = _items_from_payload(payload)
        nodes: list[dict[str, Any]] = []
        for edge in edges:
            for endpoint_key in ("source", "target"):
                endpoint = edge.get(endpoint_key)
                if isinstance(endpoint, dict):
                    nodes.append(endpoint)
        if edges or nodes:
            return {"nodes": nodes, "edges": edges}
        return None

    return None


def _summarize_tool_payload(tool_name: str, payload: Any) -> str:
    if isinstance(payload, dict) and isinstance(payload.get("count"), int):
        if tool_name in {"search_nodes", "lookup_nodes"}:
            return f"返回 {payload['count']} 个节点"
        if tool_name == "search_edges":
            return f"返回 {payload['count']} 条关系"
        if tool_name == "expand_neighbors":
            node_count = payload.get("node_count")
            edge_count = payload.get("edge_count")
            if isinstance(node_count, int) and isinstance(edge_count, int):
                return f"返回 {node_count} 个节点、{edge_count} 条关系"
    if tool_name in {"search_nodes", "lookup_nodes"} and isinstance(payload, list):
        return f"返回 {len(payload)} 个节点"
    if tool_name == "search_edges" and isinstance(payload, list):
        return f"返回 {len(payload)} 条关系"
    if tool_name == "expand_neighbors" and isinstance(payload, dict):
        node_count = len(_coerce_dict_list(payload.get("nodes")))
        edge_count = len(_coerce_dict_list(payload.get("edges")))
        return f"返回 {node_count} 个节点、{edge_count} 条关系"
    if isinstance(payload, list):
        return f"返回 {len(payload)} 条记录"
    if isinstance(payload, dict):
        keys = ", ".join(sorted(payload.keys())[:4])
        return f"返回对象：{keys}" if keys else "返回对象结果"
    if isinstance(payload, str):
        snippet = payload.strip()
        return snippet[:80] if snippet else "工具已完成"
    return "工具已完成"


def _payload_preview(payload: Any) -> dict[str, Any] | None:
    if isinstance(payload, dict):
        return payload
    return None


def _append_provider_reasoning(
    collected: list[dict[str, str]],
    chunk: dict[str, str],
) -> bool:
    text = chunk.get("text", "")
    if not text.strip():
        return False

    if collected:
        last = collected[-1]
        if last.get("id") == chunk.get("id"):
            last["text"] = f'{last["text"]}{text}'
            return True

    collected.append(dict(chunk))
    return True


async def adapt_agent_events(
    agent_events: AsyncIterator[Any],
    *,
    session_id: str,
    turn_id: str,
) -> AsyncIterator[dict[str, Any]]:
    provider_reasoning: list[dict[str, str]] = []
    answer_chunks: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    tool_calls_by_id: dict[str, dict[str, Any]] = {}
    pending_tool_calls: deque[dict[str, Any]] = deque()
    graph_state = {
        "nodes": {},
        "edges": {},
        "center_node_id": None,
        "actual_depth": 0,
    }

    async for event in agent_events:
        event_type = event.get("event")
        name = event.get("name")
        raw_data = event.get("data")
        data: dict[str, Any] = raw_data if isinstance(raw_data, dict) else {}

        if event_type == "on_chat_model_stream":
            chunk = data.get("chunk")
            content_items = _content_items(chunk)

            for reasoning_chunk in extract_provider_reasoning_chunks({"output": content_items}):
                if _append_provider_reasoning(provider_reasoning, reasoning_chunk):
                    yield {"type": "provider_reasoning", "data": reasoning_chunk}

            for item in content_items:
                if item.get("type") != "text":
                    continue
                text = item.get("text")
                if isinstance(text, str) and text:
                    answer_chunks.append(text)
                    yield {"type": "answer_chunk", "data": {"text": text}}

        elif event_type == "on_chain_end" and name == "model":
            for message in _extract_messages(data.get("output")):
                if not isinstance(message, AIMessage):
                    continue
                for tool_call in message.tool_calls:
                    if not isinstance(tool_call, dict):
                        continue
                    tool_name = tool_call.get("name")
                    call_id = tool_call.get("id")
                    arguments = tool_call.get("args")
                    if not isinstance(tool_name, str) or not isinstance(call_id, str):
                        continue
                    pending_tool_calls.append(
                        {
                            "call_id": call_id,
                            "tool_name": tool_name,
                            "arguments": arguments if isinstance(arguments, dict) else {},
                        }
                    )

        elif event_type == "on_tool_start" and isinstance(name, str):
            pending_match = next(
                (
                    item
                    for item in pending_tool_calls
                    if item["tool_name"] == name
                ),
                None,
            )
            if pending_match is not None:
                pending_tool_calls.remove(pending_match)

            arguments = data.get("input") if isinstance(data.get("input"), dict) else {}
            call_id = (
                pending_match["call_id"]
                if pending_match is not None
                else f"{name}-{len(tool_calls) + 1}"
            )
            if pending_match is not None and not arguments:
                arguments = pending_match["arguments"]

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
                "data": {
                    "call_id": call_id,
                    "tool_name": name,
                    "arguments": arguments,
                },
            }

        elif event_type == "on_tool_end":
            output = data.get("output")
            tool_name = getattr(output, "name", None) or name or "tool"
            call_id = getattr(output, "tool_call_id", None)
            parsed_payload = _parse_tool_payload(output)
            result_summary = _summarize_tool_payload(tool_name, parsed_payload)
            preview = _payload_preview(parsed_payload)

            record = tool_calls_by_id.get(call_id) if isinstance(call_id, str) else None
            if record is None:
                generated_call_id = call_id if isinstance(call_id, str) else f"{tool_name}-{len(tool_calls) + 1}"
                record = {
                    "call_id": generated_call_id,
                    "tool_name": tool_name,
                    "arguments": {},
                    "summary": "工具调用开始",
                    "result_summary": None,
                    "status": "running",
                }
                tool_calls.append(record)
                tool_calls_by_id[generated_call_id] = record
                call_id = generated_call_id

            record["result_summary"] = result_summary
            record["status"] = "completed"

            yield {
                "type": "tool_result",
                "data": {
                    "call_id": record["call_id"],
                    "tool_name": tool_name,
                    "result_summary": result_summary,
                    "payload_preview": preview,
                },
            }

            patch = _patch_from_tool_payload(tool_name, parsed_payload)
            tool_arguments = record.get("arguments")
            _merge_graph_patch(
                graph_state,
                patch,
                tool_arguments=tool_arguments if isinstance(tool_arguments, dict) else None,
            )
            if patch:
                yield {"type": "subgraph_patch", "data": patch}

        elif event_type == "on_chain_end" and name == "LangGraph":
            final_messages = _extract_messages(data.get("output"))
            answer = _extract_answer_from_messages(final_messages) or "".join(answer_chunks).strip()
            final_payload = _base_final_payload(session_id, turn_id)
            final_payload["answer"] = answer
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
            final_payload["reasoning_trace"] = [
                {
                    "kind": "tool",
                    "summary": f'{tool_call["tool_name"]}: {tool_call["result_summary"] or tool_call["summary"]}',
                }
                for tool_call in tool_calls
            ]
            yield {"type": "final", "data": final_payload}
            return

    yield {"type": "final", "data": _base_final_payload(session_id, turn_id)}
