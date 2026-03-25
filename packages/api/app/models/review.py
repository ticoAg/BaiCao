from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .herb import Base, utc_now


class ReviewSessionModel(Base):
    __tablename__ = "review_sessions"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    step: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class ReviewItemModel(Base):
    __tablename__ = "review_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("review_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    item_key: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    node_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    original_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    revised_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    decision: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
