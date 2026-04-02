# NDT-S WMS Backend (Skeleton)

Initial backend skeleton for a fully local Warehouse Management System built with FastAPI.

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

## Notes
- This is skeleton only: no domain models, migrations, or business logic are implemented yet.
- Use `.env` for local configuration.
