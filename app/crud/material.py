from __future__ import annotations

import meilisearch
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.models import Material


class MaterialRepository:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.engine = create_async_engine(self.settings.database_url, pool_pre_ping=True)
        self.session_factory = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self.meili_client = meilisearch.Client(
            self.settings.meilisearch_url,
            self.settings.meilisearch_master_key,
        )

    async def list_materials(self, limit: int = 100, offset: int = 0) -> list[Material]:
        stmt = (
            select(Material)
            .order_by(Material.material_number)
            .limit(max(limit, 1))
            .offset(max(offset, 0))
        )
        async with self.session_factory() as session:
            result = await session.scalars(stmt)
            return list(result.all())

    async def search_materials(self, query: str, limit: int = 25) -> list[Material]:
        try:
            materials = await self._search_with_meilisearch(query=query, limit=limit)
            if materials:
                return materials
        except Exception:
            pass

        return await self._search_with_postgres(query=query, limit=limit)

    async def _search_with_meilisearch(self, query: str, limit: int) -> list[Material]:
        search_result = self.meili_client.index('materials').search(
            query,
            {'limit': max(limit, 1)},
        )
        hits = search_result.get('hits', [])
        material_numbers: list[str] = []
        for hit in hits:
            material_number = hit.get('material_number') or hit.get('id')
            if material_number:
                material_numbers.append(str(material_number))

        if not material_numbers:
            return []

        order = {material_number: i for i, material_number in enumerate(material_numbers)}
        stmt = select(Material).where(Material.material_number.in_(material_numbers))
        async with self.session_factory() as session:
            result = await session.scalars(stmt)
            materials = list(result.all())

        return sorted(materials, key=lambda material: order.get(material.material_number, len(order)))

    async def _search_with_postgres(self, query: str, limit: int) -> list[Material]:
        vector = func.to_tsvector(
            'simple',
            func.concat_ws(' ', Material.material_number, Material.description, Material.category),
        )
        ts_query = func.plainto_tsquery('simple', query)

        stmt = (
            select(Material)
            .where(vector.op('@@')(ts_query))
            .order_by(func.ts_rank(vector, ts_query).desc(), Material.material_number.asc())
            .limit(max(limit, 1))
        )

        async with self.session_factory() as session:
            result = await session.scalars(stmt)
            return list(result.all())


material_repository = MaterialRepository()
