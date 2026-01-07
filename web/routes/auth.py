import os

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from web.auth import (
    SERVER_SESSION_TOKEN,
    is_login_blocked,
    record_failed_login,
    reset_login_attempts,
    secure_cookies_enabled,
    verify_admin_credentials,
)

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")


@router.get("/login")
def login_form(request: Request, error: str | None = None):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": error},
    )


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    client_ip = request.client.host if request.client else "unknown"
    blocked, retry_after = is_login_blocked(client_ip)
    if blocked:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": f"Too many attempts. Try again in {retry_after}s.",
            },
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    if not verify_admin_credentials(username, password):
        record_failed_login(client_ip)
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    reset_login_attempts(client_ip)

    admin_token = os.getenv("WEB_ADMIN_TOKEN")
    if not admin_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfigured: WEB_ADMIN_TOKEN is not set",
        )

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    cookie_secure = secure_cookies_enabled()
    response.set_cookie(
        "admin_token",
        admin_token,
        httponly=True,
        samesite="lax",
        secure=cookie_secure,
    )
    response.set_cookie(
        "session_token",
        SERVER_SESSION_TOKEN,
        httponly=True,
        samesite="lax",
        secure=cookie_secure,
    )
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("admin_token")
    response.delete_cookie("session_token")
    return response
