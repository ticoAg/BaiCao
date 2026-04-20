from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GraphToolCall(BaseModel):
    tool_name: str = Field(description="调用的工具名")
    arguments: dict[str, Any] = Field(default_factory=dict, description="工具调用参数")
    summary: str = Field(description="工具调用摘要")
    result_summary: str | None = Field(default=None, description="工具执行结果摘要")
    status: str = Field(default="completed", description="工具执行状态")

    model_config = ConfigDict(use_enum_values=False)
