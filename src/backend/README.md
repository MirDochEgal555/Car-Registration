# CarTech Backend

FastAPI service for the mechanic-facing CarTech MVP. It currently provides the
application foundation, API versioning, a health endpoint, and the central
Pydantic domain models. Audio processing, AI extraction, validation workflows,
and email delivery follow in later phase-2 tasks.

## Local start

From this directory:

```bash
python3 -m pip install -e '.[dev]'
uvicorn app.main:app --reload
```

The health check is available at `GET /api/v1/health`; interactive API
documentation is available at `/docs`.

## Layout

```text
app/
  api/          Versioned REST routes
  core/         Cross-cutting application configuration
  models/       Central Pydantic domain models and enums
  main.py       FastAPI application factory
tests/          Backend unit and API smoke tests
```
