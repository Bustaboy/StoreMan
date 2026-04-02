from fastapi import APIRouter

from app.api.routers.health import router as health_router
from app.api.routers.materials import router as materials_router

api_router = APIRouter()
api_router.include_router(health_router, tags=['health'])
api_router.include_router(materials_router)
