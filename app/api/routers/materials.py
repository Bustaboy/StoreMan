from fastapi import APIRouter, Query

from app.crud.material import material_repository
from app.schemas.material import MaterialRead

router = APIRouter(prefix='/materials', tags=['materials'])


@router.get('', response_model=list[MaterialRead], summary='List materials')
async def list_materials(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[MaterialRead]:
    materials = await material_repository.list_materials(limit=limit, offset=offset)
    return [MaterialRead.model_validate(material) for material in materials]


@router.get('/search', response_model=list[MaterialRead], summary='Search materials')
async def search_materials(
    q: str = Query(min_length=1),
    limit: int = Query(default=25, ge=1, le=100),
) -> list[MaterialRead]:
    materials = await material_repository.search_materials(query=q, limit=limit)
    return [MaterialRead.model_validate(material) for material in materials]
