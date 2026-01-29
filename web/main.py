import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, func

from models.database import (
    ensure_media_rating_columns,
    ensure_model_card_columns,
    ensure_model_normalized_columns,
    SessionLocal,
)
from models.media_entity import Media
from models.model_entity import Model
from services import model_service, storage_service
from services.card_service import clamp_card_value, compute_power_score, compute_star_rating
from services.rating_service import backfill_missing_ratings
from services.score_service import update_model_scores_from_source
from web.auth import is_admin_request, require_admin_token
from web.routes import auth, dashboard, insights, media, models
from web.routes.media import media_path_to_url

app = FastAPI(title="VaultGalleryBot API")

def _env_flag(name: str) -> str:
    return "set" if os.getenv(name) else "missing"

print(
    "Startup env check:",
    f"WEB_ADMIN_TOKEN={_env_flag('WEB_ADMIN_TOKEN')}",
    f"WEB_ADMIN_USER={_env_flag('WEB_ADMIN_USER')}",
    f"WEB_ADMIN_PASS={_env_flag('WEB_ADMIN_PASS')}",
    f"WEB_SECURE_COOKIES={_env_flag('WEB_SECURE_COOKIES')}",
    f"DATABASE_URL={_env_flag('DATABASE_URL')}",
)

ensure_media_rating_columns()
ensure_model_normalized_columns()
ensure_model_card_columns()
backfill_missing_ratings()
if os.getenv("SCORE_ON_START", "true").lower() in {"1", "true", "yes"}:
    session = SessionLocal()
    try:
        update_model_scores_from_source(session)
    except Exception as exc:
        print(f"Score refresh failed: {exc}")
    finally:
        session.close()

# -------------------------
# Resolve project root
# -------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------
# Templates (kept for potential internal use or future web UI)
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
# Static files for media (kept for mobile app to directly access media URLs)
# -------------------------
MEDIA_DIR = BASE_DIR / "media"

app.mount(
    "/media",
    StaticFiles(directory=MEDIA_DIR),
    name="media",
)

# -------------------------
# UI Routes
# -------------------------
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(insights.router)

# -------------------------
# API Routes
# -------------------------
app.include_router(models.router)
app.include_router(media.router)


def _slugify_model_name(name: str) -> str:
    return storage_service.normalize_model_name(name)


def _extract_slug_and_filename(file_path: str | None) -> tuple[str, str]:
    if not file_path:
        return "", ""

    path = file_path.replace("\\", "/")
    marker = "/media/models/"
    if marker not in path:
        return "", Path(path).name

    tail = path.split(marker, 1)[1]
    parts = [p for p in tail.split("/") if p]
    if len(parts) < 2:
        return "", Path(path).name

    return parts[0], parts[-1]


def _get_model_by_slug(session, slug: str) -> Model | None:
    models_list = session.query(Model).order_by(Model.name).all()
    for model in models_list:
        if _slugify_model_name(model.name) == slug:
            return model
    return None

