from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..services.herb_service import HerbService

router = APIRouter(prefix="/herbs", tags=["herbs"])


@router.get("/{herb_id}")
async def get_herb(
    herb_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    service = HerbService(db)
    herb = await service.get_by_id(herb_id)
    if not herb:
        raise HTTPException(status_code=404, detail="Herb not found")
    return herb


@router.get("/")
async def list_herbs(
    category: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    service = HerbService(db)
    herbs, total = await service.list_herbs(category=category, limit=limit, offset=offset)
    return {
        "items": herbs,
        "total": total,
        "page": offset // limit + 1,
        "page_size": limit,
        "has_more": offset + len(herbs) < total
    }


@router.get("/search/{name}")
async def search_herb_by_name(
    name: str,
    db: AsyncSession = Depends(get_db)
):
    service = HerbService(db)
    herb = await service.get_by_name(name)
    if not herb:
        raise HTTPException(status_code=404, detail="Herb not found")
    return herb
