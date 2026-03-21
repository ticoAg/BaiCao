# Chat Service - 智能问答服务
# 支持 LLM 流式（OpenAI/Anthropic via LangChain）和规则引擎 fallback

import json
import re
from typing import Optional, AsyncIterator, TypedDict, List
from uuid import UUID, uuid4
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import HerbModel, SourceModel
from ..kg.graph_service import graph_service
from .llm_client import stream_llm, is_llm_available


# ========== Constants ==========
HERB_KEYWORDS: List[str] = [
    "人参", "黄芪", "当归", "陈皮", "甘草", "枸杞", "红枣", "川芎", "白术", "茯苓",
    "三七", "丹参", "党参", "黄连", "金银花", "连翘", "板蓝根", "大青叶", "薄荷", "荆芥"
]

DEFAULT_HERB: str = "陈皮"


# ========== Response Schemas ==========
class ReasoningChainStep(TypedDict):
    step: int
    description: str
    entities: List[str]
    relations: List[str]
    confidence: float


class Source(TypedDict):
    id: str
    name: str
    citation: str


class GraphData(TypedDict):
    center: Optional[dict]
    nodes: List[dict]
    edges: List[dict]


class QuestionAnswerResponse(TypedDict):
    answer: str
    reasoning_chain: List[ReasoningChainStep]
    sources: List[Source]
    graph_data: GraphData
    session_id: str


@dataclass
class EntityPattern:
    keywords: List[str]
    pattern: Optional[re.Pattern] = None

    def __post_init__(self):
        if self.pattern is None:
            keyword_regex = "|".join(re.escape(k) for k in self.keywords)
            self.pattern = re.compile(keyword_regex)


herb_entity_pattern = EntityPattern(keywords=HERB_KEYWORDS)


