import os
import secrets
from pathlib import Path

from fastapi import HTTPException, Request, status
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
SERVER_SESSION_TOKEN = secrets.token_urlsafe(32)


def require_admin_token(request: Request) -> None:
    if not is_admin_request(request):
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
            detail="Unauthorized",
        )


def get_request_token(request: Request) -> str:
    return (
        request.query_params.get("token")
        or request.headers.get("X-Admin-Token")
        or request.cookies.get("admin_token")
        or ""
    )


def get_request_session_token(request: Request) -> str:
    return request.cookies.get("session_token") or ""


def is_admin_request(request: Request) -> bool:
    admin_token = os.getenv("WEB_ADMIN_TOKEN")
    if not admin_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfigured: WEB_ADMIN_TOKEN is not set",
        )

    return (
        get_request_token(request) == admin_token
        and get_request_session_token(request) == SERVER_SESSION_TOKEN
    )


def verify_admin_credentials(username: str, password: str) -> bool:
    admin_user = os.getenv("WEB_ADMIN_USER", "admin")
    admin_pass = os.getenv("WEB_ADMIN_PASS", "pass123")
    return username == admin_user and password == admin_pass
