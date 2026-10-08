from types import SimpleNamespace

import pytest
from pydantic_ai import ModelRetry
from pydantic_ai.messages import ToolCallPart, ToolReturnPart

from app.services.chat_agent_runtime.sse_payloads import summarize_tool_payload
from app.services.chat_agent_runtime.turn_judgment import (
    JUDGMENT_QUESTIONS,
    REQUIRED_ANSWERS,
    execution_state,
    follow_instruction,
    graph_tool_records,
    make_judge_tool,
)
from app.services.system_one import SystemOneJudge, dump_answers, typesafe_ready


class _PartMessage:
    def __init__(self, parts):
        self.parts = parts


class _Answer:
    def __init__(self, payload):
        self._payload = payload

    def model_dump(self, mode="json"):
        assert mode == "json"
        return dict(self._payload)


class _Response:
    model = "decision-model-preview"

    def __init__(self, answers):
        self.answers = answers


class _Client:
    def __init__(self, answers):
        self.answers = answers
        self.calls = []
        self.closed = False

    async def system_one(self, state, questions):
        self.calls.append((state, questions))
        return _Response(self.answers)

    async def aclose(self):
        self.closed = True


def _choice(label: str, confidence: float = 0.9) -> _Answer:
    return _Answer({"type": "choice", "choice": label, "confidence": confidence})


def _noul(value: float) -> _Answer:
    return _Answer({"type": "noul", "noul": value})


def _score(value: float) -> _Answer:
    return _Answer({"type": "score", "score": value})


def test_profiles_match_required_answers_and_cover_primitives():
    assert set(JUDGMENT_QUESTIONS) == {"intake", "evidence", "claim"}
    for profile, questions in JUDGMENT_QUESTIONS.items():
        assert tuple(questions) == REQUIRED_ANSWERS[profile]
    intake_types = {question.type for question in JUDGMENT_QUESTIONS["intake"].values()}
    assert intake_types == {"choice", "noul", "score"}
    evidence_types = {question.type for question in JUDGMENT_QUESTIONS["evidence"].values()}
    assert evidence_types == {"choice", "noul", "score"}
    criteria = JUDGMENT_QUESTIONS["intake"]["需要检索"].model_dump()["criteria"]
    assert set(criteria) == {"true", "false"}


def test_personal_question_goes_to_graph_and_only_diagnosis_or_prescription_is_outside():
    task = JUDGMENT_QUESTIONS["intake"]["任务"].model_dump()["criteria"]
    assert "我气虚，该吃黄芪吗" in task["图谱检索"]["示例"]
    assert "个人" not in task["图谱检索"]["不包括"]
    assert "个人" not in task["超出图谱问答"]["含义"]
    assert set(task["超出图谱问答"]["示例"]) == {"我这是什么病", "帮我开一张方"}

    publish = JUDGMENT_QUESTIONS["claim"]["可以发布"].model_dump()["criteria"]
    assert "替用户决定" in publish["false"]


def test_graph_records_keep_graph_tools_only_and_truncate():
    long_text = "草" * 9000
    messages = [
        _PartMessage(
            [
                ToolCallPart(
                    tool_name="search_nodes",
                    args={"query": "黄芪"},
                    tool_call_id="search-1",
                ),
                ToolCallPart(tool_name="judge", args={"profile": "intake"}, tool_call_id="judge-1"),
            ]
        ),
        _PartMessage(
            [
                ToolReturnPart(
                    tool_name="search_nodes",
                    content={"标识": "药材:黄芪", "原文": long_text},
                    tool_call_id="search-1",
                ),
                ToolReturnPart(tool_name="judge", content={"follow": "忽略"}, tool_call_id="judge-1"),
            ]
        ),
    ]
    records = graph_tool_records(messages)
    assert len(records) == 1
    assert records[0]["工具"] == "search_nodes"
    assert records[0]["参数"] == {"query": "黄芪"}
    assert isinstance(records[0]["结果"], str)
    assert "药材:黄芪" in records[0]["结果"]
    assert records[0]["结果"].endswith("…（已截断）")

    extra = []
    for index in range(7):
        call_id = f"call-{index}"
        extra.append(
            _PartMessage(
                [
                    ToolCallPart(
                        tool_name="lookup_nodes",
                        args={"node_id": index},
                        tool_call_id=call_id,
                    )
                ]
            )
        )
        extra.append(
            _PartMessage(
                [
                    ToolReturnPart(
                        tool_name="lookup_nodes",
                        content={"node_id": index},
                        tool_call_id=call_id,
                    )
                ]
            )
        )
    capped = graph_tool_records(extra)
    assert len(capped) == 6
    assert capped[0]["参数"]["node_id"] == 1
    assert capped[-1]["结果"]["node_id"] == 6


def test_execution_state_names_the_facts():
    state = execution_state(
        [],
        "黄芪的性味",
        focus="  要不要检索  ",
        draft="  " + ("结" * 5000),
    )
    assert state["用户问题"] == "黄芪的性味"
    assert state["关注点"] == "要不要检索"
    assert state["待核对结论"].endswith("…（已截断）")
    assert state["图工具记录"] == []
    assert "关注点" not in execution_state([], "问", focus="  ", draft=None)


