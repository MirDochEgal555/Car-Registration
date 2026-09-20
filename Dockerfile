# Build the static mechanic PWA first. It uses relative API paths, so Caddy can
# serve both the frontend and API from one HTTPS origin.
FROM node:22-alpine AS frontend-build
ARG VITE_APP_AUTH_ENABLED=false
ENV VITE_APP_AUTH_ENABLED=$VITE_APP_AUTH_ENABLED
WORKDIR /build/frontend
COPY src/frontend/package*.json ./
RUN npm ci
COPY src/frontend/ ./
RUN npm run build

FROM python:3.12-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /app
RUN python -m venv /opt/venv
COPY src/backend/pyproject.toml ./
RUN pip install --no-cache-dir .
COPY src/backend/app ./app
RUN useradd --system --create-home --uid 10001 cartech \
    && mkdir -p /var/lib/cartech \
    && chown -R cartech:cartech /app /var/lib/cartech
USER cartech
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

FROM caddy:2-alpine AS web
COPY deploy/Caddyfile /etc/caddy/Caddyfile
COPY --from=frontend-build /build/frontend/dist /srv
