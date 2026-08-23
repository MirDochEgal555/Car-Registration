"""Router composition for API version 1."""

from fastapi import APIRouter

from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.registrations import router as registrations_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(registrations_router)
