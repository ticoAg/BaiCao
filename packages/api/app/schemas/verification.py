"""Verification Pydantic 模型"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..models.enums import EntityType, VerificationStatus


class VerificationCreate(BaseModel):
    """创建验证申请"""
    entity_type: EntityType
    entity_id: str
    field_name: str | None = None
    claimed_value: str
    source_id: UUID | None = None

    model_config = ConfigDict(strict=True)


class VerificationEvidenceCreate(BaseModel):
    """创建验证证据"""
    source_id: UUID
    quote: str
    page_reference: str | None = None
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0)

    model_config = ConfigDict(strict=True)


class VerificationRead(BaseModel):
    """读取验证记录"""
    id: UUID
    entity_type: EntityType
    entity_id: str
    field_name: str | None = None
    claimed_value: str
    source_id: UUID | None = None
    status: VerificationStatus
    applicant_id: UUID
    verifier_id: UUID | None = None
    verdict: str | None = None
    verified_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(strict=True)


class VerificationVerdict(BaseModel):
    """专家裁决"""
    verification_id: UUID
    status: VerificationStatus
    verdict: str

    model_config = ConfigDict(strict=True)
