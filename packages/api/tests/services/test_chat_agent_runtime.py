from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock

import pytest
from pydantic_ai import (
    AgentRunResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    TextPartDelta,
)
from pydantic_ai.messages import ToolCallPart, ToolReturnPart

from app.services.chat_agent_runtime.pydantic_event_adapter import adapt_pydantic_stream


async def _iter_events(events: list):
    for event in events:
        yield event


@pytest.mark.asyncio
async def test_adapt_pydantic_stream_maps_tool_and_answer():
    events = [
        FunctionToolCallEvent(
            part=ToolCallPart(tool_name="search_nodes", args={"query": "乌梅丸"}, tool_call_id="call-1")
        ),
        FunctionToolResultEvent(
            part=ToolReturnPart(
                tool_name="search_nodes",
                content={"count": 1, "items": [{"id": "formula-乌梅丸", "name": "乌梅丸", "labels": ["方剂"]}]},
                tool_call_id="call-1",
            )
        ),
        PartDeltaEvent(index=0, delta=TextPartDelta(content_delta="乌梅丸是一张方剂。")),
    ]

    adapted = [
        event
        async for event in adapt_pydantic_stream(_iter_events(events), session_id="sid-1", turn_id="turn-1")
    ]
    assert [event["type"] for event in adapted] == [
        "tool_start",
        "tool_result",
        "subgraph_patch",
        "answer_chunk",
        "final",
    ]
    assert adapted[0]["data"]["tool_name"] == "search_nodes"
    assert adapted[1]["data"]["result_summary"] == "返回 1 个节点"
    assert adapted[-1]["data"]["answer"] == "乌梅丸是一张方剂。"
    assert adapted[-1]["data"]["related_nodes"][0]["name"] == "乌梅丸"


@pytest.mark.asyncio
async def test_adapt_pydantic_stream_builds_evidence_from_graph_state_only():
    payload = {
        "center": {"id": "药材:乌梅", "name": "乌梅", "labels": ["药材"]},
        "nodes": [
            {"id": "药材:乌梅", "name": "乌梅", "labels": ["药材"]},
            {
                "id": "证据:suyang-002",
                "name": "证据:suyang-002",
                "labels": ["证据"],
                "evidence_text": "乌梅味酸，能涩肠止痢。",
            },
            {"id": "来源:道医苏子阳", "name": "道医苏子阳", "labels": ["来源"]},
        ],
        "edges": [
            {
                "rel_type": "由证据支持",
                "source": {"id": "药材:乌梅", "name": "乌梅", "labels": ["药材"]},
                "target": {"id": "证据:suyang-002", "name": "证据:suyang-002", "labels": ["证据"]},
            },
            {
                "rel_type": "来源于",
                "source": {"id": "证据:suyang-002", "name": "证据:suyang-002", "labels": ["证据"]},
                "target": {"id": "来源:道医苏子阳", "name": "道医苏子阳", "labels": ["来源"]},
            },
        ],
        "node_count": 3,
        "edge_count": 2,
    }
    events = [
        FunctionToolCallEvent(
            part=ToolCallPart(
                tool_name="expand_neighbors",
                args={"node_id": "药材:乌梅", "depth": 2},
                tool_call_id="call-exp",
            )
        ),
        FunctionToolResultEvent(
            part=ToolReturnPart(tool_name="expand_neighbors", content=payload, tool_call_id="call-exp")
        ),
        PartDeltaEvent(index=0, delta=TextPartDelta(content_delta="乌梅味酸。出处：本草纲目伪引用不应进入 evidence。")),
    ]
    adapted = [
        event
        async for event in adapt_pydantic_stream(_iter_events(events), session_id="sid-2", turn_id="turn-2")
    ]
    final = next(event for event in adapted if event["type"] == "final")
    assert final["data"]["evidence"][0]["source_id"] == "来源:道医苏子阳"
    assert "伪造" not in str(final["data"]["evidence"])
    assert "本草纲目" not in str(final["data"]["evidence"])


class _FakeRunEvents:
    def __init__(self, items):
        self._items = items

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def __aiter__(self):
        self._iter = iter(self._items)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class _FakeAgent:
    name = "BaiCao Graph Specialist"

    def __init__(self, captured: dict, result_messages: list | None = None):
        self.captured = captured
        self.result_messages = result_messages or ["hist"]

    def run_stream_events(self, user_prompt, **kwargs):
        self.captured["prompt"] = user_prompt
        self.captured.setdefault("histories", []).append(kwargs.get("message_history"))
        result = SimpleNamespace(all_messages=lambda: list(self.result_messages), output="")
        return _FakeRunEvents([AgentRunResultEvent(result=cast(Any, result))])


def _ready_settings():
    return SimpleNamespace(
        openai_api_key="fw-test",
        openai_base_url="https://api.fireworks.ai/inference/v1",
        openai_model="accounts/fireworks/models/deepseek-v4-flash-0731",
    )


def _patch_runtime(monkeypatch, runtime, captured: dict):
    monkeypatch.setattr(runtime, "get_settings", _ready_settings)

    async def fake_build(client, settings=None):
        return _FakeAgent(captured)

    monkeypatch.setattr(runtime, "build_graph_agent", fake_build)


