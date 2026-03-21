"""Graph Pydantic 模型（Neo4j 图谱）"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..models.enums import EdgeType, NodeStatus, NodeType


# ============ 节点 ============

class BaseNode(BaseModel):
    """基础节点"""
    id: str
    name: str
    source: str | None = None
    imported_at: datetime | None = None
    status: NodeStatus = NodeStatus.PENDING
    verification_id: str | None = None
    verified_by: str | None = None
    verified_at: datetime | None = None

    model_config = ConfigDict(strict=True)


class HerbNode(BaseNode):
    """药材节点"""
    type: NodeType = NodeType.HERB
    herb_type: str | None = None
    category: str | None = None


class ComponentNode(BaseNode):
    """成分节点"""
    type: NodeType = NodeType.COMPONENT
    chemical_formula: str | None = None


class VariantNode(BaseNode):
    """品种变种节点"""
    type: NodeType = NodeType.VARIANT
    parent_herb: str | None = None
    description: str | None = None


class ProcessNode(BaseNode):
    """加工工艺节点"""
    type: NodeType = NodeType.PROCESS
    description: str | None = None
    min_duration: str | None = None
    conditions: str | None = None


class TraitNode(BaseNode):
    """性状特征节点"""
    type: NodeType = NodeType.TRAIT
    trait_category: str | None = None
    description: str | None = None
    observation_method: str | None = None


class TimePointNode(BaseNode):
    """时间点节点"""
    type: NodeType = NodeType.TIMEPOINT
    years: int | None = None
    description: str | None = None
    quality_indicator: str | None = None


class EfficacyNode(BaseNode):
    """功效节点"""
    type: NodeType = NodeType.EFFICACY
    category: str | None = None


class FlavorNode(BaseNode):
    """性味节点"""
    type: NodeType = NodeType.FLAVOR
    nature: str | None = None


class MeridianNode(BaseNode):
    """归经节点"""
    type: NodeType = NodeType.MERIDIAN


class DiseaseNode(BaseNode):
    """疾病节点"""
    type: NodeType = NodeType.DISEASE
    tcm_type: str | None = None


class GraphNode(BaseModel):
    """图谱节点（discriminated union）"""
    id: str
    name: str
    labels: list[str]
    properties: dict
    status: NodeStatus = NodeStatus.PENDING

    model_config = ConfigDict(strict=True)


# ============ 边 ============

class BaseEdge(BaseModel):
    """基础边"""
    status: NodeStatus = NodeStatus.PENDING
    verification_id: str | None = None
    verified_by: str | None = None
    verified_at: datetime | None = None

    model_config = ConfigDict(strict=True)


class ContainsEdge(BaseEdge):
    """成分关系"""
    quantity: str | None = None


class HasVariantEdge(BaseEdge):
    """品种关系"""
    pass


class ProcessedByEdge(BaseEdge):
    """工艺关系"""
    duration: str | None = None
    conditions: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class StoredForEdge(BaseEdge):
    """储存时间关系"""
    years: int | None = None
    start_date: str | None = None
    end_date: str | None = None


class HasTraitEdge(BaseEdge):
    """性状关系"""
    value: str | None = None
    observation: str | None = None
    year_range: str | None = None


class GraphEdge(BaseModel):
    """图谱边"""
    type: EdgeType
    source: str
    target: str
    properties: dict

    model_config = ConfigDict(strict=True)


# ============ 图谱响应 ============

class GraphData(BaseModel):
    """图谱数据响应"""
    center: dict | None = None
    nodes: list[dict]
    edges: list[GraphEdge]

    model_config = ConfigDict(strict=True)


class SearchResult(BaseModel):
    """搜索结果"""
    node: dict
    labels: list[str]

    model_config = ConfigDict(strict=True)


class GraphRecord(BaseModel):
    """导入导出用的图谱记录"""
    node_type: NodeType | None = None
    node_name: str
    properties: dict | None = None
    edges: list[dict] | None = None
    source: str
    status: NodeStatus = NodeStatus.PENDING

    model_config = ConfigDict(strict=True)


class GraphQueryNodeFilters(BaseModel):
    """图谱高级查询的节点过滤条件"""
    name_contains: str | None = None
    label: str | None = None
    status: str | None = None
    source_contains: str | None = None
    property_key: str | None = None
    property_value_contains: str | None = None

    model_config = ConfigDict(strict=True)


class GraphQueryEdgeFilters(BaseModel):
    """图谱高级查询的边过滤条件"""
    rel_type: str | None = None
    status: str | None = None
    connected_name_contains: str | None = None

    model_config = ConfigDict(strict=True)


class GraphQueryRequest(BaseModel):
    """图谱高级查询请求"""
    node: GraphQueryNodeFilters | None = None
    edge: GraphQueryEdgeFilters | None = None
    depth: int = Field(1, ge=1, le=6)
    limit: int = Field(20, ge=1, le=100)

    model_config = ConfigDict(strict=True)


class GraphQuerySummary(BaseModel):
    """图谱高级查询摘要"""
    mode: str
    matched_nodes: int
    matched_edges: int
    truncated: bool
    active_filters: list[str]

    model_config = ConfigDict(strict=True)


class GraphQueryResponse(BaseModel):
    """图谱高级查询响应"""
    summary: GraphQuerySummary
    graph: GraphData

    model_config = ConfigDict(strict=True)
