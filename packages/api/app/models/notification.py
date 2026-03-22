from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .herb import Base, utc_now


class NotificationModel(Base):
    """站内通知 - 审查结果等系统通知"""

    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # verification_completed / system
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # {message, link, verdict}
    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
