import json
from types import SimpleNamespace

import pytest

from app.services.chat_agent_runtime.openai_event_adapter import adapt_openai_stream


@pytest.mark.asyncio
async def test_adapt_openai_stream_maps_tool_and_answer():
    events = [
        SimpleNamespace(
            type="run_item_stream_event",
            item=SimpleNamespace(
                type="tool_call_item",
                raw_item=SimpleNamespace(
                    name="search_nodes",
                    call_id="call-1",
                    arguments='{"query":"乌梅丸"}',
                ),
            ),
        ),
        SimpleNamespace(
            type="run_item_stream_event",
            item=SimpleNamespace(
                type="tool_call_output_item",
                raw_item=SimpleNamespace(call_id="call-1"),
                output={
                    "type": "text",
                    "text": json.dumps(
                        [{"id": "formula-乌梅丸", "name": "乌梅丸", "labels": ["方剂"]}],
                        ensure_ascii=False,
                    ),
                },
            ),
        ),
        SimpleNamespace(type="raw_response_event", data=SimpleNamespace(delta="思考过程不应出现")),
        SimpleNamespace(
            type="run_item_stream_event",
            item=SimpleNamespace(
                type="message_output_item",
                raw_item=SimpleNamespace(content=[SimpleNamespace(text="乌梅丸是一张方剂。")]),
            ),
        ),
    ]

    async def _iter():
        for item in events:
            yield item

    adapted = [event async for event in adapt_openai_stream(_iter(), session_id="sid-1", turn_id="turn-1")]
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
    assert adapted[-1]["data"]["evidence"] == []
    assert "思考过程" not in adapted[-1]["data"]["answer"]


@pytest.mark.asyncio
async def test_adapt_openai_stream_matches_output_to_last_running_tool():
    events = [
        SimpleNamespace(
            type="run_item_stream_event",
            item=SimpleNamespace(
                type="tool_call_item",
                raw_item=SimpleNamespace(name="expand_neighbors", call_id="c1", arguments="{}"),
            ),
        ),
        SimpleNamespace(
            type="run_item_stream_event",
            item=SimpleNamespace(
                type="tool_call_output_item",
                raw_item=SimpleNamespace(),
                call_id=None,
                output={"center": {"id": "formula-乌梅丸", "name": "乌梅丸"}, "nodes": [], "edges": []},
            ),
        ),
    ]

    async def _iter():
        for item in events:
            yield item

    adapted = [event async for event in adapt_openai_stream(_iter(), session_id="s", turn_id="t")]
    result = next(event for event in adapted if event["type"] == "tool_result")
    assert result["data"]["tool_name"] == "expand_neighbors"
    assert result["data"]["result_summary"] == "返回 0 个节点、0 条关系"


@pytest.mark.asyncio
async def test_adapt_openai_stream_builds_evidence_from_graph_state_only():
    events = [
        SimpleNamespace(
            type="run_item_stream_event",
            item=SimpleNamespace(
                type="tool_call_item",
                raw_item=SimpleNamespace(
                    name="expand_neighbors",
                    call_id="call-exp",
                    arguments='{"node_id":"药材:乌梅","depth":1}',
                ),
            ),
        ),
        SimpleNamespace(
            type="run_item_stream_event",
            item=SimpleNamespace(
                type="tool_call_output_item",
                raw_item=SimpleNamespace(call_id="call-exp"),
                output={
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
                            "target": {
                                "id": "证据:suyang-002",
                                "name": "证据:suyang-002",
                                "labels": ["证据"],
                            },
                        },
                        {
                            "rel_type": "来源于",
                            "source": {
                                "id": "证据:suyang-002",
                                "name": "证据:suyang-002",
                                "labels": ["证据"],
                            },
                            "target": {
                                "id": "来源:道医苏子阳",
                                "name": "道医苏子阳",
                                "labels": ["来源"],
                            },
                        },
                    ],
                },
            ),
        ),
        SimpleNamespace(
            type="run_item_stream_event",
            item=SimpleNamespace(
                type="message_output_item",
                raw_item=SimpleNamespace(
                    content=[
                        SimpleNamespace(
                            text=(
                                "乌梅味酸。出处：本草纲目伪引用，"
                                "以及 [cite:伪造证据] 都不应进入 evidence。"
                            )
                        )
                    ]
                ),
            ),
        ),
    ]

    async def _iter():
        for item in events:
            yield item

    adapted = [event async for event in adapt_openai_stream(_iter(), session_id="sid-2", turn_id="turn-2")]
    final = next(event for event in adapted if event["type"] == "final")
    assert [event["type"] for event in adapted if event["type"] == "final"] == ["final"]
    assert final["data"]["evidence"] == [
        {
            "entity_id": "药材:乌梅",
            "evidence_id": "证据:suyang-002",
            "snippet": "乌梅味酸，能涩肠止痢。",
            "source_id": "来源:道医苏子阳",
            "source_name": "道医苏子阳",
        }
    ]
    assert "伪造" not in str(final["data"]["evidence"])
    assert "本草纲目" not in str(final["data"]["evidence"])
