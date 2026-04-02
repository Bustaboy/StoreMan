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

    async def list_materials(self, limit: int = 100, offset: int = 0) -> tuple[list[Material], int]:
        clean_limit = max(limit, 1)
        clean_offset = max(offset, 0)

        items_stmt = (
            select(Material)
            .order_by(Material.material_number)
            .limit(clean_limit)
            .offset(clean_offset)
        )
        total_stmt = select(func.count()).select_from(Material)

        async with self.session_factory() as session:
            items = list((await session.scalars(items_stmt)).all())
            total = int((await session.scalar(total_stmt)) or 0)

        return items, total

    async def search_materials(self, query: str, limit: int = 25, offset: int = 0) -> list[Material]:
        clean_limit = max(limit, 1)
        clean_offset = max(offset, 0)

        try:
            return await self._search_with_meilisearch(query=query, limit=clean_limit, offset=clean_offset)
        except Exception:
            return await self._search_with_postgres(query=query, limit=clean_limit, offset=clean_offset)

    async def _search_with_meilisearch(self, query: str, limit: int, offset: int) -> list[Material]:
        search_result = self.meili_client.index('materials').search(
            query,
            {'limit': limit, 'offset': offset},
        )

        hits = search_result.get('hits', [])
        material_numbers = [
            str(hit.get('material_number') or hit.get('id'))
            for hit in hits
            if hit.get('material_number') or hit.get('id')
        ]
        if not material_numbers:
            return []

        order = {material_number: index for index, material_number in enumerate(material_numbers)}
        stmt = select(Material).where(Material.material_number.in_(material_numbers))
        async with self.session_factory() as session:
            materials = list((await session.scalars(stmt)).all())

        return sorted(materials, key=lambda material: order.get(material.material_number, len(order)))

    async def _search_with_postgres(self, query: str, limit: int, offset: int) -> list[Material]:
        vector = func.to_tsvector(
            'simple',
            func.concat_ws(' ', Material.material_number, Material.description, Material.category),
        )
        ts_query = func.plainto_tsquery('simple', query)

        stmt = (
            select(Material)
            .where(vector.op('@@')(ts_query))
            .order_by(func.ts_rank(vector, ts_query).desc(), Material.material_number.asc())
            .limit(limit)
            .offset(offset)
        )

        async with self.session_factory() as session:
            return list((await session.scalars(stmt)).all())


material_repository = MaterialRepository()
