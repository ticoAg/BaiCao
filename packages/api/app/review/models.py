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
    item_key: str
    node_type: str | None = None
    original_payload: dict[str, object] = Field(default_factory=dict)
    revised_payload: dict[str, object] = Field(default_factory=dict)
    decision: ReviewItemDecision = ReviewItemDecision.PENDING
    comment: str | None = None

    model_config = ConfigDict(use_enum_values=False)


class ReviewSession(BaseModel):
    id: str = Field(default_factory=lambda: f"review-{uuid4()}")
    run_id: str
    step: PipelineStepKey = PipelineStepKey.HUMAN_REVIEW
    status: ReviewSessionStatus = ReviewSessionStatus.DRAFT
    items: list[ReviewItem] = Field(default_factory=list)
    comment: str | None = None
    confirmed_at: datetime | None = None
    created_at: datetime = Field(default_factory=review_now)
    updated_at: datetime = Field(default_factory=review_now)

    model_config = ConfigDict(use_enum_values=False)
