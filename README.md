# TitanWMS Backend (Skeleton)

Initial backend skeleton for TitanWMS, a fully local Warehouse Management System built with FastAPI.

## Stack
- FastAPI
- PostgreSQL 16 (+ pgBouncer)
- Redis
- Celery
- Meilisearch
- Docker Compose
- SQLAlchemy 2.0 + Alembic

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
alembic/
```

## Database Migrations (Docker-only)

Run all Alembic commands in the API container so everything stays local and reproducible.

1. Start services:

```bash
docker compose up -d db pgbouncer api
```

2. Generate the first migration from models:

```bash
docker compose exec api alembic revision --autogenerate -m "initial schema"
```

3. Apply migrations:

```bash
docker compose exec api alembic upgrade head
```

4. (Optional) Check current revision:

```bash
docker compose exec api alembic current
```

## Notes
- This project is fully local and intended to run through Docker Compose.
- Domain models are in `app/models/models.py` using SQLAlchemy 2.0 declarative mappings.
