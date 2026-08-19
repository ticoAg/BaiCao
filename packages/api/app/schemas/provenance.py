"""溯源 API 的请求 / 响应模型。字段为前端友好英文键，不泄漏中文存储键。"""

from knowledge_model.constants import EdgeType, NodeStatus
from pydantic import BaseModel, ConfigDict, Field


class CreateEvidenceRequest(BaseModel):
    """创建证据节点"""

    content: str = Field(min_length=1, description="证据文本内容")
    source_name: str = Field(min_length=1, description="来源名称")
    page_reference: str | None = Field(default=None, description="页码/章节引用")

    model_config = ConfigDict(strict=False)


class LinkSourceRequest(BaseModel):
    """将证据关联到来源节点"""

    source_id: str = Field(min_length=1, description="来源节点 ID")

    model_config = ConfigDict(strict=False)


class ProvenanceNode(BaseModel):
    """溯源链上的实体或来源节点"""

    id: str = Field(description="节点唯一标识")
    name: str = Field(description="节点展示名称")
    status: NodeStatus = Field(default=NodeStatus.PENDING, description="节点审核状态")

    model_config = ConfigDict(strict=False)


class EvidenceResponse(BaseModel):
    """溯源证据节点"""

    id: str = Field(description="证据节点 ID")
    content: str = Field(description="证据文本内容")
    source_name: str = Field(description="来源名称")
    page_reference: str | None = Field(default=None, description="页码/章节引用")
    status: NodeStatus = Field(default=NodeStatus.PENDING, description="证据状态")

    model_config = ConfigDict(strict=False)


ProvenanceEvidence = EvidenceResponse


class ProvenanceRelationship(BaseModel):
    """证据与来源之间的关系"""

    type: EdgeType = Field(description="关系类型")
    status: NodeStatus = Field(default=NodeStatus.PENDING, description="关系审核状态")
    evidence_id: str | None = Field(default=None, description="证据节点 ID")
    source_id: str | None = Field(default=None, description="来源节点 ID")

    model_config = ConfigDict(strict=False)


class LinkSourceResponse(BaseModel):
    """证据关联来源的结果"""

    relationship: ProvenanceRelationship = Field(description="证据到来源的关系")
    message: str = Field(description="操作结果说明")

    model_config = ConfigDict(strict=False)


class LineageChainResponse(BaseModel):
    """完整溯源链"""

    entity: ProvenanceNode = Field(description="实体节点")
    evidence: EvidenceResponse | None = Field(default=None, description="证据节点")
    source: ProvenanceNode = Field(description="来源节点")

    model_config = ConfigDict(strict=False)


class LineageCompletenessResponse(BaseModel):
    """溯源链完整性"""

    entity: ProvenanceNode = Field(description="实体节点")
    evidence: EvidenceResponse | None = Field(default=None, description="证据节点")
    source: ProvenanceNode | None = Field(default=None, description="来源节点")
    has_evidence: bool = Field(description="是否存在证据")
    has_source: bool = Field(description="是否存在来源")
    chain_complete: bool = Field(description="溯源链是否完整")

    model_config = ConfigDict(strict=False)


class EvidenceCollectionItem(BaseModel):
    """实体关联的一条证据"""

    evidence: EvidenceResponse = Field(description="证据节点")
    source: ProvenanceNode | None = Field(default=None, description="来源节点")

    model_config = ConfigDict(strict=False)


class SourceDerivationsResponse(BaseModel):
    """来源派生出的溯源链列表"""

    derivations: list[LineageChainResponse] = Field(description="溯源链列表")
    count: int = Field(description="溯源链数量")

    model_config = ConfigDict(strict=False)


class EvidenceCollectionResponse(BaseModel):
    """实体证据列表"""

    evidence: list[EvidenceCollectionItem] = Field(description="证据列表")
    count: int = Field(description="证据数量")

    model_config = ConfigDict(strict=False)
