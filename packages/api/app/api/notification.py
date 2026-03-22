from __future__ import annotations
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..core.database import get_db
from ..models.notification import NotificationModel

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ============ Response Models ============

class NotificationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: str
    type: str
    title: str
    content: Optional[dict] = None
    read: bool
    created_at: str

    @classmethod
    def from_model(cls, m: NotificationModel) -> "NotificationResponse":
        return cls(
            id=m.id,
            user_id=m.user_id,
            type=m.type,
            title=m.title,
            content=m.content,
            read=m.read,
            created_at=m.created_at.isoformat(),
        )


# ============ Endpoints ============

@router.get("/", summary="列出通知")
async def list_notifications(
    user_id: str = Query(default="anonymous"),
    unread_only: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(NotificationModel).where(NotificationModel.user_id == user_id)
    if unread_only:
        stmt = stmt.where(NotificationModel.read == False)  # noqa: E712
    stmt = stmt.order_by(NotificationModel.created_at.desc()).limit(limit)

    result = await db.execute(stmt)
    notifications = result.scalars().all()

    count_stmt = select(func.count()).select_from(NotificationModel).where(
        NotificationModel.user_id == user_id,
        NotificationModel.read == False,  # noqa: E712
    )
    unread_count = (await db.execute(count_stmt)).scalar_one()

    return {
        "items": [NotificationResponse.from_model(n) for n in notifications],
        "total": len(notifications),
        "unread_count": unread_count,
    }


@router.post("/{notification_id}/read", summary="标记通知为已读")
async def mark_notification_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NotificationModel).where(NotificationModel.id == notification_id)
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.read = True
    await db.commit()
    return {"id": str(notification_id), "read": True}
