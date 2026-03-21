from datetime import UTC, datetime
from typing import Optional

from uuid import UUID, uuid4

from sqlalchemy import JSON, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(UTC)


class HerbModel(Base):
    __tablename__ = "herbs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    latin_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    english_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    alias: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    efficacy: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    flavor: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    meridian: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    dosage: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contraindications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
