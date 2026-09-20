"""FastAPI application entry point."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from app.api.v1.router import api_router
from app.api.v1.routes.audio import audio_error_response
from app.core.config import settings
from app.core.auth import read_session
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

    @application.middleware("http")
    async def require_workshop_session(request: Request, call_next):
        """Require the signed app session for all business API endpoints."""

        public_paths = {
            f"{settings.api_v1_prefix}/health",
            f"{settings.api_v1_prefix}/auth/session",
            f"{settings.api_v1_prefix}/auth/login",
            f"{settings.api_v1_prefix}/auth/logout",
        }
        if (
            not settings.app_auth_enabled
            or request.method == "OPTIONS"
            or not request.url.path.startswith(settings.api_v1_prefix)
            or request.url.path in public_paths
        ):
            return await call_next(request)
        username = read_session(
            request.cookies.get("cartech_session"), settings.app_auth_session_secret or ""
        )
        if username != settings.app_auth_username:
            return JSONResponse(status_code=401, content={"detail": "Anmeldung erforderlich."})
        return await call_next(request)
    application.include_router(api_router, prefix=settings.api_v1_prefix)

    @application.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request, error: RequestValidationError
    ):
        """Keep malformed audio-form errors in the audio API's public shape."""

        if request.url.path == f"{settings.api_v1_prefix}/audio/transcribe":
            return audio_error_response(
                status_code=400,
                code="invalid_audio_upload",
                message="Im Feld 'audio' muss eine Audiodatei hochgeladen werden.",
            )
        return await request_validation_exception_handler(request, error)

    @application.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, error: StarletteHTTPException):
        """Make malformed multipart bodies an actionable audio-upload error."""

        if (
            request.url.path == f"{settings.api_v1_prefix}/audio/transcribe"
            and error.status_code == 400
        ):
            return audio_error_response(
                status_code=400,
                code="invalid_audio_upload",
                message="Die Audio-Upload-Anfrage konnte nicht gelesen werden.",
            )
        return await http_exception_handler(request, error)

    return application


app = create_app()
