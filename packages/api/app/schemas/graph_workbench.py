"""Graph Workbench 协议边界模型。"""

from pydantic import BaseModel, ConfigDict, Field


class GraphWorkbenchMetaSummary(BaseModel):
    node_count: int = Field(ge=0, description="图数据库节点总数")
    relationship_count: int = Field(ge=0, description="图数据库关系总数")
    label_count: int = Field(ge=0, description="节点标签种类数")
    relationship_type_count: int = Field(ge=0, description="关系类型种类数")
    property_key_count: int = Field(ge=0, description="属性键种类数")
    index_count: int = Field(ge=0, description="索引数量")
    constraint_count: int = Field(ge=0, description="约束数量")
    truncated: bool = Field(default=False, description="统计结果是否被截断")
    generated_at: str = Field(min_length=1, description="统计生成时间")

    model_config = ConfigDict(strict=True)


class GraphWorkbenchLabelMetaItem(BaseModel):
    name: str = Field(min_length=1, description="标签名称")
    count: int = Field(ge=0, description="标签对应节点数量")
    property_keys: list[str] = Field(default_factory=list, description="该标签使用的属性键列表")

    model_config = ConfigDict(strict=True)


class GraphWorkbenchRelationshipTypeMetaItem(BaseModel):
    name: str = Field(min_length=1, description="关系类型名称")
    count: int = Field(ge=0, description="该类型关系数量")
    property_keys: list[str] = Field(default_factory=list, description="该关系类型使用的属性键列表")

    model_config = ConfigDict(strict=True)


class GraphWorkbenchPropertyKeyMetaItem(BaseModel):
    name: str = Field(min_length=1, description="属性键名称")
    used_by_labels: list[str] = Field(default_factory=list, description="使用该属性键的节点标签列表")
    used_by_relationship_types: list[str] = Field(default_factory=list, description="使用该属性键的关系类型列表")

    model_config = ConfigDict(strict=True)


class GraphWorkbenchSchemaIndexItem(BaseModel):
    name: str | None = Field(default=None, description="索引名称")
    type: str | None = Field(default=None, description="索引类型")
    entity_type: str | None = Field(default=None, description="索引作用对象类型")
    labels_or_types: list[str] = Field(default_factory=list, description="索引关联的标签或关系类型列表")
    properties: list[str] = Field(default_factory=list, description="索引覆盖的属性列表")
    state: str | None = Field(default=None, description="索引状态")

    model_config = ConfigDict(strict=True)


class GraphWorkbenchSchemaConstraintItem(BaseModel):
    name: str | None = Field(default=None, description="约束名称")
    type: str | None = Field(default=None, description="约束类型")
    entity_type: str | None = Field(default=None, description="约束作用对象类型")
    labels_or_types: list[str] = Field(default_factory=list, description="约束关联的标签或关系类型列表")
    properties: list[str] = Field(default_factory=list, description="约束覆盖的属性列表")

    model_config = ConfigDict(strict=True)


class GraphWorkbenchSchemaResponse(BaseModel):
    indexes: list[GraphWorkbenchSchemaIndexItem] = Field(default_factory=list, description="索引列表")
    constraints: list[GraphWorkbenchSchemaConstraintItem] = Field(default_factory=list, description="约束列表")

    model_config = ConfigDict(strict=True)


class GraphWorkbenchLabelMetaListResponse(BaseModel):
    items: list[GraphWorkbenchLabelMetaItem] = Field(default_factory=list, description="标签元数据列表")
    total: int = Field(ge=0, description="标签总数")

    model_config = ConfigDict(strict=True)


class GraphWorkbenchRelationshipTypeMetaListResponse(BaseModel):
    items: list[GraphWorkbenchRelationshipTypeMetaItem] = Field(default_factory=list, description="关系类型元数据列表")
    total: int = Field(ge=0, description="关系类型总数")

    model_config = ConfigDict(strict=True)


class GraphWorkbenchPropertyKeyMetaListResponse(BaseModel):
    items: list[GraphWorkbenchPropertyKeyMetaItem] = Field(default_factory=list, description="属性键元数据列表")
    total: int = Field(ge=0, description="属性键总数")

    model_config = ConfigDict(strict=True)


class GraphSceneInfo(BaseModel):
    truncated: bool = Field(default=False, description="图场景结果是否被截断")
    node_limit_hit: bool = Field(default=False, description="是否命中节点数量限制")
    relationship_limit_hit: bool = Field(default=False, description="是否命中关系数量限制")
    info_message: str | None = Field(default=None, description="补充说明信息")

    model_config = ConfigDict(strict=True)
