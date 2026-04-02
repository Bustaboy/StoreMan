from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    app_name: str = 'NDT-S WMS API'
    app_env: str = Field(default='development', alias='APP_ENV')
    debug: bool = Field(default=True, alias='DEBUG')
    host: str = Field(default='0.0.0.0', alias='HOST')
    port: int = Field(default=8000, alias='PORT')
    log_level: str = Field(default='INFO', alias='LOG_LEVEL')

    database_url: str = Field(
        default='postgresql+asyncpg://ndts:ndts@pgbouncer:5432/ndts_wms',
        alias='DATABASE_URL',
    )
    sync_database_url: str = Field(
        default='postgresql://ndts:ndts@pgbouncer:5432/ndts_wms',
        alias='SYNC_DATABASE_URL',
    )
    redis_url: str = Field(default='redis://redis:6379/0', alias='REDIS_URL')
    meilisearch_url: str = Field(default='http://meilisearch:7700', alias='MEILISEARCH_URL')
    meilisearch_master_key: str = Field(default='change-me', alias='MEILISEARCH_MASTER_KEY')

    celery_broker_url: str = Field(default='redis://redis:6379/1', alias='CELERY_BROKER_URL')
    celery_result_backend: str = Field(default='redis://redis:6379/2', alias='CELERY_RESULT_BACKEND')


@lru_cache
def get_settings() -> Settings:
    return Settings()
