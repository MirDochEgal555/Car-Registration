# CarTech Backend

FastAPI service for the mechanic-facing CarTech MVP. It provides the
application foundation, API versioning, a health endpoint, the central
Pydantic domain models, and the stateless mechanic-registration workflow. A
browser sends its complete draft for validation and, after explicit mechanic
confirmation, for email delivery. Audio processing and AI extraction remain
separate follow-up tasks.

## Local start

From this directory:

```bash
python3 -m pip install -e '.[dev]'
uvicorn app.main:app --reload
```

The health check is available at `GET /api/v1/health`; interactive API
documentation is available at `/docs`.

## Registration API

- `POST /api/v1/registrations/validate` validates a complete draft without
  persisting it. It returns field statuses, review hints, and the
  `mechanic_review` workflow status; known plate spelling is normalized in the
  returned draft.
- `POST /api/v1/registrations/send` validates again, requires
  `mechanic_confirmed: true`, renders matching HTML and plain-text office-email
  alternatives from one validated registration document, and sends them via SMTP.
  Missing/invalid required values return `409`; a missing confirmation returns
  `422`; an unconfigured delivery service returns `503`.

The only required values for handoff to WERBAS are `service_type`,
`service_date`, `mechanic_id`, and `vehicle.license_plate`. Existing
`field_status` values from extraction are preserved; `uncertain` and `invalid`
set `review_required` but do not block sending on their own. The endpoint does
not persist drafts, so a failed send can be retried by submitting the same
draft again.

Configure SMTP in the deployment environment:

```text
CARTECH_OFFICE_EMAIL=office@example.com
CARTECH_SMTP_HOST=smtp.example.com
CARTECH_SMTP_PORT=587
CARTECH_SMTP_FROM=cartech@example.com
CARTECH_SMTP_USERNAME=...
CARTECH_SMTP_PASSWORD=...
CARTECH_SMTP_USE_TLS=true
```

Set `CARTECH_SMTP_USE_SSL=true` for providers using implicit TLS; in that case
STARTTLS is not used.

## Layout

```text
app/
  api/          Versioned REST routes
  core/         Cross-cutting application configuration
  models/       Central Pydantic domain models and enums
  main.py       FastAPI application factory
tests/          Backend unit and API smoke tests
```
