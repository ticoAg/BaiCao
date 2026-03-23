from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


WorkbenchCommandSource = Literal["workbench", "chat"]
WorkbenchFrameType = Literal["graph", "table", "text", "error"]
WorkbenchFrameStatus = Literal["ok", "warning", "error"]


class CypherValidationRequest(BaseModel):
    query: str = Field(..., min_length=1)
    source: WorkbenchCommandSource = "workbench"

    model_config = ConfigDict(strict=True)


class CypherValidationResult(BaseModel):
    valid: bool
    normalized_query: str
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    readonly: bool = True

    model_config = ConfigDict(strict=True)


class WorkbenchHistoryItem(BaseModel):
    command: str
    source: WorkbenchCommandSource
    executed_at: str | None = None

    model_config = ConfigDict(strict=True)


class WorkbenchFrame(BaseModel):
    id: str
    type: WorkbenchFrameType
    title: str
    status: WorkbenchFrameStatus
    payload: dict[str, Any]
    command: str | None = None

    model_config = ConfigDict(strict=False)


class WorkbenchExecuteRequest(BaseModel):
    command: str = Field(..., min_length=1)
    source: WorkbenchCommandSource = "workbench"
    session_id: str | None = None

    model_config = ConfigDict(strict=True)


class WorkbenchExecuteResponse(BaseModel):
    command: str
    frames: list[WorkbenchFrame]
    history_item: WorkbenchHistoryItem

    model_config = ConfigDict(strict=False)
