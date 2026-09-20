"""Same-origin workshop login endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel

from app.core.auth import create_session, read_session, verify_password
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])
COOKIE_NAME = "cartech_session"


class LoginRequest(BaseModel):
    username: str
    password: str


class SessionResponse(BaseModel):
    authentication_enabled: bool
    authenticated: bool
    username: Optional[str] = None


def _username_from_request(request: Request) -> str | None:
    if not settings.app_auth_enabled:
        return None
    return read_session(request.cookies.get(COOKIE_NAME), settings.app_auth_session_secret or "")


@router.get("/session", response_model=SessionResponse)
def session(request: Request) -> SessionResponse:
    username = _username_from_request(request)
    return SessionResponse(
        authentication_enabled=settings.app_auth_enabled,
        authenticated=not settings.app_auth_enabled or username is not None,
        username=username,
    )


@router.post("/login", response_model=SessionResponse)
def login(credentials: LoginRequest, response: Response) -> SessionResponse:
    valid = settings.app_auth_enabled and (
        credentials.username == settings.app_auth_username
        and verify_password(credentials.password, settings.app_auth_password_hash or "")
    )
    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültige Zugangsdaten.")

    response.set_cookie(
        key=COOKIE_NAME,
        value=create_session(
            credentials.username,
            settings.app_auth_session_secret or "",
            settings.app_auth_session_ttl_seconds,
        ),
        max_age=settings.app_auth_session_ttl_seconds,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/api",
    )
    return SessionResponse(authentication_enabled=True, authenticated=True, username=credentials.username)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    response.delete_cookie(key=COOKIE_NAME, path="/api", secure=True, httponly=True, samesite="strict")
    return response