class ChatService:
    """智能问答服务 - 支持 LLM 流式和规则引擎双模式"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ============ 同步问答（原有接口，保留兼容） ============

    async def answer_question(self, question: str, session_id: Optional[str] = None) -> dict:
        """同步问答 - LLM 可用时调用 LLM，否则使用规则引擎"""
        entities = await self._extract_entities(question)
        graph_data = await self._query_knowledge_graph(entities)
        reasoning_chain = await self._build_reasoning_chain(question, entities, graph_data)

        # LLM 可用时使用 LLM 生成答案
        if is_llm_available():
            graph_context = self._format_graph_context(graph_data)
            answer_parts = []
            async for token in stream_llm(question, graph_context):
                answer_parts.append(token)
            answer = "".join(answer_parts)
        else:
            answer = await self._generate_answer(question, entities, graph_data, reasoning_chain)

        sources = await self._collect_sources(graph_data)

        response = {
            "answer": answer,
            "reasoning_chain": reasoning_chain,
            "sources": sources,
            "graph_data": graph_data,
            "session_id": session_id or str(uuid4())
        }

        self._validate_response(response)
        return response

    # ============ SSE 流式问答 ============

    async def answer_question_stream(
        self, question: str, session_id: Optional[str] = None
    ) -> AsyncIterator[dict]:
        """SSE 流式问答 - 逐步返回推理链、tokens、来源

        Yields SSE 事件:
            {type: "session", data: {session_id}}
            {type: "reasoning", data: {reasoning_chain}}
            {type: "sources", data: {sources}}
            {type: "token", data: {token}}
            {type: "done", data: {}}
            {type: "error", data: {message}}
        """
        sid = session_id or str(uuid4())

        # 1. 发送 session_id
        yield {"type": "session", "data": {"session_id": sid}}

        # 2. 提取实体 + 查询图谱
        entities = await self._extract_entities(question)
        graph_data = await self._query_knowledge_graph(entities)

        # 3. 发送推理链
        reasoning_chain = await self._build_reasoning_chain(question, entities, graph_data)
        yield {"type": "reasoning", "data": {"reasoning_chain": reasoning_chain}}

        # 4. 发送来源
        sources = await self._collect_sources(graph_data)
        yield {"type": "sources", "data": {"sources": sources}}

        # 5. 流式回答
        if is_llm_available():
            graph_context = self._format_graph_context(graph_data)
            try:
                async for token in stream_llm(question, graph_context):
                    yield {"type": "token", "data": {"token": token}}
            except Exception as e:
                yield {"type": "error", "data": {"message": str(e)}}
                # Fallback to rule engine
                answer = await self._generate_answer(
                    question, entities, graph_data, reasoning_chain
                )
                yield {"type": "token", "data": {"token": answer}}
        else:
            # 规则引擎 fallback（一次性发送）
            answer = await self._generate_answer(
                question, entities, graph_data, reasoning_chain
            )
            yield {"type": "token", "data": {"token": answer}}

        # 6. 完成
        yield {"type": "done", "data": {}}

    # ============ 图谱上下文格式化 ============

    def _format_graph_context(self, graph_data: dict) -> str:
        """将图谱数据格式化为 LLM 可读的文本上下文"""
        parts = []
        center = graph_data.get("center")
        if center:
            parts.append(f"核心实体: {center.get('name', '未知')} (类型: {', '.join(center.get('labels', []))})")
            if center.get("category"):
                parts.append(f"  分类: {center['category']}")
            if center.get("source"):
                parts.append(f"  数据来源: {center['source']}")
            if center.get("status"):
                parts.append(f"  验证状态: {center['status']}")

        edges = graph_data.get("edges", [])
        if edges:
            parts.append("\n关系:")
            for edge in edges[:20]:  # 限制上下文长度
                rel_type = edge.get("type") or edge.get("rel_type", "")
                target = edge.get("target", {})
                target_name = target.get("name", "") if isinstance(target, dict) else str(target)
                if rel_type and target_name:
                    parts.append(f"  - {rel_type} -> {target_name}")

        nodes = graph_data.get("nodes", [])
        if nodes:
            parts.append(f"\n相关节点 ({len(nodes)} 个):")
            for node in nodes[:15]:
                node_name = node.get("name", "")
                node_labels = ", ".join(node.get("labels", []))
                if node_name:
                    parts.append(f"  - {node_name} ({node_labels})")

        return "\n".join(parts) if parts else "未找到相关知识图谱信息"

    # ============ 内部方法（保持不变） ============

    def _validate_response(self, response: dict) -> None:
        required_keys = {"answer", "reasoning_chain", "sources", "graph_data", "session_id"}
        missing_keys = required_keys - set(response.keys())
        if missing_keys:
            raise ValueError(f"Response missing required keys: {missing_keys}")

        if not isinstance(response["answer"], str):
            raise ValueError("Response 'answer' must be a string")

        if not isinstance(response["reasoning_chain"], list):
            raise ValueError("Response 'reasoning_chain' must be a list")

        for i, step in enumerate(response["reasoning_chain"]):
            if not isinstance(step, dict):
                raise ValueError(f"Reasoning chain step {i} must be a dict")
            if "step" not in step or "description" not in step or "confidence" not in step:
                raise ValueError(f"Reasoning chain step {i} missing required fields")

        if not isinstance(response["sources"], list):
            raise ValueError("Response 'sources' must be a list")

        if not isinstance(response["graph_data"], dict):
            raise ValueError("Response 'graph_data' must be a dict")

        if not isinstance(response["session_id"], str):
            raise ValueError("Response 'session_id' must be a string")

    async def _extract_entities(self, question: str) -> list[str]:
        matches = herb_entity_pattern.pattern.findall(question)
        entities = list(dict.fromkeys(matches))
        return entities if entities else [DEFAULT_HERB]

    async def _query_knowledge_graph(self, entities: list[str]) -> dict:
        if not entities:
            return {"center": None, "nodes": [], "edges": []}

        graph = await graph_service.get_herb_graph(entities[0], depth=2)

        all_nodes = []
        all_edges = []

        for entity in entities[1:]:
            try:
                entity_graph = await graph_service.get_herb_graph(entity, depth=1)
                if entity_graph["center"]:
                    all_nodes.append(entity_graph["center"])
                all_nodes.extend(entity_graph["nodes"])
                all_edges.extend(entity_graph["edges"])
            except Exception:
                pass

        return {
            "center": graph.get("center"),
            "nodes": graph.get("nodes", []) + all_nodes,
            "edges": graph.get("edges", []) + all_edges
        }

    async def _build_reasoning_chain(
        self, question: str, entities: list[str], graph_data: dict
    ) -> list[dict]:
        chain = []

        question_type = self._classify_question(question)
        chain.append({
            "step": 1,
            "description": f"识别问题类型：{question_type}",
            "entities": entities,
            "confidence": 0.95
        })

        if graph_data.get("center"):
            chain.append({
                "step": 2,
                "description": "在知识图谱中查找相关实体",
                "entities": [graph_data["center"].get("name", "")] if graph_data.get("center") else [],
                "confidence": 0.90
            })

        edges = graph_data.get("edges", [])
        if edges:
            rel_types = list(set([e.get("type", e.get("rel_type", "")) for e in edges if e]))
            chain.append({
                "step": 3,
                "description": f"分析实体间关系：{', '.join(rel_types[:3])}",
                "relations": rel_types[:3],
                "confidence": 0.85
            })

        chain.append({
            "step": 4,
            "description": "综合图谱信息生成回答" + (" (LLM)" if is_llm_available() else " (规则引擎)"),
            "entities": [],
            "confidence": 0.80
        })

        return chain

    def _classify_question(self, question: str) -> str:
        if any(k in question for k in ["功效", "作用", "能做什么", "有什么效果"]):
            return "功效查询"
        elif any(k in question for k in ["主治", "治疗", "用于", "治疗什么"]):
            return "主治查询"
        elif any(k in question for k in ["成分", "含有", "包含什么"]):
            return "成分查询"
        elif any(k in question for k in ["性味", "味道", "味道如何"]):
            return "性味查询"
        elif any(k in question for k in ["归经", "进入", "作用于"]):
            return "归经查询"
        elif any(k in question for k in ["用法", "如何服用", "剂量"]):
            return "用法查询"
        elif any(k in question for k in ["禁忌", "注意", "副作用"]):
            return "禁忌查询"
        else:
            return "综合查询"

    async def _generate_answer(
        self, question: str, entities: list[str], graph_data: dict, reasoning_chain: list[dict]
    ) -> str:
        """规则引擎生成回答（fallback）"""
        if not entities:
            return "抱歉，我无法理解您的问题。请尝试询问关于特定药材的信息。"

        herb_name = entities[0]
        center = graph_data.get("center")

        if not center:
            return f"抱歉，我在知识图谱中未找到关于「{herb_name}」的信息。"

        parts = [f"关于「{herb_name}」的信息："]

        if center.get("category"):
            parts.append(f"- 分类：{center.get('category')}")

        edges = graph_data.get("edges", [])

        efficacies = []
        for edge in edges:
            rel_type = edge.get("type") or edge.get("rel_type", "")
            if "EFFICACY" in rel_type.upper() or "功效" in str(edge):
                target = edge.get("target") or {}
                if target.get("name"):
                    efficacies.append(target["name"])

        if efficacies:
            parts.append(f"- 主要功效：{', '.join(set(efficacies[:5]))}")

        flavors = []
        meridians = []
        for edge in edges:
            rel_type = edge.get("type") or edge.get("rel_type", "")
            if "FLAVOR" in rel_type.upper():
                flavors.append(edge.get("target", {}).get("name", ""))
            if "MERIDIAN" in rel_type.upper():
                meridians.append(edge.get("target", {}).get("name", ""))

        if flavors:
            parts.append(f"- 性味：{', '.join(set(flavors))}")
        if meridians:
            parts.append(f"- 归经：{', '.join(set(meridians))}")

        if center.get("source"):
            parts.append(f"- 数据来源：{center.get('source')}")

        status = center.get("status", "pending")
        status_text = {"pending": "待验证", "verified": "已验证", "rejected": "已拒绝"}.get(status, status)
        parts.append(f"- 信息状态：{status_text}")

        return "\n".join(parts)

    async def _collect_sources(self, graph_data: dict) -> list[dict]:
        sources = []
        seen_ids = set()

        center = graph_data.get("center")
        if center and center.get("source"):
            source_name = center["source"]
            if source_name not in seen_ids:
                seen_ids.add(source_name)
                sources.append({
                    "id": str(uuid4()),
                    "name": source_name,
                    "citation": f"来源：{source_name}"
                })

        return sources

    async def create_session(self, user_id: Optional[str] = None) -> dict:
        return {
            "id": str(uuid4()),
            "user_id": user_id,
            "messages": [],
            "created_at": "now"
        }

    async def get_session(self, session_id: str) -> Optional[dict]:
        return None


chat_service = ChatService
