from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.pipeline.models import PipelineStepKey


def review_now() -> datetime:
    return datetime.now(UTC)


class ReviewSessionStatus(StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class ReviewItemDecision(StrEnum):
    PENDING = "pending"
    CONFIRM = "confirm"
    REJECT = "reject"
    EDIT = "edit"


class ReviewItem(BaseModel):
    item_key: str = Field(description="评审条目标识")
    node_type: str | None = Field(default=None, description="关联节点类型")
    original_payload: dict[str, object] = Field(default_factory=dict, description="原始载荷")
    revised_payload: dict[str, object] = Field(default_factory=dict, description="修订后载荷")
    decision: ReviewItemDecision = Field(default=ReviewItemDecision.PENDING, description="评审决策")
    comment: str | None = Field(default=None, description="评审备注")

    model_config = ConfigDict(use_enum_values=False)


class ReviewSession(BaseModel):
    id: str = Field(default_factory=lambda: f"review-{uuid4()}", description="评审会话标识")
    run_id: str = Field(description="所属流水线运行标识")
    step: PipelineStepKey = Field(default=PipelineStepKey.HUMAN_REVIEW, description="关联流水线步骤")
    status: ReviewSessionStatus = Field(default=ReviewSessionStatus.DRAFT, description="评审会话状态")
    items: list[ReviewItem] = Field(default_factory=list, description="评审条目列表")
    comment: str | None = Field(default=None, description="评审会话备注")
    confirmed_at: datetime | None = Field(default=None, description="确认时间")
    created_at: datetime = Field(default_factory=review_now, description="创建时间")
    updated_at: datetime = Field(default_factory=review_now, description="更新时间")

    model_config = ConfigDict(use_enum_values=False)
