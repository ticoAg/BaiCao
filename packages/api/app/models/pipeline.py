from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .herb import Base, utc_now


class PipelineRunModel(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_locator: Mapped[str] = mapped_column(String(500), nullable=False)
    source_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    current_step: Mapped[str] = mapped_column(String(100), nullable=False)
    steps: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class PipelineStepArtifactModel(Base):
    __tablename__ = "pipeline_step_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    step: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    preview_version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    preview_kind: Mapped[str] = mapped_column(String(100), nullable=False)
    preview_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    warnings: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    errors: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    artifacts: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    next_step_ready: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