@app.get("/upload", dependencies=[Depends(require_admin_token)])
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/models", dependencies=[Depends(require_admin_token)])
def models_page(request: Request):
    if not is_admin_request(request):
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
            detail="Unauthorized",
        )

    session = SessionLocal()
    try:
        models_list = session.query(Model).order_by(Model.name).all()

        count_rows = (
            session.query(Media.model_id, Media.media_type, func.count(Media.id))
            .group_by(Media.model_id, Media.media_type)
            .all()
        )
        image_counts: dict[int, int] = {}
        video_counts: dict[int, int] = {}
        for model_id, media_type, count in count_rows:
            if media_type == "image":
                image_counts[model_id] = int(count)
            elif media_type == "video":
                video_counts[model_id] = int(count)

        last_upload_rows = (
            session.query(Media.model_id, func.max(Media.created_at))
            .group_by(Media.model_id)
            .all()
        )
        last_upload_by_model: dict[int, object] = {
            model_id: last_upload for model_id, last_upload in last_upload_rows
        }

        latest_subquery = (
            session.query(
                Media.model_id.label("model_id"),
                func.max(Media.created_at).label("max_created_at"),
            )
            .group_by(Media.model_id)
            .subquery()
        )
        latest_rows = (
            session.query(Media)
            .join(
                latest_subquery,
                (Media.model_id == latest_subquery.c.model_id)
                & (Media.created_at == latest_subquery.c.max_created_at),
            )
            .order_by(desc(Media.created_at))
            .all()
        )
        preview_by_model: dict[int, Media] = {}
        for media_row in latest_rows:
            preview_by_model.setdefault(media_row.model_id, media_row)

        models_view = []
        for model in models_list:
            slug = _slugify_model_name(model.name)
            preview_file = None
            preview_type = None
            preview_media = preview_by_model.get(model.id)
            if preview_media:
                slug_from_path, filename = _extract_slug_and_filename(preview_media.file_path)
                if slug_from_path:
                    slug = slug_from_path
                preview_file = filename or None
                preview_type = preview_media.media_type

            models_view.append(
                {
                    "name": model.name,
                    "slug": slug,
                    "image_count": image_counts.get(model.id, 0),
                    "video_count": video_counts.get(model.id, 0),
                    "preview_file": preview_file,
                    "preview_type": preview_type,
                    "last_upload": last_upload_by_model.get(model.id),
                }
            )
    finally:
        session.close()

    return templates.TemplateResponse(
        "models.html",
        {
            "request": request,
            "models": models_view,
        },
    )

@app.get("/models/{slug}", dependencies=[Depends(require_admin_token)])
def model_gallery_page(request: Request, slug: str, page: int = 1):
    if not is_admin_request(request):
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
            detail="Unauthorized",
        )

    session = SessionLocal()
    per_page = 48
    page = max(1, page)

    try:
        model = _get_model_by_slug(session, slug)
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

        base_query = session.query(Media).filter(Media.model_id == model.id)
        total = base_query.count()
        rows = (
            base_query
            .order_by(desc(Media.created_at))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        media_items = []
        for media_row in rows:
            url = media_path_to_url(media_row.file_path)
            if not url:
                continue
            media_items.append(
                {
                    "id": media_row.id,
                    "url": url,
                    "model_name": model.name,
                    "rating": media_row.rating,
                    "rating_caption": media_row.rating_caption,
                    "media_type": media_row.media_type,
                    "created_at": (
                        media_row.created_at.isoformat()
                        if media_row.created_at
                        else None
                    ),
                }
            )

        popularity = clamp_card_value(model.popularity)
        versatility = clamp_card_value(model.versatility)
        longevity = clamp_card_value(model.longevity)
        industry_impact = clamp_card_value(model.industry_impact)
        fan_appeal = clamp_card_value(model.fan_appeal)
        score = compute_power_score(
            [popularity, versatility, longevity, industry_impact, fan_appeal]
        )
        card = {
            "popularity": popularity,
            "versatility": versatility,
            "longevity": longevity,
            "industry_impact": industry_impact,
            "fan_appeal": fan_appeal,
            "score": score,
            "stars": compute_star_rating(score),
        }
    finally:
        session.close()

    has_prev = page > 1
    has_next = page * per_page < total

    return templates.TemplateResponse(
        "gallery.html",
        {
            "request": request,
            "model_name": model.name,
            "media": media_items,
            "card": card,
            "page": page,
            "has_prev": has_prev,
            "has_next": has_next,
        },
    )


@app.delete("/models/{slug}", dependencies=[Depends(require_admin_token)], status_code=status.HTTP_204_NO_CONTENT)
def delete_model_by_slug(request: Request, slug: str):
    if not is_admin_request(request):
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
            detail="Unauthorized",
        )

    session = SessionLocal()
    try:
        model = _get_model_by_slug(session, slug)
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

        deleted, media_records = model_service.delete_model_by_id(session, model.id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete model",
            )

        storage_service.delete_media_files(media_records)
        storage_service.delete_model_directory(model.name)
    finally:
        session.close()

    return None
