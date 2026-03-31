from pydantic import BaseModel, ConfigDict, Field


class SourceFileContext(BaseModel):
    provider: str = Field(description="来源提供方")
    dataset: str = Field(description="来源数据集")
    file_path: str = Field(description="来源文件路径")
    local_abspath: str = Field(description="本地文件绝对路径")
    file_size: int = Field(description="文件大小")
    line_count: int = Field(description="文件总行数")

    model_config = ConfigDict(use_enum_values=False)


class RawEntryBlock(BaseModel):
    entry_id: str = Field(description="条目标识")
    entry_title: str = Field(description="条目标题")
    raw_text: str = Field(description="条目原文")
    start_line: int = Field(description="起始行号")
    end_line: int = Field(description="结束行号")
    context: SourceFileContext = Field(description="来源上下文")

    model_config = ConfigDict(use_enum_values=False)
