"""问答循环中的 system_one 判定。

state 只放本轮事实。问题和标准写在本文件，模型不能改。
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, Literal

from pydantic_ai import ModelRetry, RunContext, Tool
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from typesafe_sdk import Choice, Noul, NoulCriteria, Score

from ..system_one import SystemOneJudge

ProfileName = Literal["intake", "evidence", "claim"]

# 单次判定请求必须有界。最近 6 次图工具、单次结果 8000 字；超出的部分不能再当成完整子图。
_MAX_GRAPH_RECORDS = 6
_MAX_RESULT_CHARS = 8000
_MAX_FOCUS_CHARS = 500
_MAX_DRAFT_CHARS = 4000

# noul 是「是」的概率。中间区间不当成是或否。Choice 置信度过低时不采用标签。
_NOUL_YES = 0.7
_NOUL_NO = 0.3
_CHOICE_MIN_CONFIDENCE = 0.5
_ENOUGH_EVIDENCE_SCORE = 2.0
_TOO_VAGUE_SCORE = 0.5

GRAPH_TOOL_NAMES = frozenset(
    {"search_nodes", "search_edges", "expand_neighbors", "lookup_nodes"}
)

_INCOMPLETE = "判定结果不完整。不要据此发布结论，也不要把它当成已经判定过。"

JUDGMENT_QUESTIONS: dict[str, dict[str, Choice | Noul | Score]] = {
    "intake": {
        "任务": Choice(
            instructions={
                "问题": "这一轮主要要做什么？",
                "关注点": "按用户的主要诉求判断，不按文中顺带提到的每一个词。",
            },
            criteria={
                "图谱检索": {
                    "含义": "要用已入库图谱回答实体、关系、属性或出处；问题带个人情况时，只要能用图谱里的记载回答，也算这一类",
                    "不包括": "诊断病情或开处方",
                    "示例": ["乌梅丸的组成", "黄芪的性味归经", "我气虚，该吃黄芪吗"],
                },
                "需要澄清": {
                    "含义": "没有可检索的名称，或有多个互斥对象",
                    "示例": ["这个呢", "它能治什么"],
                },
                "超出图谱问答": {
                    "含义": "要求诊断病情或开处方",
                    "不包括": "询问图谱里已有的性味、归经、功效、主治或组成，即使问题带个人情况",
                    "示例": ["我这是什么病", "帮我开一张方"],
                },
            },
        ),
        "需要检索": Noul(
            instructions="回答前是否必须先调用图工具？",
            criteria=NoulCriteria(
                true="问题指向具体实体、关系、属性或出处，且图工具记录里还没有对应结果",
                false="已明确超出图谱问答，或追问的内容已经在图工具记录里",
            ),
        ),
        "问题具体程度": Score(
            instructions="问题里的检索锚点有多具体？",
            criteria=[
                "没有可检索的名称或标识",
                "有名称，但可能对应多类实体",
                "有明确的中文名称或标识，可以直接检索",
            ],
        ),
    },
    "evidence": {
        "锚点已定位": Noul(
            instructions="图工具记录里是否已经有与问题对应的节点标识？",
            criteria=NoulCriteria(
                true="结果里有标签相符的节点标识",
                false="没有命中，或只有名称相似但标签不符的节点",
            ),
        ),
        "证据足够作答": Noul(
            instructions={
                "问题": "现有子图是否够支撑这一问？",
                "关注点": "只看图工具记录，不使用模型自己的药理知识。",
            },
            criteria=NoulCriteria(
                true={
                    "含义": "所问的关系、属性或证据邻居已经在结果里",
                    "示例": ["问组成，结果里有组成药", "问出处，结果里有来源或导入源"],
                },
                false={
                    "含义": "结果为空、只有名称，或还缺问题所问的那一跳",
                    "示例": ["只搜到方剂，还没展开组成", "没有任何节点"],
                },
            ),
        ),
        "下一步": Choice(
            instructions="根据现有图工具记录，下一步做什么？",
            criteria={
                "继续检索": "锚点已有或名称可换，但所问关系或证据还不在结果里",
                "可以作答": "所问内容已经在子图里",
                "说明没有图谱证据": "换过名称和标识后仍没有可用节点，或子图里明确没有该关系",
            },
        ),
        "证据充分度": Score(
            instructions="现有子图离「能回答且能给出处」还差多少？",
            criteria=[
                "没有可用节点",
                "有锚点，缺所问的关系或属性",
                "所问的关系或属性已在子图里",
                "所问内容以及出处邻居都在子图里",
            ],
        ),
    },
    "claim": {
        "超出已检索子图": Noul(
            instructions="草稿是否写出了图工具记录里没有的实体、关系、剂量或出处？",
            criteria=NoulCriteria(
                true="出现了记录中找不到的名称、关系、剂量、书名或文献",
                false="只复述记录里已有的内容，或明确写了当前没有图谱证据",
            ),
        ),
        "编造剂量或出处": Noul(
            instructions="草稿是否新增了图工具记录里没有的剂量或出处？",
            criteria=NoulCriteria(
                true="写出了记录中没有的剂量、书名、文献或来源",
                false="没有新增剂量或出处",
            ),
        ),
        "可以发布": Noul(
            instructions={
                "问题": "这份草稿能否作为给用户的最终结论？",
                "关注点": "没有图谱证据时，只有明确写出这一点才算可以发布。",
            },
            criteria=NoulCriteria(
                true="没有超出子图，并且要么回答了问题，要么明确说明没有图谱证据",
                false="含子图之外的断言、替用户决定该不该用某药，或在没有证据时给了肯定结论",
            ),
        ),
    },
}

REQUIRED_ANSWERS: dict[str, tuple[str, ...]] = {
    profile: tuple(questions) for profile, questions in JUDGMENT_QUESTIONS.items()
}


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "…（已截断）"


def _parse_maybe(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text.startswith(("{", "[")):
        return text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _fit(value: Any) -> Any:
    parsed = _parse_maybe(value)
    if isinstance(parsed, str):
        return _clip(parsed, _MAX_RESULT_CHARS)
    try:
        encoded = json.dumps(parsed, ensure_ascii=False, default=str)
    except TypeError:
        return _clip(str(parsed), _MAX_RESULT_CHARS)
    if len(encoded) <= _MAX_RESULT_CHARS:
        return json.loads(encoded)
    return _clip(encoded, _MAX_RESULT_CHARS)


def _prompt_text(prompt: Any) -> str:
    if isinstance(prompt, str):
        return prompt.strip()
    if isinstance(prompt, Sequence) and not isinstance(prompt, (str, bytes)):
        chunks = [item.strip() for item in prompt if isinstance(item, str) and item.strip()]
        return "\n".join(chunks)
    return ""


def graph_tool_records(messages: Sequence[Any]) -> list[dict[str, Any]]:
    pending: dict[str, dict[str, Any]] = {}
    ordered: list[dict[str, Any]] = []
    for message in messages:
        parts = getattr(message, "parts", None) or []
        for part in parts:
            if isinstance(part, ToolCallPart) and part.tool_name in GRAPH_TOOL_NAMES:
                call_id = str(part.tool_call_id or f"{part.tool_name}-{id(part)}")
                record = {"工具": part.tool_name, "参数": _fit(part.args)}
                pending[call_id] = record
                ordered.append(record)
            elif isinstance(part, ToolReturnPart) and part.tool_name in GRAPH_TOOL_NAMES:
                call_id = str(part.tool_call_id or "")
                record = pending.get(call_id)
                if record is None:
                    record = {"工具": part.tool_name, "参数": {}}
                    ordered.append(record)
                record["结果"] = _fit(part.content)
    return ordered[-_MAX_GRAPH_RECORDS:]


def execution_state(
    messages: Sequence[Any],
    prompt: Any,
    *,
    focus: str | None,
    draft: str | None,
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "用户问题": _prompt_text(prompt),
        "图工具记录": graph_tool_records(messages),
    }
    if focus and focus.strip():
        state["关注点"] = _clip(focus.strip(), _MAX_FOCUS_CHARS)
    if draft and draft.strip():
        state["待核对结论"] = _clip(draft.strip(), _MAX_DRAFT_CHARS)
    return state


def _noul_stance(answers: Mapping[str, Any], name: str) -> str:
    raw = answers.get(name)
    if not isinstance(raw, dict):
        return "缺失"
    value = raw.get("noul")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "缺失"
    if value >= _NOUL_YES:
        return "是"
    if value <= _NOUL_NO:
        return "否"
    return "不确定"


def _choice_label(answers: Mapping[str, Any], name: str) -> str:
    raw = answers.get(name)
    if not isinstance(raw, dict):
        return "缺失"
    label = raw.get("choice")
    confidence = raw.get("confidence")
    if not isinstance(label, str) or not label:
        return "缺失"
    if (
        isinstance(confidence, (int, float))
        and not isinstance(confidence, bool)
        and confidence < _CHOICE_MIN_CONFIDENCE
    ):
        return "不确定"
    return label


def _score_value(answers: Mapping[str, Any], name: str) -> float | None:
    raw = answers.get(name)
    if not isinstance(raw, dict):
        return None
    value = raw.get("score")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _missing(profile: str, answers: Mapping[str, Any]) -> bool:
    return any(name not in answers for name in REQUIRED_ANSWERS[profile])


def follow_instruction(profile: str, answers: Mapping[str, Any]) -> str:
    """把 system_one 的答案收成模型必须执行的下一步。"""
    if profile not in REQUIRED_ANSWERS or _missing(profile, answers):
        return _INCOMPLETE
    if profile == "intake":
        return _follow_intake(answers)
    if profile == "evidence":
        return _follow_evidence(answers)
    if profile == "claim":
        return _follow_claim(answers)
    return _INCOMPLETE


def _follow_intake(answers: Mapping[str, Any]) -> str:
    task = _choice_label(answers, "任务")
    need_search = _noul_stance(answers, "需要检索")
    specificity = _score_value(answers, "问题具体程度")
    if "缺失" in {task, need_search} or specificity is None:
        return _INCOMPLETE
    if task == "不确定" or need_search == "不确定":
        return "判定不稳定。先向用户确认要查的具体名称，不要调用图工具，也不要作答。"
    if task == "超出图谱问答":
        return "不要调用图工具。直接说明本系统只根据已入库图谱回答，不提供诊断或处方。"
    if task == "需要澄清":
        return "先向用户追问要查的药材、方剂或概念，不要调用图工具。"
    if task == "图谱检索" and need_search == "是" and specificity < _TOO_VAGUE_SCORE:
        return "问题里还没有可检索的名称。先追问药材、方剂或概念，不要调用图工具。"
    if task == "图谱检索" and need_search == "是":
        return "先 search_nodes 定位锚点，不要直接作答。"
    if task == "图谱检索" and need_search == "否":
        return "可以沿用已有图工具结果。写出给用户的结论前调用 judge，profile=claim。"
    return "判定结果无法执行。先向用户确认要查的名称，不要作答。"


def _follow_evidence(answers: Mapping[str, Any]) -> str:
    anchored = _noul_stance(answers, "锚点已定位")
    enough = _noul_stance(answers, "证据足够作答")
    nxt = _choice_label(answers, "下一步")
    richness = _score_value(answers, "证据充分度")
    if "缺失" in {anchored, enough, nxt} or richness is None:
        return _INCOMPLETE
    if nxt == "不确定":
        return (
            "证据判定不稳定。换一个更精确的名称或标识再检索一次；"
            "若已经换过，就说明当前没有图谱证据。"
        )
    if nxt == "说明没有图谱证据" and enough == "是" and richness >= _ENOUGH_EVIDENCE_SCORE:
        return (
            "判定互相矛盾。不要发布肯定结论；再核对一次锚点和邻居，"
            "若结果不变就说明当前没有图谱证据。"
        )
    if nxt == "说明没有图谱证据":
        return "不要编造。最终结论必须写明当前没有图谱证据。发布前调用 judge，profile=claim。"
    if nxt == "可以作答" and enough == "是" and richness >= _ENOUGH_EVIDENCE_SCORE:
        return "可以组织结论。写出最终文字前调用 judge，profile=claim，draft 放入准备发布的全文。"
    if anchored == "否":
        return "不要作答。先用 search_nodes 换中文名称、精确标识或标签定位锚点。"
    return "不要作答。按缺的那一跳继续 expand_neighbors、search_edges 或 lookup_nodes。"


def _follow_claim(answers: Mapping[str, Any]) -> str:
    beyond = _noul_stance(answers, "超出已检索子图")
    invented = _noul_stance(answers, "编造剂量或出处")
    publish = _noul_stance(answers, "可以发布")
    if "缺失" in {beyond, invented, publish}:
        return _INCOMPLETE
    if beyond == "否" and invented == "否" and publish == "是":
        return "可以发布这份草稿。"
    return (
        "不要发布。删掉子图里没有的实体、关系、剂量和出处，"
        "或改成明确说明没有图谱证据，然后再次调用 judge，profile=claim。"
    )


def make_judge_tool(judge: SystemOneJudge) -> Tool:
    async def judge_tool(
        ctx: RunContext[object],
        profile: ProfileName,
        focus: str | None = None,
        draft: str | None = None,
    ) -> dict[str, Any]:
        """用固定的 Choice、Noul、Score 判定当前这一轮。

        问题和标准已写死。intake 在第一次图工具之前；evidence 在图工具返回之后；
        claim 在发布前，draft 放准备给用户看的全文。按返回的 follow 执行。
        """
        if profile == "claim" and not (draft and draft.strip()):
            raise ModelRetry("profile=claim 时必须把准备发布的全文放进 draft。")
        questions = JUDGMENT_QUESTIONS.get(profile)
        if questions is None:
            raise ModelRetry("profile 只能是 intake、evidence 或 claim。")
        state = execution_state(ctx.messages, ctx.prompt, focus=focus, draft=draft)
        payload = await judge.ask(state, questions)
        answers = payload.get("answers")
        payload["profile"] = profile
        payload["follow"] = follow_instruction(
            profile, answers if isinstance(answers, dict) else {}
        )
        return payload

    judge_tool.__name__ = "judge"
    return Tool(
        judge_tool,
        name="judge",
        sequential=True,
        description=(
            "对当前这一轮做结构化判定。profile 只能是 intake、evidence 或 claim。"
            "不要在参数里写选项或评分标准。"
            "intake：第一次图工具之前。"
            "evidence：每次图工具返回后，决定继续检索还是作答之前。"
            "claim：把准备给用户看的全文放进 draft，发布前调用。"
            "state 由运行时填入用户问题和图工具结果。必须按返回的 follow 行动。"
        ),
    )
