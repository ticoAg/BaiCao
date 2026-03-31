from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.review.models import ReviewItemDecision, ReviewSessionStatus


class ReviewItemResponse(BaseModel):
    item_key: str = Field(description="评审条目标识")
    node_type: str | None = Field(default=None, description="关联节点类型")
    original_payload: dict[str, Any] = Field(default_factory=dict, description="原始载荷")
    revised_payload: dict[str, Any] = Field(default_factory=dict, description="修订后载荷")
    decision: str = Field(description="评审决策")
    comment: str | None = Field(default=None, description="评审备注")

    model_config = ConfigDict(use_enum_values=False)


class ReviewSessionResponse(BaseModel):
    id: str = Field(description="评审会话标识")
    run_id: str = Field(description="所属流水线运行标识")
    step: str = Field(description="关联流水线步骤")
    status: str = Field(description="评审会话状态")
    items: list[ReviewItemResponse] = Field(default_factory=list, description="当前评审会话中的条目列表")
    comment: str | None = Field(default=None, description="评审会话备注")
    confirmed_at: str | None = Field(default=None, description="确认时间")

    model_config = ConfigDict(use_enum_values=False)


class UpdateReviewItemRequest(BaseModel):
    decision: ReviewItemDecision | None = Field(default=None, description="更新后的评审决策")
    revised_payload: dict[str, Any] | None = Field(default=None, description="更新后的修订载荷")
    comment: str | None = Field(default=None, description="评审备注")

    model_config = ConfigDict(use_enum_values=False)


class ConfirmReviewSessionRequest(BaseModel):
    comment: str | None = Field(default=None, description="评审会话备注")

    model_config = ConfigDict(use_enum_values=False)


class ReviewSummary(BaseModel):
    status: ReviewSessionStatus = Field(description="评审会话状态")
    total_items: int = Field(description="评审条目总数")
    pending_items: int = Field(description="待处理条目数量")
    confirmed_items: int = Field(description="确认条目数量")
    edited_items: int = Field(description="编辑条目数量")
    rejected_items: int = Field(description="拒绝条目数量")

    model_config = ConfigDict(use_enum_values=False)
