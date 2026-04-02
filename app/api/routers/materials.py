from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.material import MaterialRepository, get_db_session
from app.schemas.material import MaterialResponse

router = APIRouter(tags=['materials'])


@router.get('/materials', response_model=list[MaterialResponse])
async def list_materials(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db_session),
) -> list[MaterialResponse]:
    repository = MaterialRepository(session)
    materials = await repository.get_materials(skip=skip, limit=limit)
    return [MaterialResponse.model_validate(material) for material in materials]
