from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.models import InventoryItem, Location, Material

settings = get_settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


class MaterialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_materials(self, skip: int = 0, limit: int = 100) -> list[Material]:
        stmt = (
            select(
                Material,
                func.coalesce(func.sum(InventoryItem.quantity), 0).label('quantity'),
                Location.name.label('location'),
            )
            .outerjoin(InventoryItem, InventoryItem.material_id == Material.material_number)
            .outerjoin(Location, Location.id == Material.default_location_id)
            .group_by(Material.material_number, Location.name)
            .order_by(Material.material_number)
            .offset(max(skip, 0))
            .limit(max(limit, 1))
        )
        rows = (await self.session.execute(stmt)).all()

        materials: list[Material] = []
        for material, quantity, location in rows:
            setattr(material, 'quantity', int(quantity or 0))
            setattr(material, 'location', location)
            materials.append(material)

        return materials
