"""FastAPI application entry point."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.services.delivery_store import DeliveryStore, DeliveryStoreError


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Recover retryable records left mid-send by a prior stopped process."""

    try:
        recovered = DeliveryStore(settings.delivery_store_path).recover_interrupted_attempts()
        if recovered:
            logger.warning("Recovered %s interrupted email delivery attempt(s).", recovered)
    except DeliveryStoreError:
        # Individual delivery endpoints still reject requests explicitly when
        # the store is unavailable; startup should keep health diagnostics up.
        logger.exception("Could not recover interrupted email deliveries.")
    yield


def create_app() -> FastAPI:
    """Create the API application so tests and ASGI servers share one setup."""

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Backend for voice-first vehicle and tire service-record capture. "
            "WERBAS remains the MVP's leading system."
        ),
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Accept"],
    )
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
