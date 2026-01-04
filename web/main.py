from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from web.routes import dashboard, models, media

app = FastAPI(title="VaultGalleryBot Admin")

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
app.include_router(models.router)
app.include_router(media.router)
