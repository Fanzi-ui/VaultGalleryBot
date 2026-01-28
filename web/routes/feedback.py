from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from web.auth import require_admin_token


router = APIRouter(prefix="/api/feedback", dependencies=[Depends(require_admin_token)])


class FeedbackPayload(BaseModel):
    message: str | None = None
    logs: str | None = None


def _summarize_logs(logs: str) -> tuple[int, int]:
    if not logs:
        return 0, 0
    lines = [line for line in logs.splitlines() if line.strip()]
    error_lines = [
        line
        for line in lines
        if "error" in line.lower()
        or "exception" in line.lower()
        or "traceback" in line.lower()
    ]
    return len(lines), len(error_lines)


@router.post("")
def feedback(payload: FeedbackPayload) -> dict:
    log_lines, error_lines = _summarize_logs(payload.logs or "")

    if payload.message:
        reply = (
            "Message received. "
            "Paste logs if you want a quick error scan."
        )
    elif payload.logs:
        if log_lines == 0:
            reply = "No log lines detected. Paste the raw log output."
        elif error_lines:
            reply = f"Scanned {log_lines} lines. Found {error_lines} error-like lines."
        else:
            reply = f"Scanned {log_lines} lines. No error keywords detected."
    else:
        reply = "Nothing received. Add a message or paste logs."

    return {
        "ok": True,
        "reply": reply,
        "log_lines": log_lines,
        "error_lines": error_lines,
    }
