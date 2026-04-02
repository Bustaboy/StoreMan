from __future__ import annotations

import meilisearch
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.models import InventoryItem, Location, Material


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
        search_result = self.meili_client.index('materials').search(query, {'limit': clean_limit})
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
        quantity_subquery = (
            select(
                InventoryItem.material_id.label('material_number'),
                func.coalesce(func.sum(InventoryItem.quantity), 0).label('quantity'),
            )
            .group_by(InventoryItem.material_id)
            .subquery()
        )

        stmt = (
            select(
                Material.material_number,
                Material.description,
                Material.category,
                Material.sap_material_number,
                func.coalesce(quantity_subquery.c.quantity, 0).label('quantity'),
                Location.name.label('location'),
            )
            .outerjoin(quantity_subquery, quantity_subquery.c.material_number == Material.material_number)
            .outerjoin(Location, Location.id == Material.default_location_id)
        )

        async with self.session_factory() as session:
            rows = (await session.execute(stmt)).all()

        documents = [
            {
                'id': row.material_number,
                'material_number': row.material_number,
                'description': row.description,
                'category': row.category,
                'quantity': int(row.quantity or 0),
                'location': row.location,
                'sap_material_number': row.sap_material_number,
            }
            for row in rows
        ]
        materials_index = self.meili_client.index('materials')
        settings_task = materials_index.update_searchable_attributes(
            ['material_number', 'description', 'category', 'sap_material_number', 'location']
        )
        self.meili_client.wait_for_task(settings_task.task_uid)
        task = materials_index.add_documents(documents, primary_key='id')
        self.meili_client.wait_for_task(task.task_uid)
        return len(documents)

    async def get_material_summaries(self, materials: list[Material]) -> list[dict[str, object]]:
        if not materials:
            return []

        material_numbers = [material.material_number for material in materials]
        quantity_subquery = (
            select(
                InventoryItem.material_id.label('material_number'),
                func.coalesce(func.sum(InventoryItem.quantity), 0).label('quantity'),
            )
            .where(InventoryItem.material_id.in_(material_numbers))
            .group_by(InventoryItem.material_id)
            .subquery()
        )

        stmt = (
            select(
                Material.material_number,
                Material.description,
                Material.category,
                Material.sap_material_number,
                func.coalesce(quantity_subquery.c.quantity, 0).label('quantity'),
                Location.name.label('location'),
            )
            .outerjoin(quantity_subquery, quantity_subquery.c.material_number == Material.material_number)
            .outerjoin(Location, Location.id == Material.default_location_id)
            .where(Material.material_number.in_(material_numbers))
        )

        async with self.session_factory() as session:
            rows = (await session.execute(stmt)).all()

        by_material_number = {
            row.material_number: {
                'material_number': row.material_number,
                'description': row.description,
                'category': row.category,
                'quantity': int(row.quantity or 0),
                'location': row.location,
                'sap_material_number': row.sap_material_number,
            }
            for row in rows
        }
        return [
            by_material_number[material_number]
            for material_number in material_numbers
            if material_number in by_material_number
        ]


material_repository = MaterialRepository()
