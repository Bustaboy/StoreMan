from fastapi import APIRouter, HTTPException, Query

from app.crud.material import material_repository
from app.models.models import Material
from app.schemas.material import MaterialResponse

router = APIRouter(tags=['materials'])


def _normalize_optional_string(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _to_material_response(material: Material) -> MaterialResponse:
    material_number = str(getattr(material, 'material_number', '') or '')
    description = str(getattr(material, 'description', '') or '')
    quantity_on_hand = int(getattr(material, 'quantity', 0) or 0)
    location = _normalize_optional_string(getattr(material, 'location', None))
    if location is None:
        default_location = getattr(material, 'default_location', None)
        location = _normalize_optional_string(default_location.name if default_location else None)

    return MaterialResponse(
        id=material_number,
        code=material_number,
        name=description,
        quantity_on_hand=quantity_on_hand,
        location=location,
        material_number=material_number,
        description=description,
        category=_normalize_optional_string(getattr(material, 'category', None)),
        sap_material_number=_normalize_optional_string(getattr(material, 'sap_material_number', None)),
        is_serialized=bool(getattr(material, 'is_serialized', False)),
    )


@router.get('/materials', response_model=list[MaterialResponse], summary='List materials')
async def list_materials(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[MaterialResponse]:
    try:
        materials = await material_repository.get_materials(skip=skip, limit=limit)
        return [_to_material_response(material) for material in materials]
    except Exception as exc:
        raise HTTPException(status_code=500, detail='Unable to load materials') from exc


@router.get('/materials/search', response_model=list[MaterialResponse], summary='Search materials')
async def search_materials(
    q: str = Query(min_length=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[MaterialResponse]:
    try:
        materials = await material_repository.search_materials(query=q, limit=limit)
        return [_to_material_response(material) for material in materials]
    except Exception as exc:
        raise HTTPException(status_code=500, detail='Unable to search materials') from exc


@router.post('/materials/sync', summary='Sync materials index')
async def sync_materials() -> dict[str, int]:
    try:
        indexed_documents = await material_repository.sync_to_meilisearch()
        return {'indexed': indexed_documents}
    except Exception as exc:
        raise HTTPException(status_code=500, detail='Unable to sync materials index') from exc
