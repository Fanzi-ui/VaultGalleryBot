import os
import secrets
import time
from pathlib import Path

from fastapi import HTTPException, status, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SERVER_SESSION_TOKEN = secrets.token_urlsafe(32)
FAILED_LOGINS: dict[str, list[float]] = {}
LOCKED_UNTIL: dict[str, float] = {}
MAX_LOGIN_ATTEMPTS = 5
WINDOW_SECONDS = 10 * 60
LOCKOUT_SECONDS = 15 * 60

api_key_scheme = HTTPBearer(auto_error=False)


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
        # If token is not set, we can't secure anything with it, so we prevent access.
        # This should ideally be caught at startup or via config validation.
        return False

    return (
        get_request_token(request) == admin_token
        and get_request_session_token(request) == SERVER_SESSION_TOKEN
    )


def require_admin_token(request: Request) -> None:
    if not is_admin_request(request):
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
            detail="Unauthorized",
        )


def verify_admin_credentials(username: str, password: str) -> bool:
    admin_user = os.getenv("WEB_ADMIN_USER", "admin")
    admin_pass = os.getenv("WEB_ADMIN_PASS", "pass123")
    return username == admin_user and password == admin_pass


def is_login_blocked(ip: str) -> tuple[bool, int]:
    now = time.time()
    locked_until = LOCKED_UNTIL.get(ip)
    if locked_until and locked_until > now:
        return True, int(locked_until - now)
    if locked_until and locked_until <= now:
        LOCKED_UNTIL.pop(ip, None)
    return False, 0


def record_failed_login(ip: str) -> None:
    now = time.time()
    attempts = [t for t in FAILED_LOGINS.get(ip, []) if now - t < WINDOW_SECONDS]
    attempts.append(now)
    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        LOCKED_UNTIL[ip] = now + LOCKOUT_SECONDS
        FAILED_LOGINS[ip] = []
        return
    FAILED_LOGINS[ip] = attempts


def reset_login_attempts(ip: str) -> None:
    FAILED_LOGINS.pop(ip, None)
    LOCKED_UNTIL.pop(ip, None)


def secure_cookies_enabled() -> bool:
    return os.getenv("WEB_SECURE_COOKIES", "false").lower() in {"1", "true", "yes"}


def require_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(api_key_scheme),
) -> str:
    if is_admin_request(request):
        return "session"
    admin_token = os.getenv("WEB_ADMIN_TOKEN")
    if not admin_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfigured: WEB_ADMIN_TOKEN is not set in .env",
        )
    if credentials and credentials.credentials == admin_token:
        return credentials.credentials
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
        headers={"WWW-Authenticate": "Bearer"},
    )
