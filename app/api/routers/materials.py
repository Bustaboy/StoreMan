from fastapi import APIRouter, Query

from app.crud.material import material_repository
from app.schemas.material import ApiResult, MaterialRead, MaterialsPage

router = APIRouter(prefix='/materials', tags=['materials'])


@router.get('', response_model=ApiResult[MaterialsPage], summary='List materials')
async def list_materials(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> ApiResult[MaterialsPage]:
    materials, total = await material_repository.list_materials(limit=limit, offset=offset)
    payload = MaterialsPage(
        items=[MaterialRead.model_validate(material) for material in materials],
        limit=limit,
        offset=offset,
        total=total,
    )
    return ApiResult[MaterialsPage](data=payload)


@router.get('/search', response_model=ApiResult[list[MaterialRead]], summary='Search materials')
async def search_materials(
    q: str = Query(min_length=1),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResult[list[MaterialRead]]:
    materials = await material_repository.search_materials(query=q, limit=limit, offset=offset)
    payload = [MaterialRead.model_validate(material) for material in materials]
    return ApiResult[list[MaterialRead]](data=payload)
