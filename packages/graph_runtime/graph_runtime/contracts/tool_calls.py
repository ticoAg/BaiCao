from pydantic import BaseModel, ConfigDict, Field


class GraphToolCall(BaseModel):
    tool_name: str = Field(description="调用的工具名")
    summary: str = Field(description="工具调用摘要")

    model_config = ConfigDict(use_enum_values=False)
