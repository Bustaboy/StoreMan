from fastapi import APIRouter, Query

from app.crud.material import material_repository
from app.schemas.material import ApiResult, MaterialResponse

router = APIRouter(prefix='/materials', tags=['materials'])


@router.get('', response_model=ApiResult[list[MaterialResponse]], summary='List materials')
async def list_materials(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> ApiResult[list[MaterialResponse]]:
    materials = await material_repository.get_materials(skip=skip, limit=limit)
    payload = [MaterialResponse.model_validate(material) for material in materials]
    return ApiResult[list[MaterialResponse]](data=payload)


@router.get('/search', response_model=ApiResult[list[MaterialResponse]], summary='Search materials')
async def search_materials(
    q: str = Query(min_length=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> ApiResult[list[MaterialResponse]]:
    try:
        materials = await material_repository.search_materials(query=q, limit=limit)
    except Exception:
        materials = []
    if not materials:
        materials = await material_repository.search_materials_db(query=q, limit=limit)
    payload = [MaterialResponse.model_validate(material) for material in materials]
    return ApiResult[list[MaterialResponse]](data=payload)


@router.post('/sync', response_model=ApiResult[dict[str, int]], summary='Sync materials to Meilisearch')
async def sync_materials() -> ApiResult[dict[str, int]]:
    indexed = await material_repository.sync_to_meilisearch()
    return ApiResult[dict[str, int]](data={'indexed': indexed})
