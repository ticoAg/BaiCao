from pydantic import BaseModel, ConfigDict, Field

from knowledge_model.constants import NodeType


class SourceDocument(BaseModel):
    source_name: str
    source_locator: str
    raw_text: str
    metadata: dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=False)


class ExtractionCandidate(BaseModel):
    node_type: NodeType
    node_name: str
    source_name: str
    properties: dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=False)
