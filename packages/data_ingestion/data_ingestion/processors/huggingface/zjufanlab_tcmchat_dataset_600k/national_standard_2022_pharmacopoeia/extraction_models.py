from pydantic import BaseModel, ConfigDict, Field


class PharmacopoeiaEntrySections(BaseModel):
    title_zh: str = Field(description="中文条目标题")
    header_lines: list[str] = Field(default_factory=list, description="标题区附加行")
    base_description: str | None = Field(default=None, description="基础描述文本")
    sections: dict[str, str] = Field(default_factory=dict, description="正文章节映射")
    piece_sections: dict[str, str] = Field(default_factory=dict, description="饮片章节映射")
    raw_text: str = Field(description="条目原文")

    model_config = ConfigDict(use_enum_values=False)


class PharmacopoeiaHerbExtraction(BaseModel):
    herb_name: str = Field(description="药材名称")
    pinyin_name: str | None = Field(default=None, description="拼音名")
    latin_name: str | None = Field(default=None, description="拉丁名或规范名")

    model_config = ConfigDict(use_enum_values=False)


class PharmacopoeiaPreparedPieceExtraction(BaseModel):
    piece_name: str = Field(description="饮片名称")
    parent_herb_name: str = Field(description="对应药材名称")
    processing_text: str | None = Field(default=None, description="炮制文本")
    flavors: list[str] = Field(default_factory=list, description="性味列表")
    nature: str | None = Field(default=None, description="药性")
    meridians: list[str] = Field(default_factory=list, description="归经列表")
    efficacies: list[str] = Field(default_factory=list, description="功效列表")

    model_config = ConfigDict(use_enum_values=False)


class PharmacopoeiaExtractionResult(BaseModel):
    herb: PharmacopoeiaHerbExtraction = Field(description="药材抽取结果")
    prepared_piece: PharmacopoeiaPreparedPieceExtraction | None = Field(default=None, description="饮片抽取结果")

    model_config = ConfigDict(use_enum_values=False)
