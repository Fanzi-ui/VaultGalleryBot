import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# --- Telegram ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in .env")

# --- Security ---
AUTHORIZED_USERS = {
    int(uid)
    for uid in os.getenv("AUTHORIZED_USERS", "").split(",")
    if uid.strip()
}

if not AUTHORIZED_USERS:
    raise RuntimeError("AUTHORIZED_USERS is not set in .env")

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent
MEDIA_ROOT = BASE_DIR / os.getenv("MEDIA_ROOT", "media/models")

MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
