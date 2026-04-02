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
    payload = [
        MaterialResponse.model_validate(summary)
        for summary in await material_repository.get_material_summaries(materials)
    ]
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

    payload = [
        MaterialResponse.model_validate(summary)
        for summary in await material_repository.get_material_summaries(materials)
    ]
    return ApiResult[list[MaterialResponse]](data=payload)


@router.post('/sync', response_model=ApiResult[int], summary='Sync materials index')
async def sync_materials() -> ApiResult[int]:
    indexed_documents = await material_repository.sync_to_meilisearch()
    return ApiResult[int](data=indexed_documents)
