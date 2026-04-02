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


## Database Migrations

Generate the initial migration after model changes:

```bash
docker compose run --rm api alembic revision --autogenerate -m "initial schema"
```

Apply migrations:

```bash
docker compose run --rm api alembic upgrade head
```

Check migration state:

```bash
docker compose run --rm api alembic current
```

## Notes
- Domain models and Alembic environment are scaffolded for local development.
- Use `.env` for local configuration.
