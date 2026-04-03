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
    return [
        MaterialResponse(
            material_number=material.material_number,
            description=material.description,
            category=material.category,
            quantity=int(getattr(material, 'quantity', 0)),
            location=getattr(material, 'location', None),
            updated_at=getattr(material, 'updated_at', None),
        )
        for material in materials
    ]
