# CarTech Backend

FastAPI service for the mechanic-facing CarTech MVP. It provides the
application foundation, API versioning, a health endpoint, the central
Pydantic domain models, and the mechanic-registration workflow. A browser
sends its complete draft for validation and, after explicit mechanic
confirmation, for email delivery. A small durable outbox preserves every valid
confirmed record before SMTP is called, so failed deliveries can be retried
after a browser or server restart. Audio processing and AI extraction remain
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
  alternatives from one validated registration document, persists that document
  in the delivery outbox, and sends it via SMTP. A repeated request with the
  same registration ID and unchanged payload is idempotent and does not send a
  duplicate message.
- `GET /api/v1/registrations/{registration_id}/delivery-status` returns the
  durable delivery status, latest safe error message, and number of attempts.
- `POST /api/v1/registrations/{registration_id}/retry` sends the exact saved
  registration again without requiring the browser to submit the data anew.

Missing/invalid required values return `409`; a missing confirmation returns
`422`. SMTP/configuration failures return `502` or `503` with the saved
delivery status and a retry URL. The record remains in `email_failed` until a
retry succeeds. `email_pending` and `email_sending` make an unfinished attempt
visible; interrupted `email_sending` records become retryable on service start.

The only required values for handoff to WERBAS are `service_type`,
`service_date`, `mechanic_id`, and `vehicle.license_plate`. Existing
`field_status` values from extraction are preserved; `uncertain` and `invalid`
set `review_required` but do not block sending on their own. The outbox is an
audit/retry mechanism, not a general office inbox or WERBAS replacement. It
stores the complete structured confirmed registration locally (not the raw
transcript) and must therefore be placed on encrypted, access-controlled
persistent storage in production.

## Tests

Run the complete backend suite from this directory:

```bash
python3 -m pytest -q
```

`tests/test_workshop_e2e.py` executes all 23 anonymised workshop phrases from
[`data/fixtures/workshop_e2e_cases.json`](../../data/fixtures/workshop_e2e_cases.json)
through the extraction-result contract, validation API, and—using an
in-process mailbox—the durable outbox and office-email handoff. The actual
speech-to-text/AI extraction adapter remains a separate integration point; the
fixtures define its regression contract without requiring external services.

Configure SMTP in the deployment environment:

```text
CARTECH_OFFICE_EMAIL=office@example.com
CARTECH_SMTP_HOST=smtp.example.com
CARTECH_SMTP_PORT=587
CARTECH_SMTP_FROM=cartech@example.com
CARTECH_SMTP_USERNAME=...
CARTECH_SMTP_PASSWORD=...
CARTECH_SMTP_USE_TLS=true
CARTECH_SMTP_USE_SSL=false
CARTECH_SMTP_TIMEOUT_SECONDS=15
CARTECH_DELIVERY_STORE_PATH=/var/lib/cartech/cartech-deliveries.sqlite3
```

All mail configuration is read only from environment variables. An annotated,
secret-free template is available at [`.env.example`](.env.example). Do not
commit a real `.env` file or SMTP credentials. `CARTECH_SMTP_HOST` and
`CARTECH_SMTP_FROM` are required; username and password must either both be
set or both be omitted for SMTP servers without authentication.

Set `CARTECH_SMTP_USE_SSL=true` for providers using implicit TLS (usually port
465); in that case STARTTLS is not used. The default configuration uses
STARTTLS on port 587. `CARTECH_SMTP_TIMEOUT_SECONDS` controls the connection
and delivery timeout. `CARTECH_DELIVERY_STORE_PATH` is the SQLite outbox path.
Mount its parent directory as persistent storage when running in Docker or on a
VPS; deleting the file removes the retry history.

## Layout

```text
app/
  api/          Versioned REST routes
  core/         Cross-cutting application configuration
  models/       Central Pydantic domain models and enums
  main.py       FastAPI application factory
tests/          Backend unit and API smoke tests
```
