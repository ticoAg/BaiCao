import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
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
async def test_stream_turn_builds_agent_with_real_runtime_dependencies(monkeypatch):
    from app.services.chat_agent_runtime import runtime

    captured = {}

    class FakeAgent:
        async def astream_events(self, payload, config=None, version="v2"):
            captured["payload"] = payload
            captured["config"] = config
            captured["version"] = version
            yield {
                "event": "on_chain_end",
                "name": "LangGraph",
                "data": {
                    "output": {
                        "messages": [AIMessage(content=[{"type": "text", "text": "done"}])],
                    }
                },
            }

    def fake_create_deep_agent(*, model, tools, system_prompt, checkpointer):
        captured["model"] = model
        captured["tools"] = tools
        captured["system_prompt"] = system_prompt
        captured["checkpointer"] = checkpointer
        return FakeAgent()

    monkeypatch.setattr(runtime, "get_chat_model", lambda: object())
    monkeypatch.setattr(runtime, "build_graph_tools", lambda: ["search_nodes"])
    monkeypatch.setattr(runtime, "build_graph_specialist_system_prompt", lambda: "prompt")
    monkeypatch.setattr(runtime, "create_deep_agent", fake_create_deep_agent)

    events = [event async for event in runtime.stream_turn("第一问", session_id="sid-runtime")]

    assert events[0]["type"] == "session"
    assert events[-1]["type"] == "final"
    assert captured["tools"] == ["search_nodes"]
    assert captured["system_prompt"] == "prompt"
    assert captured["checkpointer"] is runtime._SESSION_MANAGER.checkpointer
    assert len(captured["payload"]["messages"]) == 1
    assert isinstance(captured["payload"]["messages"][0], HumanMessage)
    assert captured["payload"]["messages"][0].content == "第一问"
    assert captured["config"] == {"configurable": {"thread_id": "sid-runtime"}}
    assert captured["version"] == "v2"


@pytest.mark.asyncio
async def test_stream_turn_reuses_thread_id_without_manually_replaying_old_messages(monkeypatch):
    from app.services.chat_agent_runtime.runtime import stream_turn

    calls: list[dict] = []

    class FakeAgent:
        async def astream_events(self, payload, config=None, version="v2"):
            calls.append({"payload": payload, "config": config, "version": version})
            yield {
                "event": "on_chain_end",
                "name": "LangGraph",
                "data": {
                    "output": {
                        "messages": [AIMessage(content=[{"type": "text", "text": "ok"}])],
                    }
                },
            }

    monkeypatch.setattr("app.services.chat_agent_runtime.runtime.get_chat_model", lambda: object())
    monkeypatch.setattr("app.services.chat_agent_runtime.runtime.build_graph_tools", lambda: ["search_nodes"])
    monkeypatch.setattr("app.services.chat_agent_runtime.runtime.build_graph_specialist_system_prompt", lambda: "prompt")
    monkeypatch.setattr("app.services.chat_agent_runtime.runtime.create_deep_agent", lambda **_: FakeAgent())

    async for _ in stream_turn("第一问", session_id="sid-keep-all"):
        pass
    async for _ in stream_turn("第二问", session_id="sid-keep-all"):
        pass

    assert len(calls) == 2
    assert calls[0]["config"] == {"configurable": {"thread_id": "sid-keep-all"}}
    assert calls[1]["config"] == {"configurable": {"thread_id": "sid-keep-all"}}
    assert len(calls[0]["payload"]["messages"]) == 1
    assert len(calls[1]["payload"]["messages"]) == 1
    assert isinstance(calls[0]["payload"]["messages"][0], HumanMessage)
    assert isinstance(calls[1]["payload"]["messages"][0], HumanMessage)
    assert calls[0]["payload"]["messages"][0].content == "第一问"
    assert calls[1]["payload"]["messages"][0].content == "第二问"
