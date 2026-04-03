from __future__ import annotations

import meilisearch
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.models import InventoryItem, Location, Material

MEILISEARCH_BATCH_SIZE = 1000


class MaterialRepository:
    def __init__(self) -> None:
        settings = get_settings()
        self.engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        self.session_factory = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self.meili_client = meilisearch.Client(settings.meilisearch_url, settings.meilisearch_master_key)

    @staticmethod
    def _normalize_string(value: object) -> str:
        return str(value or '')

    @staticmethod
    def _normalize_optional_string(value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @staticmethod
    def _get_meili_task_uid(task: object) -> object:
        if isinstance(task, dict):
            return task.get('taskUid') or task.get('task_uid') or task.get('uid')
        return (
            getattr(task, 'task_uid', None)
            or getattr(task, 'taskUid', None)
            or getattr(task, 'uid', None)
        )

    @classmethod
    def _wait_for_meili_task(cls, client: meilisearch.Client, task: object) -> None:
        task_uid = cls._get_meili_task_uid(task)
        if task_uid is None:
            raise RuntimeError('Missing Meilisearch task identifier')
        client.wait_for_task(task_uid)

    @staticmethod
    def _extract_meili_hits(search_result: object) -> list[object]:
        if isinstance(search_result, dict):
            hits = search_result.get('hits', [])
        else:
            hits = getattr(search_result, 'hits', [])
        return hits if isinstance(hits, list) else []

    @staticmethod
    def _extract_hit_value(hit: object, field_name: str) -> object:
        if isinstance(hit, dict):
            return hit.get(field_name)
        return getattr(hit, field_name, None)

    async def get_materials(self, skip: int = 0, limit: int = 100) -> list[Material]:
        clean_skip = max(skip, 0)
        clean_limit = max(limit, 1)
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
                Material,
                func.coalesce(quantity_subquery.c.quantity, 0).label('quantity'),
            )
            .options(selectinload(Material.default_location))
            .outerjoin(quantity_subquery, quantity_subquery.c.material_number == Material.material_number)
            .order_by(Material.material_number)
            .offset(clean_skip)
            .limit(clean_limit)
        )
        async with self.session_factory() as session:
            rows = (await session.execute(stmt)).all()

        materials: list[Material] = []
        for material, quantity in rows:
            setattr(material, 'quantity', int(quantity or 0))
            setattr(material, 'location', material.default_location.name if material.default_location else None)
            materials.append(material)
        return materials

    async def search_materials(self, query: str, limit: int = 50) -> list[Material]:
        clean_query = query.strip()
        clean_limit = max(limit, 1)
        if not clean_query:
            return []

        search_result = self.meili_client.index('materials').search(clean_query, {'limit': clean_limit})
        hits = self._extract_meili_hits(search_result)
        material_numbers: list[str] = []
        for hit in hits:
            material_number = self._extract_hit_value(hit, 'material_number') or self._extract_hit_value(hit, 'id')
            normalized_material_number = self._normalize_optional_string(material_number)
            if normalized_material_number is None:
                continue

            if normalized_material_number not in material_numbers:
                material_numbers.append(normalized_material_number)

        if not material_numbers:
            return []

        order = {material_number: index for index, material_number in enumerate(material_numbers)}
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
                Material,
                func.coalesce(quantity_subquery.c.quantity, 0).label('quantity'),
            )
            .options(selectinload(Material.default_location))
            .where(Material.material_number.in_(material_numbers))
            .outerjoin(quantity_subquery, quantity_subquery.c.material_number == Material.material_number)
        )
        async with self.session_factory() as session:
            rows = (await session.execute(stmt)).all()

        materials: list[Material] = []
        for material, quantity in rows:
            setattr(material, 'quantity', int(quantity or 0))
            setattr(material, 'location', material.default_location.name if material.default_location else None)
            materials.append(material)
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
                Material,
                func.coalesce(quantity_subquery.c.quantity, 0).label('quantity'),
                Location.name.label('location'),
            )
            .outerjoin(quantity_subquery, quantity_subquery.c.material_number == Material.material_number)
            .outerjoin(Location, Location.id == Material.default_location_id)
            .order_by(Material.material_number)
        )

        async with self.session_factory() as session:
            rows = (await session.execute(stmt)).all()

        documents = []
        for material, quantity, location in rows:
            normalized_material_number = self._normalize_string(material.material_number)
            normalized_description = self._normalize_string(material.description)
            normalized_quantity = int(quantity or 0)

            documents.append(
                {
                    'id': normalized_material_number,
                    'code': normalized_material_number,
                    'name': normalized_description,
                    'category': self._normalize_optional_string(material.category),
                    'quantity_on_hand': normalized_quantity,
                    'location': self._normalize_optional_string(location),
                    'material_number': normalized_material_number,
                    'description': normalized_description,
                    'sap_material_number': self._normalize_optional_string(material.sap_material_number),
                    'is_serialized': bool(material.is_serialized),
                    'quantity': normalized_quantity,
                }
            )

        materials_index = self.meili_client.index('materials')

        try:
            clear_existing_documents = False

            try:
                primary_key = materials_index.get_primary_key()
            except Exception:
                create_task = self.meili_client.create_index('materials', {'primaryKey': 'id'})
                self._wait_for_meili_task(self.meili_client, create_task)
                primary_key = 'id'

            if primary_key != 'id':
                clear_task = materials_index.delete_all_documents()
                self._wait_for_meili_task(self.meili_client, clear_task)

                primary_key_task = materials_index.update(primary_key='id')
                self._wait_for_meili_task(self.meili_client, primary_key_task)
            else:
                clear_existing_documents = True

            settings_task = materials_index.update_searchable_attributes(
                [
                    'material_number',
                    'description',
                    'category',
                    'sap_material_number',
                    'location',
                ]
            )
            self._wait_for_meili_task(self.meili_client, settings_task)

            if clear_existing_documents:
                clear_task = materials_index.delete_all_documents()
                self._wait_for_meili_task(self.meili_client, clear_task)

            for start in range(0, len(documents), MEILISEARCH_BATCH_SIZE):
                batch = documents[start:start + MEILISEARCH_BATCH_SIZE]
                if not batch:
                    continue

                task = materials_index.add_documents(batch, primary_key='id')
                self._wait_for_meili_task(self.meili_client, task)
        except Exception as exc:
            raise RuntimeError('Failed to sync materials to Meilisearch') from exc

        return len(documents)


material_repository = MaterialRepository()
