"""Operational endpoints that do not expose business data."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: str


@router.get("/health", response_model=HealthResponse, summary="Check API availability")
def health_check() -> HealthResponse:
    """Return a minimal liveness response for deployments and local checks."""

    return HealthResponse(status="ok")
