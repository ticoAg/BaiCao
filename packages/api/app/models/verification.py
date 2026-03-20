from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .herb import Base, utc_now
from .enums import VerificationStatus, EntityType


class VerificationModel(Base):
    """验证记录 - 记录知识点的验证状态"""

    __tablename__ = "verifications"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_type: Mapped[EntityType] = mapped_column(Enum(EntityType, native_enum=True), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(200), nullable=False)
    field_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    claimed_value: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("sources.id"), nullable=True)
    status: Mapped[VerificationStatus] = mapped_column(Enum(VerificationStatus, native_enum=True), default=VerificationStatus.PENDING)
    applicant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    verifier_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verdict: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    applicant = relationship("UserModel", foreign_keys=[applicant_id])
    verifier = relationship("UserModel", foreign_keys=[verifier_id])
    source = relationship("SourceModel")
    evidence_list: Mapped[list["VerificationEvidenceModel"]] = relationship(back_populates="verification")


class VerificationEvidenceModel(Base):
    """验证证据 - 支持验证的具体证据"""

    __tablename__ = "verification_evidences"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    verification_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("verifications.id"), nullable=False)
    source_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    page_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    relevance_score: Mapped[float] = mapped_column(default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    verification = relationship("VerificationModel", back_populates="evidence_list")
    source = relationship("SourceModel")
