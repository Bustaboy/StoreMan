# TitanWMS Backend (Skeleton)

Initial backend skeleton for TitanWMS, a fully local Warehouse Management System built with FastAPI.

## Stack
- FastAPI
- PostgreSQL 16 (+ pgBouncer)
- Redis
- Celery
- Meilisearch
- Docker Compose

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

API docs:
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Health check:
- `GET http://localhost:8000/health`

## Database Migrations (Alembic)

Run migrations from the API container to ensure environment variables and network aliases match Docker Compose:

```bash
docker compose run --rm api alembic revision --autogenerate -m "initial schema"
docker compose run --rm api alembic upgrade head
```

Check current migration state:

```bash
docker compose run --rm api alembic current
docker compose run --rm api alembic history
```

## Project Structure

```text
app/
  api/
    routers/
  core/
  crud/
  models/
  schemas/
  services/
  utils/
```

## Notes
- This is skeleton only: no domain models, migrations, or business logic are implemented yet.
- Use `.env` for local configuration.