@pytest.mark.asyncio
async def test_stream_turn_uses_pydantic_agent(monkeypatch):
    from app.services.chat_agent_runtime import runtime

    captured: dict = {}
    _patch_runtime(monkeypatch, runtime, captured)
    runtime._MESSAGE_HISTORIES.clear()

    events = [event async for event in runtime.stream_turn("第一问", session_id="sid-runtime")]

    assert events[0]["type"] == "session"
    assert events[-1]["type"] == "final"
    assert captured["prompt"] == "第一问"
    assert runtime._MESSAGE_HISTORIES["sid-runtime"] == ["hist"]


@pytest.mark.asyncio
async def test_stream_turn_reuses_message_history(monkeypatch):
    from app.services.chat_agent_runtime import runtime

    captured: dict = {"histories": []}
    _patch_runtime(monkeypatch, runtime, captured)
    runtime._MESSAGE_HISTORIES.clear()

    async for _ in runtime.stream_turn("第一问", session_id="sid-keep-all"):
        pass
    async for _ in runtime.stream_turn("第二问", session_id="sid-keep-all"):
        pass

    assert captured["histories"][0] in (None, [])
    assert captured["histories"][1] == ["hist"]


@pytest.mark.asyncio
async def test_expired_history_is_removed(monkeypatch):
    from app.services.chat_agent_runtime import runtime

    captured: dict = {}
    _patch_runtime(monkeypatch, runtime, captured)
    runtime._MESSAGE_HISTORIES.clear()

    async for _ in runtime.stream_turn("第一问", session_id="sid-ttl-close"):
        pass

    runtime._SESSION_MANAGER._last_seen["sid-ttl-close"] = (  # noqa: SLF001
        runtime._SESSION_MANAGER.time_fn() - runtime._SESSION_MANAGER.ttl_seconds - 1
    )

    async for _ in runtime.stream_turn("第二问", session_id="sid-ttl-fresh"):
        pass

    assert "sid-ttl-close" not in runtime._MESSAGE_HISTORIES
    assert "sid-ttl-fresh" in runtime._MESSAGE_HISTORIES


def test_close_all_chat_sessions_clears_history(monkeypatch):
    from app.services.chat_agent_runtime import runtime

    isolated: dict[str, list] = {"a": ["m"]}
    monkeypatch.setattr(runtime, "_MESSAGE_HISTORIES", isolated)
    runtime.close_all_chat_sessions()
    assert isolated == {}


@pytest.mark.asyncio
async def test_app_shutdown_closes_chat_sessions(monkeypatch):
    from contextlib import asynccontextmanager
    from unittest.mock import AsyncMock

    from app import main
    from app.services.chat_agent_runtime import runtime

    monkeypatch.setattr(main, "init_db", AsyncMock())
    monkeypatch.setattr(main, "init_kg_db", AsyncMock())
    monkeypatch.setattr(main, "streamable_http_app", lambda: None)

    @asynccontextmanager
    async def fake_run():
        yield

    monkeypatch.setattr(main.knowledge_mcp.session_manager, "run", lambda: fake_run())

    isolated: dict[str, list] = {"sid-app-shutdown": ["m"]}
    monkeypatch.setattr(runtime, "_MESSAGE_HISTORIES", isolated)

    async with main.lifespan(main.app):
        assert isolated["sid-app-shutdown"] == ["m"]

    assert isolated == {}


@pytest.mark.asyncio
async def test_stream_turn_passes_mcp_client_to_agent_builder(monkeypatch):
    from mcp.client import Client

    from app.services.chat_agent_runtime import runtime

    captured: dict = {}
    _patch_runtime(monkeypatch, runtime, captured)
    runtime._MESSAGE_HISTORIES.clear()

    seen: list = []

    async def fake_build(client, settings=None):
        seen.append(client)
        return _FakeAgent(captured)

    monkeypatch.setattr(runtime, "build_graph_agent", fake_build)
    async for _ in runtime.stream_turn("问", session_id="sid-mcp-client"):
        pass

    assert seen
    assert isinstance(seen[0], Client)


@pytest.mark.asyncio
async def test_tools_from_mcp_client_wraps_list_tools_and_call():
    from mcp.client import Client

    from app.services.chat_agent_runtime.mcp_agent_tools import tools_from_mcp_client
    from app.services.knowledge_mcp.handlers import KnowledgeMcpHandlers
    from app.services.knowledge_mcp.server import create_knowledge_mcp

    backend = AsyncMock()
    backend.search_nodes = AsyncMock(return_value=[])
    mcp = create_knowledge_mcp(KnowledgeMcpHandlers(backend_factory=lambda: backend))
    async with Client(mcp) as client:
        tools = await tools_from_mcp_client(client)
        names = {tool.name for tool in tools}
        assert names == {"search_nodes", "search_edges", "expand_neighbors", "lookup_nodes"}
        search = next(tool for tool in tools if tool.name == "search_nodes")
        payload = await search.function(query="不存在的实体")
    assert payload["count"] == 0
    assert "标识" in payload["hint"]
    backend.search_nodes.assert_awaited()
