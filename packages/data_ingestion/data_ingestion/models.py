"""定义数据采集边界层暴露给外部的最小业务模型。"""

from pydantic import BaseModel, ConfigDict, Field

from knowledge_model.constants import NodeType


class SourceDocument(BaseModel):
    """表示已经过来源适配后的最小文本单元。"""

    source_name: str = Field(description="来源名称")
    source_locator: str = Field(description="来源定位信息")
    raw_text: str = Field(description="原始文本内容")
    metadata: dict[str, object] = Field(default_factory=dict, description="来源补充元数据")

    model_config = ConfigDict(use_enum_values=False)


class ExtractionCandidate(BaseModel):
    """表示抽取阶段产生的图谱节点候选。"""

    node_type: NodeType = Field(description="候选节点类型")
    node_name: str = Field(description="候选节点名称")
    source_name: str = Field(description="候选来源名称")
    properties: dict[str, object] = Field(default_factory=dict, description="候选节点属性集合")

    model_config = ConfigDict(use_enum_values=False)
