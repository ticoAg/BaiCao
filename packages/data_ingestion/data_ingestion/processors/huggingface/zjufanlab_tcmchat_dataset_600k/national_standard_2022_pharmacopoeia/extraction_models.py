"""定义药典条目解析结果与抽取结果的结构化模型。"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PharmacopoeiaEntrySections(BaseModel):
    """表示单个药典条目在规则解析后的章节化结果。"""

    title_zh: str = Field(description="中文条目标题")
    header_lines: list[str] = Field(default_factory=list, description="标题区附加行")
    base_description: str | None = Field(default=None, description="基础描述文本")
    sections: dict[str, str] = Field(default_factory=dict, description="正文章节映射")
    piece_sections: dict[str, str] = Field(default_factory=dict, description="饮片章节映射")
    raw_text: str = Field(description="条目原文")

    model_config = ConfigDict(use_enum_values=False)


class PharmacopoeiaHerbExtraction(BaseModel):
    """描述药材主体层面的结构化抽取结果。"""

    herb_name: str = Field(description="药材名称")
    pinyin_name: str | None = Field(default=None, description="拼音名")
    latin_name: str | None = Field(default=None, description="拉丁名或规范名")
    base_description: str | None = Field(default=None, description="基础描述文本")
    indications: list[str] = Field(default_factory=list, description="病证或适应症列表")
    usage_text: str | None = Field(default=None, description="用法与用量")
    storage_text: str | None = Field(default=None, description="贮藏")
    caution_text: str | None = Field(default=None, description="注意事项")

    model_config = ConfigDict(use_enum_values=False)


class PharmacopoeiaPreparedPieceExtraction(BaseModel):
    """描述饮片层面的结构化抽取结果。"""

    piece_name: str = Field(description="饮片名称")
    parent_herb_name: str = Field(description="对应药材名称")
    processing_text: str | None = Field(default=None, description="炮制文本")
    flavors: list[str] = Field(default_factory=list, description="性味列表")
    nature: str | None = Field(default=None, description="药性")
    meridians: list[str] = Field(default_factory=list, description="归经列表")
    efficacies: list[str] = Field(default_factory=list, description="功效列表")
    indications: list[str] = Field(default_factory=list, description="病证或适应症列表")
    usage_text: str | None = Field(default=None, description="用法与用量")
    storage_text: str | None = Field(default=None, description="贮藏")
    caution_text: str | None = Field(default=None, description="注意事项")

    model_config = ConfigDict(use_enum_values=False)

    @model_validator(mode="before")
    @classmethod
    def fill_missing_piece_name(cls, data: Any) -> Any:
        """兼容 LLM 漏填饮片名或把列表字段返回为 null 的情况。"""

        if not isinstance(data, dict):
            return data
        data = dict(data)
        if data.get("piece_name") is None and data.get("parent_herb_name"):
            data["piece_name"] = data["parent_herb_name"]
        for field_name in ("flavors", "meridians", "efficacies", "indications"):
            if data.get(field_name) is None:
                data[field_name] = []
        return data


class PharmacopoeiaExtractionResult(BaseModel):
    """聚合药材、饮片和抽取告警的最终结果对象。"""

    herb: PharmacopoeiaHerbExtraction = Field(description="药材抽取结果")
    prepared_piece: PharmacopoeiaPreparedPieceExtraction | None = Field(default=None, description="饮片抽取结果")
    warnings: list[str] = Field(default_factory=list, description="抽取警告")
    confidence_notes: str | None = Field(default=None, description="抽取置信说明")

    model_config = ConfigDict(use_enum_values=False)

    @model_validator(mode="before")
    @classmethod
    def normalize_prepared_piece(cls, data: Any) -> Any:
        """兼容 LLM 偶发把单个饮片对象返回成列表的情况。"""

        if not isinstance(data, dict):
            return data
        prepared_piece = data.get("prepared_piece")
        if isinstance(prepared_piece, list):
            data = dict(data)
            data["prepared_piece"] = prepared_piece[0] if prepared_piece else None
        return data
