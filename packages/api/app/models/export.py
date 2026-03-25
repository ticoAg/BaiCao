from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .herb import Base, utc_now


class ExportRecordModel(Base):
    __tablename__ = "export_records"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    review_session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    graph_write_status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    snapshot_bucket: Mapped[str | None] = mapped_column(String(200), nullable=True)
    snapshot_object_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    snapshot_checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    snapshot_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
