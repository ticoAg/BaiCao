from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.review.models import ReviewItemDecision, ReviewSessionStatus


class ReviewItemResponse(BaseModel):
    item_key: str
    node_type: str | None = None
    original_payload: dict[str, Any] = Field(default_factory=dict)
    revised_payload: dict[str, Any] = Field(default_factory=dict)
    decision: str
    comment: str | None = None

    model_config = ConfigDict(use_enum_values=False)


class ReviewSessionResponse(BaseModel):
    id: str
    run_id: str
    step: str
    status: str
    items: list[ReviewItemResponse] = Field(default_factory=list)
    comment: str | None = None
    confirmed_at: str | None = None

    model_config = ConfigDict(use_enum_values=False)


class UpdateReviewItemRequest(BaseModel):
    decision: ReviewItemDecision | None = None
    revised_payload: dict[str, Any] | None = None
    comment: str | None = None

    model_config = ConfigDict(use_enum_values=False)


class ConfirmReviewSessionRequest(BaseModel):
    comment: str | None = None

    model_config = ConfigDict(use_enum_values=False)


class ReviewSummary(BaseModel):
    status: ReviewSessionStatus
    total_items: int
    pending_items: int
    confirmed_items: int
    edited_items: int
    rejected_items: int

    model_config = ConfigDict(use_enum_values=False)
