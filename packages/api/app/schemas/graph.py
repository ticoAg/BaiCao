"""Graph Pydantic 模型（Neo4j 图谱）"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from graph_schema.constants import NodeStatus, NodeType

from ..models.enums import EdgeType
from .graph_workbench import GraphSceneInfo


GRAPH_QUERY_PROPERTY_KEYS = (
    "latin_name",
    "category",
    "description",
    "chemical_formula",
    "parent_herb",
    "min_duration",
    "conditions",
    "trait_category",
    "years",
    "quality_indicator",
    "nature",
    "tcm_type",
    "type",
)
GraphQueryPropertyKey = Literal[
    "latin_name",
    "category",
    "description",
    "chemical_formula",
    "parent_herb",
    "min_duration",
    "conditions",
    "trait_category",
    "years",
    "quality_indicator",
    "nature",
    "tcm_type",
    "type",
]


# ============ 节点 ============

class BaseNode(BaseModel):
    """基础节点"""
    id: str = Field(description="节点唯一标识")
    name: str = Field(description="节点展示名称")
    source: str | None = Field(default=None, description="数据来源")
    imported_at: datetime | None = Field(default=None, description="导入时间")
    status: NodeStatus = Field(default=NodeStatus.PENDING, description="节点审核状态")
    verification_id: str | None = Field(default=None, description="审核记录标识")
    verified_by: str | None = Field(default=None, description="审核人")
    verified_at: datetime | None = Field(default=None, description="审核完成时间")

    model_config = ConfigDict(strict=True)


class HerbNode(BaseNode):
    """药材节点"""
    type: NodeType = Field(default=NodeType.HERB, description="节点类型：药材")
    herb_type: str | None = Field(default=None, description="药材细分类型")
    category: str | None = Field(default=None, description="药材分类")


class ComponentNode(BaseNode):
    """成分节点"""
    type: NodeType = Field(default=NodeType.COMPONENT, description="节点类型：成分")
    chemical_formula: str | None = Field(default=None, description="化学式")


class VariantNode(BaseNode):
    """品种变种节点"""
    type: NodeType = Field(default=NodeType.VARIANT, description="节点类型：品种")
    parent_herb: str | None = Field(default=None, description="所属药材名称或标识")
    description: str | None = Field(default=None, description="品种说明")


class ProcessNode(BaseNode):
    """加工工艺节点"""
    type: NodeType = Field(default=NodeType.PROCESS, description="节点类型：工艺")
    description: str | None = Field(default=None, description="工艺说明")
    min_duration: str | None = Field(default=None, description="最小时长说明")
    conditions: str | None = Field(default=None, description="工艺条件说明")


class TraitNode(BaseNode):
    """性状特征节点"""
    type: NodeType = Field(default=NodeType.TRAIT, description="节点类型：性状")
    trait_category: str | None = Field(default=None, description="性状分类")
    description: str | None = Field(default=None, description="性状说明")
    observation_method: str | None = Field(default=None, description="观测方法")


class TimePointNode(BaseNode):
    """时间点节点"""
    type: NodeType = Field(default=NodeType.TIMEPOINT, description="节点类型：时间点")
    years: int | None = Field(default=None, description="对应年份数值")
    description: str | None = Field(default=None, description="时间点说明")
    quality_indicator: str | None = Field(default=None, description="质量指标说明")


class EfficacyNode(BaseNode):
    """功效节点"""
    type: NodeType = Field(default=NodeType.EFFICACY, description="节点类型：功效")
    category: str | None = Field(default=None, description="功效分类")


class FlavorNode(BaseNode):
    """性味节点"""
    type: NodeType = Field(default=NodeType.FLAVOR, description="节点类型：性味")
    nature: str | None = Field(default=None, description="性味属性")


class MeridianNode(BaseNode):
    """归经节点"""
    type: NodeType = Field(default=NodeType.MERIDIAN, description="节点类型：归经")


class DiseaseNode(BaseNode):
    """疾病节点"""
    type: NodeType = Field(default=NodeType.DISEASE, description="节点类型：病证")
    tcm_type: str | None = Field(default=None, description="中医病证分类")


class GraphNode(BaseModel):
    """图谱节点（discriminated union）"""
    id: str = Field(description="节点唯一标识")
    name: str = Field(description="节点展示名称")
    labels: list[str] = Field(description="节点标签列表")
    properties: dict = Field(description="节点属性映射")
    status: NodeStatus = Field(default=NodeStatus.PENDING, description="节点审核状态")

    model_config = ConfigDict(strict=True)


# ============ 边 ============

class BaseEdge(BaseModel):
    """基础边"""
    status: NodeStatus = Field(default=NodeStatus.PENDING, description="边审核状态")
    verification_id: str | None = Field(default=None, description="审核记录标识")
    verified_by: str | None = Field(default=None, description="审核人")
    verified_at: datetime | None = Field(default=None, description="审核完成时间")

    model_config = ConfigDict(strict=True)


class ContainsEdge(BaseEdge):
    """成分关系"""
    quantity: str | None = Field(default=None, description="包含数量或比例说明")


class HasVariantEdge(BaseEdge):
    """品种关系"""
    pass


class ProcessedByEdge(BaseEdge):
    """工艺关系"""
    duration: str | None = Field(default=None, description="处理时长说明")
    conditions: str | None = Field(default=None, description="处理条件说明")
    start_date: str | None = Field(default=None, description="开始时间")
    end_date: str | None = Field(default=None, description="结束时间")


class StoredForEdge(BaseEdge):
    """储存时间关系"""
    years: int | None = Field(default=None, description="储存年限")
    start_date: str | None = Field(default=None, description="开始时间")
    end_date: str | None = Field(default=None, description="结束时间")


class HasTraitEdge(BaseEdge):
    """性状关系"""
    value: str | None = Field(default=None, description="性状值")
    observation: str | None = Field(default=None, description="观测说明")
    year_range: str | None = Field(default=None, description="适用年份范围")


class GraphEdgeNodeRef(BaseModel):
    """图谱边上的节点引用"""
    id: str = Field(description="节点唯一标识")
    name: str = Field(description="节点展示名称")
    source: str | None = Field(default=None, description="数据来源")
    status: NodeStatus = Field(default=NodeStatus.PENDING, description="节点审核状态")
    labels: list[str] = Field(description="节点标签列表")

    model_config = ConfigDict(strict=False)


class GraphEdge(BaseModel):
    """图谱边"""
    id: str | None = Field(default=None, description="边唯一标识")
    rel_type: EdgeType = Field(description="关系类型")
    status: NodeStatus = Field(default=NodeStatus.PENDING, description="边审核状态")
    verification_id: str | None = Field(default=None, description="审核记录标识")
    verified_by: str | None = Field(default=None, description="审核人")
    verified_at: str | None = Field(default=None, description="审核完成时间")
    source: GraphEdgeNodeRef = Field(description="起始节点引用")
    target: GraphEdgeNodeRef = Field(description="目标节点引用")

    model_config = ConfigDict(strict=False)


# ============ 图谱响应 ============

class GraphData(BaseModel):
    """图谱数据响应"""
    center: dict | None = Field(default=None, description="中心节点")
    nodes: list[dict] = Field(description="节点列表")
    edges: list[GraphEdge] = Field(description="边列表")

    model_config = ConfigDict(strict=True)


class SearchResult(BaseModel):
    """搜索结果"""
    node: dict = Field(description="匹配节点")
    labels: list[str] = Field(description="匹配节点标签列表")

    model_config = ConfigDict(strict=True)


class GraphRecord(BaseModel):
    """导入导出用的图谱记录"""
    node_type: NodeType | None = Field(default=None, description="节点类型")
    node_name: str = Field(description="节点名称")
    properties: dict | None = Field(default=None, description="节点属性集合")
    edges: list[dict] | None = Field(default=None, description="关联边列表")
    source: str = Field(description="数据来源")
    status: NodeStatus = Field(default=NodeStatus.PENDING, description="节点审核状态")

    model_config = ConfigDict(strict=True)


class GraphQueryNodeFilters(BaseModel):
    """图谱高级查询的节点过滤条件"""
    name_contains: str | None = Field(default=None, description="节点名称包含条件")
    label: NodeType | None = Field(default=None, description="节点类型过滤条件")
    status: NodeStatus | None = Field(default=None, description="节点审核状态过滤条件")
    source_contains: str | None = Field(default=None, description="数据来源包含条件")
    property_key: GraphQueryPropertyKey | None = Field(default=None, description="属性键过滤条件")
    property_value_contains: str | None = Field(default=None, description="属性值包含条件")

    model_config = ConfigDict(strict=False)


class GraphQueryEdgeFilters(BaseModel):
    """图谱高级查询的边过滤条件"""
    rel_type: EdgeType | None = Field(default=None, description="关系类型过滤条件")
    status: NodeStatus | None = Field(default=None, description="边审核状态过滤条件")
    connected_name_contains: str | None = Field(default=None, description="关联节点名称包含条件")

    model_config = ConfigDict(strict=False)


class GraphQueryRequest(BaseModel):
    """图谱高级查询请求"""
    node: GraphQueryNodeFilters | None = Field(default=None, description="节点过滤条件")
    edge: GraphQueryEdgeFilters | None = Field(default=None, description="边过滤条件")
    depth: int = Field(default=1, ge=1, le=6, description="图查询展开深度")
    limit: int = Field(default=20, ge=1, le=100, description="返回结果上限")

    model_config = ConfigDict(strict=True)


class GraphQuerySummary(BaseModel):
    """图谱高级查询摘要"""
    mode: str = Field(description="查询模式")
    matched_nodes: int = Field(description="命中的节点数量")
    matched_edges: int = Field(description="命中的边数量")
    truncated: bool = Field(description="结果是否被截断")
    active_filters: list[str] = Field(description="生效的过滤条件列表")

    model_config = ConfigDict(strict=True)


class GraphQueryResponse(BaseModel):
    """图谱高级查询响应"""
    summary: GraphQuerySummary = Field(description="查询摘要")
    graph: GraphData = Field(description="图查询结果")
    scene: GraphSceneInfo = Field(description="图场景信息")

    model_config = ConfigDict(strict=True)
