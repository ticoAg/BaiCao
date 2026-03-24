from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Text, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .herb import Base, utc_now
from .enums import SourceType


class SourceModel(Base):
    __tablename__ = "sources"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    type: Mapped[SourceType] = mapped_column(Enum(SourceType, native_enum=True), nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    publication_date: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    isbn: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    pages: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    citation: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
