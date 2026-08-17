import pytest
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.types import Command

from app.services.chat_agent_runtime.event_adapter import adapt_agent_events


async def _iter_events(events: list[dict]):
    for event in events:
        yield event


@pytest.mark.asyncio
async def test_adapt_agent_events_maps_langgraph_stream_to_sse_protocol():
    raw_events = [
        {
            "event": "on_chat_model_stream",
            "name": "ChatOpenAI",
            "data": {
                "chunk": AIMessage(
                    content=[
                        {
                            "type": "reasoning",
                            "id": "rs-1",
                            "summary": [{"type": "summary_text", "text": "先定位病证锚点"}],
                        }
                    ]
                )
            },
        },
        {
            "event": "on_chain_end",
            "name": "model",
            "data": {
                "output": [
                    Command(
                        update={
                            "messages": [
                                AIMessage(
                                    content=[
                                        {
                                            "type": "function_call",
                                            "name": "search_nodes",
                                            "arguments": '{"query": "感冒"}',
                                            "call_id": "call-1",
                                            "id": "fc-1",
                                            "index": 0,
                                        }
                                    ],
                                    tool_calls=[
                                        {
                                            "name": "search_nodes",
                                            "args": {"query": "感冒"},
                                            "id": "call-1",
                                            "type": "tool_call",
                                        }
                                    ],
                                )
                            ]
                        }
                    )
                ]
            },
        },
        {
            "event": "on_tool_start",
            "name": "search_nodes",
            "data": {"input": {"query": "感冒"}},
        },
        {
            "event": "on_tool_end",
            "name": "search_nodes",
            "data": {
                "output": ToolMessage(
                    content='[{"id":"药材:桂枝","name":"桂枝","labels":["Herb"],"status":"verified"}]',
                    name="search_nodes",
                    tool_call_id="call-1",
                )
            },
        },
        {
            "event": "on_chat_model_stream",
            "name": "ChatOpenAI",
            "data": {"chunk": AIMessage(content=[{"type": "text", "text": "可考虑桂枝。"}])},
        },
        {
            "event": "on_chain_end",
            "name": "LangGraph",
            "data": {
                "output": {
                    "messages": [
                        AIMessage(content=[{"type": "text", "text": "可考虑桂枝。"}]),
                    ]
                }
            },
        },
    ]

    events = [
        event
        async for event in adapt_agent_events(
            _iter_events(raw_events),
            session_id="sid-1",
            turn_id="turn-1",
        )
    ]

    assert [event["type"] for event in events] == [
        "provider_reasoning",
        "tool_start",
        "tool_result",
        "subgraph_patch",
        "answer_chunk",
        "final",
    ]
    assert events[0]["data"] == {"id": "rs-1", "text": "先定位病证锚点"}
    assert events[1]["data"] == {
        "call_id": "call-1",
        "tool_name": "search_nodes",
        "arguments": {"query": "感冒"},
    }
    assert events[2]["data"]["call_id"] == "call-1"
    assert events[2]["data"]["tool_name"] == "search_nodes"
    assert "1 个节点" in events[2]["data"]["result_summary"]
    assert events[3]["data"]["nodes"][0]["name"] == "桂枝"
    assert events[4]["data"] == {"text": "可考虑桂枝。"}
    assert events[5]["data"]["answer"] == "可考虑桂枝。"
    assert events[5]["data"]["provider_reasoning"] == [{"id": "rs-1", "text": "先定位病证锚点"}]
    assert events[5]["data"]["tool_calls"][0]["call_id"] == "call-1"
    assert events[5]["data"]["related_nodes"][0]["name"] == "桂枝"
    assert events[5]["data"]["subgraph_meta"]["node_count"] == 1


@pytest.mark.asyncio
async def test_stream_turn_uses_openai_agents_runner(monkeypatch):
    from types import SimpleNamespace

    from app.services.chat_agent_runtime import runtime

    captured = {}

    class FakeResult:
        async def stream_events(self):
            yield SimpleNamespace(type="raw_response_event", data=SimpleNamespace(delta="done"))

    def fake_run_streamed(agent, question, session=None):
        captured["question"] = question
        captured["session"] = session
        captured["agent_name"] = agent.name
        return FakeResult()

    monkeypatch.setattr(
        runtime,
        "get_settings",
        lambda: SimpleNamespace(
            openai_api_key="fw-test",
            openai_base_url="https://api.fireworks.ai/inference/v1",
            openai_model="accounts/fireworks/models/deepseek-v4-flash-0731",
        ),
    )

    async def fake_mcp():
        return object()

    monkeypatch.setattr(runtime, "get_knowledge_mcp_server", fake_mcp)
    monkeypatch.setattr(runtime.Runner, "run_streamed", fake_run_streamed)

    events = [event async for event in runtime.stream_turn("第一问", session_id="sid-runtime")]

    assert events[0]["type"] == "session"
    assert events[-1]["type"] == "final"
    assert captured["question"] == "第一问"
    assert captured["session"] is runtime._OPENAI_SESSIONS["sid-runtime"]
    assert captured["agent_name"] == "BaiCao Graph Specialist"


@pytest.mark.asyncio
async def test_stream_turn_reuses_openai_session(monkeypatch):
    from types import SimpleNamespace

    from app.services.chat_agent_runtime import runtime

    sessions: list[object] = []

    class FakeResult:
        async def stream_events(self):
            if False:
                yield None

    def fake_run_streamed(agent, question, session=None):
        sessions.append(session)
        return FakeResult()

    monkeypatch.setattr(
        runtime,
        "get_settings",
        lambda: SimpleNamespace(
            openai_api_key="fw-test",
            openai_base_url="https://api.fireworks.ai/inference/v1",
            openai_model="accounts/fireworks/models/deepseek-v4-flash-0731",
        ),
    )
    async def fake_mcp():
        return object()

    monkeypatch.setattr(runtime, "get_knowledge_mcp_server", fake_mcp)
    monkeypatch.setattr(runtime.Runner, "run_streamed", fake_run_streamed)

    async for _ in runtime.stream_turn("第一问", session_id="sid-keep-all"):
        pass
    async for _ in runtime.stream_turn("第二问", session_id="sid-keep-all"):
        pass

    assert len(sessions) == 2
    assert sessions[0] is sessions[1]
