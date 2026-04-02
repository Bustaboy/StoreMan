from __future__ import annotations

import meilisearch
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.models import InventoryItem, Location, Material


class MaterialRepository:
    def __init__(self) -> None:
        settings = get_settings()
        self.engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        self.session_factory = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self.meili_client = meilisearch.Client(
            settings.meilisearch_url,
            settings.meilisearch_master_key,
        )

    async def get_materials(self, skip: int = 0, limit: int = 100) -> list[Material]:
        clean_skip = max(skip, 0)
        clean_limit = max(limit, 1)
        stmt = (
            select(Material)
            .options(selectinload(Material.default_location))
            .order_by(Material.material_number)
            .offset(clean_skip)
            .limit(clean_limit)
        )
        async with self.session_factory() as session:
            materials = list((await session.scalars(stmt)).all())

        return await self._attach_quantities(materials)


    async def _attach_quantities(self, materials: list[Material]) -> list[Material]:
        if not materials:
            return materials

        material_numbers = [material.material_number for material in materials]
        qty_stmt = (
            select(
                InventoryItem.material_id,
                func.coalesce(func.sum(InventoryItem.quantity), 0).label('quantity'),
            )
            .where(InventoryItem.material_id.in_(material_numbers))
            .group_by(InventoryItem.material_id)
        )

        async with self.session_factory() as session:
            quantities = {row.material_id: int(row.quantity or 0) for row in (await session.execute(qty_stmt)).all()}

        for material in materials:
            setattr(material, 'quantity', quantities.get(material.material_number, 0))

        return materials

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
        stmt = (
            select(Material)
            .options(selectinload(Material.default_location))
            .where(Material.material_number.in_(material_numbers))
        )
        async with self.session_factory() as session:
            materials = list((await session.scalars(stmt)).all())

        materials = await self._attach_quantities(materials)
        return sorted(materials, key=lambda material: order.get(material.material_number, len(order)))

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
                Material.is_serialized,
                func.coalesce(quantity_subquery.c.quantity, 0).label('quantity'),
                Location.name.label('location'),
            )
            .outerjoin(quantity_subquery, quantity_subquery.c.material_number == Material.material_number)
            .outerjoin(Location, Location.id == Material.default_location_id)
            .order_by(Material.material_number)
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
                'is_serialized': bool(row.is_serialized),
            }
            for row in rows
        ]

        materials_index = self.meili_client.index('materials')
        settings_task = materials_index.update_searchable_attributes(
            [
                'material_number',
                'description',
                'category',
                'sap_material_number',
                'location',
            ]
        )
        self.meili_client.wait_for_task(settings_task.task_uid)

        task = materials_index.add_documents(documents, primary_key='id')
        self.meili_client.wait_for_task(task.task_uid)
        return len(documents)


material_repository = MaterialRepository()
