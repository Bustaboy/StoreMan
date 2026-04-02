from fastapi import APIRouter, Query

from app.crud.material import material_repository
from app.schemas.material import MaterialResponse

router = APIRouter(tags=['materials'])


@router.get('/materials', response_model=list[MaterialResponse], summary='List materials')
async def list_materials(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[MaterialResponse]:
    materials = await material_repository.get_materials(skip=skip, limit=limit)
    return [
        MaterialResponse(
            material_number=material.material_number,
            description=material.description,
            category=material.category,
            quantity=int(getattr(material, 'quantity', 0)),
            location=material.default_location.name if material.default_location else None,
            sap_material_number=material.sap_material_number,
            is_serialized=material.is_serialized,
        )
        for material in materials
    ]


@router.get('/materials/search', response_model=list[MaterialResponse], summary='Search materials')
async def search_materials(
    q: str = Query(min_length=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[MaterialResponse]:
    materials = await material_repository.search_materials(query=q, limit=limit)
    return [
        MaterialResponse(
            material_number=material.material_number,
            description=material.description,
            category=material.category,
            quantity=int(getattr(material, 'quantity', 0)),
            location=material.default_location.name if material.default_location else None,
            sap_material_number=material.sap_material_number,
            is_serialized=material.is_serialized,
        )
        for material in materials
    ]


@router.post('/materials/sync', summary='Sync materials index')
async def sync_materials() -> dict[str, int]:
    indexed_documents = await material_repository.sync_to_meilisearch()
    return {'indexed': indexed_documents}
