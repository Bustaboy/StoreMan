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

    async def get_materials(self, skip: int = 0, limit: int = 100) -> list[Material]:
        clean_skip = max(skip, 0)
        clean_limit = max(limit, 1)
        stmt = (
            select(Material)
            .order_by(Material.material_number)
            .offset(clean_skip)
            .limit(clean_limit)
        )
        async with self.session_factory() as session:
            return list((await session.scalars(stmt)).all())

    async def search_materials(self, query: str, limit: int = 50) -> list[Material]:
        clean_limit = max(limit, 1)
        search_result = self.meili_client.index('materials').search(
            query,
            {'limit': clean_limit},
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

    async def search_materials_db(self, query: str, limit: int = 50) -> list[Material]:
        clean_limit = max(limit, 1)
        vector = func.to_tsvector(
            'simple',
            func.concat_ws(' ', Material.material_number, Material.description, Material.category),
        )
        ts_query = func.plainto_tsquery('simple', query)

        stmt = (
            select(Material)
            .where(vector.op('@@')(ts_query))
            .order_by(func.ts_rank(vector, ts_query).desc(), Material.material_number.asc())
            .limit(clean_limit)
        )

        async with self.session_factory() as session:
            return list((await session.scalars(stmt)).all())

    async def sync_to_meilisearch(self) -> int:
        async with self.session_factory() as session:
            materials = list((await session.scalars(select(Material))).all())

        documents = []
        for material in materials:
            documents.append(
                {
                    'id': material.material_number,
                    'material_number': material.material_number,
                    'description': material.description,
                    'category': material.category,
                    'sap_material_number': material.sap_material_number,
                }
            )

        self.meili_client.index('materials').add_documents(documents, primary_key='id')
        return len(documents)


material_repository = MaterialRepository()
