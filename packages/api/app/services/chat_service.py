# Chat Service - 智能问答服务
# 使用 LangChain + OpenAI 实现基于知识图谱的智能问答

import json
import re
from typing import Optional, AsyncIterator, TypedDict, List
from uuid import UUID, uuid4
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import HerbModel, SourceModel
from ..kg.graph_service import graph_service


# ========== Refactor 1: Extract herb keywords as constant ==========
HERB_KEYWORDS: List[str] = [
    "人参", "黄芪", "当归", "陈皮", "甘草", "枸杞", "红枣", "川芎", "白术", "茯苓",
    "三七", "丹参", "党参", "黄连", "金银花", "连翘", "板蓝根", "大青叶", "薄荷", "荆芥"
]

# Default herb when no herb keyword is found in question
DEFAULT_HERB: str = "陈皮"


# ========== Refactor 3: Response structure validation schemas ==========
class ReasoningChainStep(TypedDict):
    """Schema for reasoning chain step"""
    step: int
    description: str
    entities: List[str]
    relations: List[str]
    confidence: float


class Source(TypedDict):
    """Schema for source reference"""
    id: str
    name: str
    citation: str


class GraphData(TypedDict):
    """Schema for graph data"""
    center: Optional[dict]
    nodes: List[dict]
    edges: List[dict]


class QuestionAnswerResponse(TypedDict):
    """Schema for question answer response"""
    answer: str
    reasoning_chain: List[ReasoningChainStep]
    sources: List[Source]
    graph_data: GraphData
    session_id: str


@dataclass
class EntityPattern:
    """Reusable entity extraction pattern"""
    keywords: List[str]
    pattern: Optional[re.Pattern] = None

    def __post_init__(self):
        if self.pattern is None:
            keyword_regex = "|".join(re.escape(k) for k in self.keywords)
            self.pattern = re.compile(keyword_regex)


# Entity pattern instance for herb extraction
herb_entity_pattern = EntityPattern(keywords=HERB_KEYWORDS)


class ChatService:
    """智能问答服务"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def answer_question(self, question: str, session_id: Optional[str] = None) -> dict:
        """
        回答用户问题

        返回格式:
        {
            "answer": str,                    # 回答内容
            "reasoning_chain": [              # 推理链
                {
                    "step": int,
                    "description": str,
                    "entities": [str],
                    "relations": [str],
                    "confidence": float
                }
            ],
            "sources": [                      # 引用的来源
                {
                    "id": str,
                    "name": str,
                    "citation": str
                }
            ],
            "graph_data": {                  # 相关图谱数据
                "nodes": [...],
                "edges": [...]
            }
        }
        """
        # 1. 解析问题，提取关键实体
        entities = await self._extract_entities(question)

        # 2. 查询知识图谱获取相关信息
        graph_data = await self._query_knowledge_graph(entities)

        # 3. 构建推理链
        reasoning_chain = await self._build_reasoning_chain(question, entities, graph_data)

        # 4. 生成回答（简化版本，实际应调用 LLM）
        answer = await self._generate_answer(question, entities, graph_data, reasoning_chain)

        # 5. 收集来源
        sources = await self._collect_sources(graph_data)

        response = {
            "answer": answer,
            "reasoning_chain": reasoning_chain,
            "sources": sources,
            "graph_data": graph_data,
            "session_id": session_id or str(uuid4())
        }

        # Refactor 3: Validate response structure before returning
        self._validate_response(response)

        return response

    def _validate_response(self, response: dict) -> None:
        """Validate response structure matches expected schema.

        Raises ValueError if response structure is invalid.
        """
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
        """从问题中提取关键实体（简化版）

        Uses herb_entity_pattern for efficient entity extraction.
        Falls back to DEFAULT_HERB when no herb keywords are found.
        """
        # Refactor 2: Use entity pattern for reusable extraction
        matches = herb_entity_pattern.pattern.findall(question)
        entities = list(dict.fromkeys(matches))  # Remove duplicates while preserving order

        return entities if entities else [DEFAULT_HERB]

    async def _query_knowledge_graph(self, entities: list[str]) -> dict:
        """查询知识图谱获取相关信息"""
        if not entities:
            return {"center": None, "nodes": [], "edges": []}

        # 获取第一个实体的图谱
        graph = await graph_service.get_herb_graph(entities[0], depth=2)

        # 收集相关节点
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
        self,
        question: str,
        entities: list[str],
        graph_data: dict
    ) -> list[dict]:
        """构建推理链"""
        chain = []

        # 步骤 1: 识别问题类型
        question_type = self._classify_question(question)
        chain.append({
            "step": 1,
            "description": f"识别问题类型：{question_type}",
            "entities": entities,
            "confidence": 0.95
        })

        # 步骤 2: 查找相关实体
        if graph_data.get("center"):
            chain.append({
                "step": 2,
                "description": f"在知识图谱中查找相关实体",
                "entities": [graph_data["center"].get("name", "")] if graph_data.get("center") else [],
                "confidence": 0.90
            })

        # 步骤 3: 分析关系
        edges = graph_data.get("edges", [])
        if edges:
            rel_types = list(set([e.get("type", e.get("rel_type", "")) for e in edges if e]))
            chain.append({
                "step": 3,
                "description": f"分析实体间关系：{', '.join(rel_types[:3])}",
                "relations": rel_types[:3],
                "confidence": 0.85
            })

        # 步骤 4: 综合结论
        chain.append({
            "step": 4,
            "description": "综合图谱信息生成回答",
            "entities": [],
            "confidence": 0.80
        })

        return chain

    def _classify_question(self, question: str) -> str:
        """分类问题类型"""
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
        self,
        question: str,
        entities: list[str],
        graph_data: dict,
        reasoning_chain: list[dict]
    ) -> str:
        """生成回答（简化版）"""
        if not entities:
            return "抱歉，我无法理解您的问题。请尝试询问关于特定药材的信息。"

        herb_name = entities[0]
        center = graph_data.get("center")

        if not center:
            return f"抱歉，我在知识图谱中未找到关于「{herb_name}」的信息。"

        # 根据问题类型生成不同回答
        question_type = self._classify_question(question)

        parts = [f"关于「{herb_name}」的信息："]

        # 基本信息
        if center.get("category"):
            parts.append(f"- 分类：{center.get('category')}")

        # 节点和关系信息
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        # 收集功效
        efficacies = []
        for edge in edges:
            rel_type = edge.get("type") or edge.get("rel_type", "")
            if "EFFICACY" in rel_type.upper() or "功效" in str(edge):
                target = edge.get("target") or {}
                if target.get("name"):
                    efficacies.append(target["name"])

        if efficacies:
            parts.append(f"- 主要功效：{', '.join(set(efficacies[:5]))}")

        # 收集性味归经
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

        # 来源
        if center.get("source"):
            parts.append(f"- 数据来源：{center.get('source')}")

        # 验证状态
        status = center.get("status", "pending")
        status_text = {"pending": "待验证", "verified": "已验证", "rejected": "已拒绝"}.get(status, status)
        parts.append(f"- 信息状态：{status_text}")

        return "\n".join(parts)

    async def _collect_sources(self, graph_data: dict) -> list[dict]:
        """收集回答中引用的来源"""
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
        """创建新的聊天会话"""
        return {
            "id": str(uuid4()),
            "user_id": user_id,
            "messages": [],
            "created_at": "now"
        }

    async def get_session(self, session_id: str) -> Optional[dict]:
        """获取聊天会话"""
        # TODO: 从数据库或缓存获取会话
        return None


# 全局单例
chat_service = ChatService
