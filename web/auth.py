import os
from pathlib import Path

from fastapi import HTTPException, Request, status
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def require_admin_token(request: Request) -> None:
    admin_token = os.getenv("WEB_ADMIN_TOKEN")
    if not admin_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfigured: WEB_ADMIN_TOKEN is not set",
        )

    token = (
        request.query_params.get("token")
        or request.headers.get("X-Admin-Token")
        or request.cookies.get("admin_token")
    )

    if token != admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


def get_request_token(request: Request) -> str:
    return (
        request.query_params.get("token")
        or request.headers.get("X-Admin-Token")
        or request.cookies.get("admin_token")
        or ""
    )


def verify_admin_credentials(username: str, password: str) -> bool:
    return username == "admin" and password == "pass123"
