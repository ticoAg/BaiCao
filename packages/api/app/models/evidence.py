from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Float, ForeignKey, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .herb import Base, utc_now


class EvidenceModel(Base):
    __tablename__ = "evidences"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    herb_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("herbs.id"), nullable=False, index=True
    )
    source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("sources.id"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    quote: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chapter: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    page_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    extraction_method: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
