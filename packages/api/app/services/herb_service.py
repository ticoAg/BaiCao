# typed-store integration note:
# typed-store provides SyncTypedStore/AsyncTypedStore facade over SQLAlchemy
# However, some features may not be fully supported yet:
# - See: https://github.com/ticoAg/typed-store/issues
# Once typed-store supports all required features, we will migrate data access to use it.

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import HerbModel


class HerbService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, herb_id: UUID) -> Optional[HerbModel]:
        result = await self.session.execute(
            select(HerbModel).where(HerbModel.id == herb_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[HerbModel]:
        result = await self.session.execute(
            select(HerbModel).where(HerbModel.name == name)
        )
        return result.scalar_one_or_none()

    async def list_herbs(
        self,
        category: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[list[HerbModel], int]:
        query = select(HerbModel)
        count_query = select(HerbModel)

        if category:
            query = query.where(HerbModel.category == category)
            count_query = count_query.where(HerbModel.category == category)

        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        count_result = await self.session.execute(count_query)

        return list(result.scalars().all()), len(count_result.scalars().all())
