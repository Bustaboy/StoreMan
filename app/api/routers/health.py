from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings

settings = get_settings()
router = APIRouter()


@router.get('/health', summary='Service health check')
async def health_check() -> dict[str, str]:
    db_status = 'ok'
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    try:
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
    except Exception:
        db_status = 'unavailable'
    finally:
        await engine.dispose()

    status = 'ok' if db_status == 'ok' else 'degraded'
    return {'status': status, 'database': db_status}
