"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    """Create the API application so tests and ASGI servers share one setup."""

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Backend for voice-first vehicle and tire service-record capture. "
            "WERBAS remains the MVP's leading system."
        ),
    )
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
