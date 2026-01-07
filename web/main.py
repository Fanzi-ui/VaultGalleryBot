from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from models.database import ensure_media_rating_columns, ensure_model_normalized_columns
from services.rating_service import backfill_missing_ratings
from web.routes import auth, dashboard, models, media, insights

app = FastAPI(title="VaultGalleryBot Admin")

ensure_media_rating_columns()
ensure_model_normalized_columns()
backfill_missing_ratings()

# -------------------------
# Resolve project root
# -------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------
# Templates
# -------------------------
templates = Jinja2Templates(directory=BASE_DIR / "web" / "templates")

# -------------------------
# Static files (CSS / JS)
# -------------------------
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "web" / "static"),
    name="static",
)

# -------------------------
# ✅ MEDIA FILES (FIXED)
# -------------------------
MEDIA_DIR = BASE_DIR / "media"

app.mount(
    "/media",
    StaticFiles(directory=MEDIA_DIR),
    name="media",
)

# -------------------------
# Routes
# -------------------------
app.include_router(dashboard.router)
app.include_router(insights.router)
app.include_router(models.router)
app.include_router(media.router)
app.include_router(media.delete_router)
app.include_router(auth.router)
