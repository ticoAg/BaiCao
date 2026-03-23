"""Graph Workbench 协议边界模型。"""

from pydantic import BaseModel, ConfigDict, Field


class GraphWorkbenchMetaSummary(BaseModel):
    node_count: int = Field(ge=0)
    relationship_count: int = Field(ge=0)
    label_count: int = Field(ge=0)
    relationship_type_count: int = Field(ge=0)
    property_key_count: int = Field(ge=0)
    index_count: int = Field(ge=0)
    constraint_count: int = Field(ge=0)
    truncated: bool = False
    generated_at: str = Field(min_length=1)

    model_config = ConfigDict(strict=True)


class GraphWorkbenchLabelMetaItem(BaseModel):
    name: str = Field(min_length=1)
    count: int = Field(ge=0)
    property_keys: list[str] = Field(default_factory=list)

    model_config = ConfigDict(strict=True)


class GraphWorkbenchRelationshipTypeMetaItem(BaseModel):
    name: str = Field(min_length=1)
    count: int = Field(ge=0)
    property_keys: list[str] = Field(default_factory=list)

    model_config = ConfigDict(strict=True)


class GraphWorkbenchPropertyKeyMetaItem(BaseModel):
    name: str = Field(min_length=1)
    used_by_labels: list[str] = Field(default_factory=list)
    used_by_relationship_types: list[str] = Field(default_factory=list)

    model_config = ConfigDict(strict=True)


class GraphWorkbenchSchemaIndexItem(BaseModel):
    name: str | None = None
    type: str | None = None
    entity_type: str | None = None
    labels_or_types: list[str] = Field(default_factory=list)
    properties: list[str] = Field(default_factory=list)
    state: str | None = None

    model_config = ConfigDict(strict=True)


class GraphWorkbenchSchemaConstraintItem(BaseModel):
    name: str | None = None
    type: str | None = None
    entity_type: str | None = None
    labels_or_types: list[str] = Field(default_factory=list)
    properties: list[str] = Field(default_factory=list)

    model_config = ConfigDict(strict=True)


class GraphWorkbenchSchemaResponse(BaseModel):
    indexes: list[GraphWorkbenchSchemaIndexItem] = Field(default_factory=list)
    constraints: list[GraphWorkbenchSchemaConstraintItem] = Field(default_factory=list)

    model_config = ConfigDict(strict=True)


class GraphWorkbenchLabelMetaListResponse(BaseModel):
    items: list[GraphWorkbenchLabelMetaItem] = Field(default_factory=list)
    total: int = Field(ge=0)

    model_config = ConfigDict(strict=True)


class GraphWorkbenchRelationshipTypeMetaListResponse(BaseModel):
    items: list[GraphWorkbenchRelationshipTypeMetaItem] = Field(default_factory=list)
    total: int = Field(ge=0)

    model_config = ConfigDict(strict=True)


class GraphWorkbenchPropertyKeyMetaListResponse(BaseModel):
    items: list[GraphWorkbenchPropertyKeyMetaItem] = Field(default_factory=list)
    total: int = Field(ge=0)

    model_config = ConfigDict(strict=True)


class GraphSceneInfo(BaseModel):
    truncated: bool = False
    node_limit_hit: bool = False
    relationship_limit_hit: bool = False
    info_message: str | None = None

    model_config = ConfigDict(strict=True)
