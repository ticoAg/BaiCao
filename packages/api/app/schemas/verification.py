"""Verification Pydantic 模型"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..models.enums import EntityType, VerificationStatus


class VerificationCreate(BaseModel):
    """创建验证申请"""
    entity_type: EntityType = Field(description="待验证实体类型")
    entity_id: str = Field(description="待验证实体标识")
    field_name: str | None = Field(default=None, description="待验证字段名")
    claimed_value: str = Field(description="待验证字段值")
    source_id: UUID | None = Field(default=None, description="关联来源标识")

    model_config = ConfigDict(strict=True)


class VerificationEvidenceCreate(BaseModel):
    """创建验证证据"""
    source_id: UUID = Field(description="来源标识")
    quote: str = Field(description="证据引文")
    page_reference: str | None = Field(default=None, description="页码或章节引用")
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0, description="证据相关度")

    model_config = ConfigDict(strict=True)


class VerificationRead(BaseModel):
    """读取验证记录"""
    id: UUID = Field(description="验证记录标识")
    entity_type: EntityType = Field(description="待验证实体类型")
    entity_id: str = Field(description="待验证实体标识")
    field_name: str | None = Field(default=None, description="待验证字段名")
    claimed_value: str = Field(description="待验证字段值")
    source_id: UUID | None = Field(default=None, description="关联来源标识")
    status: VerificationStatus = Field(description="验证状态")
    applicant_id: UUID = Field(description="申请人标识")
    verifier_id: UUID | None = Field(default=None, description="审核人标识")
    verdict: str | None = Field(default=None, description="裁决说明")
    verified_at: datetime | None = Field(default=None, description="验证完成时间")
    created_at: datetime = Field(description="创建时间")

    model_config = ConfigDict(strict=True)


class VerificationVerdict(BaseModel):
    """专家裁决"""
    verification_id: UUID = Field(description="验证记录标识")
    status: VerificationStatus = Field(description="裁决后的验证状态")
    verdict: str = Field(description="裁决说明")

    model_config = ConfigDict(strict=True)