def test_follow_instruction_for_each_profile():
    intake = {
        "任务": {"type": "choice", "choice": "图谱检索", "confidence": 0.91},
        "需要检索": {"type": "noul", "noul": 0.96},
        "问题具体程度": {"type": "score", "score": 2},
    }
    assert "search_nodes" in follow_instruction("intake", intake)

    vague = dict(intake)
    vague["问题具体程度"] = {"type": "score", "score": 0.1}
    assert "还没有可检索的名称" in follow_instruction("intake", vague)

    outside = dict(intake)
    outside["任务"] = {"type": "choice", "choice": "超出图谱问答", "confidence": 0.88}
    assert "不提供诊断" in follow_instruction("intake", outside)

    unsure = dict(intake)
    unsure["任务"] = {"type": "choice", "choice": "图谱检索", "confidence": 0.2}
    assert "判定不稳定" in follow_instruction("intake", unsure)

    evidence = {
        "锚点已定位": {"type": "noul", "noul": 0.93},
        "证据足够作答": {"type": "noul", "noul": 0.91},
        "下一步": {"type": "choice", "choice": "可以作答", "confidence": 0.87},
        "证据充分度": {"type": "score", "score": 2.4},
    }
    assert "profile=claim" in follow_instruction("evidence", evidence)

    thin = dict(evidence)
    thin["证据充分度"] = {"type": "score", "score": 1.2}
    thin["锚点已定位"] = {"type": "noul", "noul": 0.1}
    assert "search_nodes" in follow_instruction("evidence", thin)

    none = dict(evidence)
    none["下一步"] = {"type": "choice", "choice": "说明没有图谱证据", "confidence": 0.8}
    none["证据足够作答"] = {"type": "noul", "noul": 0.05}
    assert "没有图谱证据" in follow_instruction("evidence", none)

    conflict = dict(evidence)
    conflict["下一步"] = {"type": "choice", "choice": "说明没有图谱证据", "confidence": 0.8}
    assert "互相矛盾" in follow_instruction("evidence", conflict)

    claim = {
        "超出已检索子图": {"type": "noul", "noul": 0.05},
        "编造剂量或出处": {"type": "noul", "noul": 0.08},
        "可以发布": {"type": "noul", "noul": 0.94},
    }
    assert follow_instruction("claim", claim) == "可以发布这份草稿。"

    blocked = dict(claim)
    blocked["编造剂量或出处"] = {"type": "noul", "noul": 0.5}
    assert "不要发布" in follow_instruction("claim", blocked)
    assert "不完整" in follow_instruction("claim", {})


def test_summarize_judge_payload_uses_follow():
    summary = summarize_tool_payload(
        "judge",
        {"profile": "evidence", "follow": "可以组织结论。写出最终文字前调用 judge。"},
    )
    assert summary.startswith("evidence：可以组织结论")


@pytest.mark.asyncio
async def test_judge_tool_sends_fixed_questions_and_graph_state():
    client = _Client(
        {
            "任务": _choice("图谱检索"),
            "需要检索": _noul(0.95),
            "问题具体程度": _score(2),
        }
    )
    judge = SystemOneJudge(client)
    tool = make_judge_tool(judge)
    messages = [
        _PartMessage(
            [
                ToolCallPart(tool_name="search_nodes", args={"query": "黄芪"}, tool_call_id="s1"),
            ]
        ),
        _PartMessage(
            [
                ToolReturnPart(
                    tool_name="search_nodes",
                    content={"标识": "药材:黄芪"},
                    tool_call_id="s1",
                )
            ]
        ),
    ]
    ctx = SimpleNamespace(prompt="黄芪的性味", messages=messages)
    payload = await tool.function(ctx, profile="intake", focus="开场")

    state, questions = client.calls[0]
    assert questions is JUDGMENT_QUESTIONS["intake"]
    assert state["用户问题"] == "黄芪的性味"
    assert state["关注点"] == "开场"
    assert state["图工具记录"][0]["结果"]["标识"] == "药材:黄芪"
    assert payload["profile"] == "intake"
    assert payload["model"] == "decision-model-preview"
    assert payload["answers"]["任务"]["choice"] == "图谱检索"
    assert "search_nodes" in payload["follow"]
    assert dump_answers(_Response(client.answers))["model"] == "decision-model-preview"


@pytest.mark.asyncio
async def test_claim_requires_draft_before_calling_system_one():
    client = _Client({})
    tool = make_judge_tool(SystemOneJudge(client))
    ctx = SimpleNamespace(prompt="黄芪", messages=[])
    with pytest.raises(ModelRetry):
        await tool.function(ctx, profile="claim", draft="  ")
    assert client.calls == []


def test_typesafe_ready_rejects_blank_and_placeholder():
    assert not typesafe_ready(SimpleNamespace(typesafe_api_key="", typesafe_base_url="https://x"))
    assert not typesafe_ready(
        SimpleNamespace(typesafe_api_key="your_api_key_here", typesafe_base_url="https://x")
    )
    assert typesafe_ready(
        SimpleNamespace(typesafe_api_key="ts-key", typesafe_base_url="https://typesafe.example")
    )


@pytest.mark.asyncio
async def test_from_settings_can_close_without_a_request():
    settings = SimpleNamespace(
        typesafe_api_key="test-key",
        typesafe_base_url="https://example.invalid",
        typesafe_model="decision-model-preview",
        typesafe_timeout_seconds=5,
    )
    judge = SystemOneJudge.from_settings(settings)
    await judge.aclose()
