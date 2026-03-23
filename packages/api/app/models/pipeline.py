from datetime import datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .herb import Base, utc_now


class PipelineRunModel(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_locator: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    current_step: Mapped[str] = mapped_column(String(100), nullable=False)
    steps: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
