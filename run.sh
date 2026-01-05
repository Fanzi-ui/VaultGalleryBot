#!/usr/bin/env bash
set -euo pipefail

python app.py &
BOT_PID=$!

cleanup() {
  kill "$BOT_PID" 2>/dev/null || true
}
trap cleanup EXIT

uvicorn web.main:app --reload
