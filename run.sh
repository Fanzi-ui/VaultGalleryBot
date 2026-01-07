#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=".env"
VENV_DIR="venv"

ensure_venv() {
  if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
  fi
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
}

install_deps() {
  if [ -f requirements.txt ]; then
    pip install -r requirements.txt
  fi
}

load_env() {
  if [ ! -f "$ENV_FILE" ]; then
    echo ".env not found. Create one first (see .env.example)."
    return 1
  fi
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      "" | \#*) continue ;;
      [A-Za-z_]*=*)
        export "$line"
        ;;
      *)
        echo "Warning: skipping invalid .env line: $line"
        ;;
    esac
  done < "$ENV_FILE"
}

env_needs_setup() {
  if [ ! -f "$ENV_FILE" ]; then
    return 0
  fi
  local bot_token authorized_users
  bot_token="$(awk -F= '/^BOT_TOKEN=/{sub(/^BOT_TOKEN=/,"");print; exit}' "$ENV_FILE")"
  authorized_users="$(awk -F= '/^AUTHORIZED_USERS=/{sub(/^AUTHORIZED_USERS=/,"");print; exit}' "$ENV_FILE")"
  case "$bot_token" in
    ""|"your_bot_token_here"|"your_own_bot_token_here") return 0 ;;
  esac
  case "$authorized_users" in
    ""|"your_user_id_here") return 0 ;;
  esac
  return 1
}

LOG_DIR="logs"
mkdir -p "$LOG_DIR"
INSTALL_LOG="$LOG_DIR/install.log"
BOT_LOG="$LOG_DIR/bot.log"
WEB_LOG="$LOG_DIR/web.log"

echo "Starting VaultGalleryBot..."
ensure_venv
install_deps >"$INSTALL_LOG" 2>&1 || {
  echo "Dependency install failed. Check $INSTALL_LOG."
  exit 1
}
echo "Launching setup..."
python install.py || {
  echo "Setup failed. Run python install.py to retry."
  exit 1
}
load_env || exit 1

python app.py >"$BOT_LOG" 2>&1 &
BOT_PID=$!

cleanup() {
  kill "$BOT_PID" 2>/dev/null || true
  kill "$WEB_PID" 2>/dev/null || true
}
trap cleanup EXIT

uvicorn web.main:app --reload >"$WEB_LOG" 2>&1 &
WEB_PID=$!

echo "VaultGalleryBot is running."
echo "Bot: READY"
echo "Web: READY (http://127.0.0.1:8000)"

while true; do
  if ! kill -0 "$BOT_PID" 2>/dev/null; then
    wait "$BOT_PID" || true
    echo "Bot crashed. Check $BOT_LOG."
    exit 1
  fi
  if ! kill -0 "$WEB_PID" 2>/dev/null; then
    wait "$WEB_PID" || true
    echo "Web server crashed. Check $WEB_LOG."
    exit 1
  fi
  sleep 1
done
