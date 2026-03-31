from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


WorkbenchCommandSource = Literal["workbench", "chat"]
WorkbenchFrameType = Literal["graph", "table", "text", "error"]
WorkbenchFrameStatus = Literal["ok", "warning", "error"]


class CypherValidationRequest(BaseModel):
    query: str = Field(..., min_length=1, description="待校验的 Cypher 语句")
    source: WorkbenchCommandSource = Field(default="workbench", description="命令来源")

    model_config = ConfigDict(strict=True)


class CypherValidationResult(BaseModel):
    valid: bool = Field(description="语句是否有效")
    normalized_query: str = Field(description="归一化后的 Cypher 语句")
    errors: list[str] = Field(default_factory=list, description="校验错误列表")
    warnings: list[str] = Field(default_factory=list, description="校验警告列表")
    readonly: bool = Field(default=True, description="是否为只读语句")

    model_config = ConfigDict(strict=True)


class WorkbenchHistoryItem(BaseModel):
    command: str = Field(description="执行命令")
    source: WorkbenchCommandSource = Field(description="命令来源")
    executed_at: str | None = Field(default=None, description="执行时间")

    model_config = ConfigDict(strict=True)


class WorkbenchFrame(BaseModel):
    id: str = Field(description="工作台帧标识")
    type: WorkbenchFrameType = Field(description="工作台帧类型")
    title: str = Field(description="工作台帧标题")
    status: WorkbenchFrameStatus = Field(description="工作台帧状态")
    payload: dict[str, Any] = Field(description="工作台帧载荷")
    command: str | None = Field(default=None, description="生成该帧的命令")

    model_config = ConfigDict(strict=False)


class WorkbenchExecuteRequest(BaseModel):
    command: str = Field(..., min_length=1, description="待执行命令")
    source: WorkbenchCommandSource = Field(default="workbench", description="命令来源")
    session_id: str | None = Field(default=None, description="会话标识")

    model_config = ConfigDict(strict=True)


class WorkbenchExecuteResponse(BaseModel):
    command: str = Field(description="执行命令")
    frames: list[WorkbenchFrame] = Field(description="执行返回的工作台帧列表")
    history_item: WorkbenchHistoryItem = Field(description="新增历史记录")

    model_config = ConfigDict(strict=False)
