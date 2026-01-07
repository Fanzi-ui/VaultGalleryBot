from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, desc

from models.database import SessionLocal
from models.media_entity import Media
from models.model_entity import Model
from web.auth import get_request_token, is_admin_request

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")


def media_path_to_url(file_path: str) -> str:
    if not file_path:
        return ""

    path = file_path.replace("\\", "/")

    if "/media/" in path:
        return path[path.index("/media/") :]

    if path.startswith("media/"):
        return "/" + path

    return ""


def build_media_rows(rows):
    items = []
    for media, model in rows:
        if not media.file_path:
            continue
        url = media_path_to_url(media.file_path)
        if not url:
            continue
        items.append(
            {
                "id": media.id,
                "url": url,
                "model_name": model.name,
                "rating": media.rating,
                "rating_caption": media.rating_caption,
                "media_type": media.media_type,
            }
        )
    return items


@router.get("/ratings")
def ratings_review(request: Request):
    if not is_admin_request(request):
        return RedirectResponse(url="/login", status_code=303)

    session = SessionLocal()
    token = get_request_token(request)
    token_query = f"?token={token}" if token else ""

    try:
        rows = (
            session.query(Media, Model)
            .join(Model, Media.model_id == Model.id)
            .filter(Media.media_type == "image")
            .filter(Media.rating_caption.is_(None))
            .order_by(desc(Media.created_at))
            .limit(120)
            .all()
        )
        items = build_media_rows(rows)
    finally:
        session.close()

    return templates.TemplateResponse(
        "ratings.html",
        {
            "request": request,
            "items": items,
            "token": token,
            "token_query": token_query,
        },
    )


@router.get("/top")
def top_picks(request: Request, page: int = 1):
    if not is_admin_request(request):
        return RedirectResponse(url="/login", status_code=303)

    session = SessionLocal()
    token = get_request_token(request)
    token_query = f"?token={token}" if token else ""
    per_page = 48
    page = max(1, page)

    try:
        base_query = (
            session.query(Media, Model)
            .join(Model, Media.model_id == Model.id)
            .filter(Media.media_type == "image")
            .filter(Media.rating.is_not(None))
        )
        total = base_query.count()
        rows = (
            base_query
            .order_by(desc(Media.rating), desc(Media.created_at))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        items = build_media_rows(rows)
    finally:
        session.close()

    has_prev = page > 1
    has_next = page * per_page < total
    page_token_query = f"&token={token}" if token else ""

    return templates.TemplateResponse(
        "top.html",
        {
            "request": request,
            "media": items,
            "page": page,
            "has_prev": has_prev,
            "has_next": has_next,
            "page_token_query": page_token_query,
            "token": token,
            "token_query": token_query,
        },
    )


@router.get("/recent")
def recent_media(request: Request, page: int = 1):
    if not is_admin_request(request):
        return RedirectResponse(url="/login", status_code=303)

    session = SessionLocal()
    token = get_request_token(request)
    token_query = f"?token={token}" if token else ""
    per_page = 48
    page = max(1, page)

    try:
        base_query = (
            session.query(Media, Model)
            .join(Model, Media.model_id == Model.id)
        )
        total = base_query.count()
        rows = (
            base_query
            .order_by(desc(Media.created_at))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        items = build_media_rows(rows)
    finally:
        session.close()

    has_prev = page > 1
    has_next = page * per_page < total
    page_token_query = f"&token={token}" if token else ""

    return templates.TemplateResponse(
        "recent.html",
        {
            "request": request,
            "media": items,
            "page": page,
            "has_prev": has_prev,
            "has_next": has_next,
            "page_token_query": page_token_query,
            "token": token,
            "token_query": token_query,
        },
    )


@router.get("/insights")
def model_insights(request: Request):
    if not is_admin_request(request):
        return RedirectResponse(url="/login", status_code=303)

    session = SessionLocal()
    token = get_request_token(request)
    token_query = f"?token={token}" if token else ""

    try:
        models = session.query(Model).order_by(Model.name).all()
        insights = []
        for model in models:
            total_media = (
                session.query(func.count(Media.id))
                .filter(Media.model_id == model.id)
                .scalar()
                or 0
            )
            image_count = (
                session.query(func.count(Media.id))
                .filter(Media.model_id == model.id)
                .filter(Media.media_type == "image")
                .scalar()
                or 0
            )
            video_count = (
                session.query(func.count(Media.id))
                .filter(Media.model_id == model.id)
                .filter(Media.media_type == "video")
                .scalar()
                or 0
            )
            rated_images = (
                session.query(func.count(Media.id))
                .filter(Media.model_id == model.id)
                .filter(Media.media_type == "image")
                .filter(Media.rating.is_not(None))
                .scalar()
                or 0
            )
            avg_rating = (
                session.query(func.avg(Media.rating))
                .filter(Media.model_id == model.id)
                .filter(Media.rating.is_not(None))
                .scalar()
            )
            last_upload = (
                session.query(func.max(Media.created_at))
                .filter(Media.model_id == model.id)
                .scalar()
            )
            rating_90 = (
                session.query(func.count(Media.id))
                .filter(Media.model_id == model.id)
                .filter(Media.rating >= 90)
                .scalar()
                or 0
            )
            rating_80 = (
                session.query(func.count(Media.id))
                .filter(Media.model_id == model.id)
                .filter(Media.rating >= 80)
                .filter(Media.rating < 90)
                .scalar()
                or 0
            )
            rating_low = (
                session.query(func.count(Media.id))
                .filter(Media.model_id == model.id)
                .filter(Media.rating < 80)
                .scalar()
                or 0
            )
            unrated = image_count - rated_images

            insights.append(
                {
                    "name": model.name,
                    "total_media": total_media,
                    "image_count": image_count,
                    "video_count": video_count,
                    "rated_images": rated_images,
                    "unrated_images": max(unrated, 0),
                    "avg_rating": avg_rating,
                    "last_upload": last_upload,
                    "rating_90": rating_90,
                    "rating_80": rating_80,
                    "rating_low": rating_low,
                }
            )
    finally:
        session.close()

    return templates.TemplateResponse(
        "insights.html",
        {
            "request": request,
            "insights": insights,
            "token_query": token_query,
        },
    )


@router.get("/collections")
def collections(request: Request):
    if not is_admin_request(request):
        return RedirectResponse(url="/login", status_code=303)

    session = SessionLocal()
    token = get_request_token(request)
    token_query = f"?token={token}" if token else ""

    try:
        models = [model.name for model in session.query(Model).order_by(Model.name).all()]
    finally:
        session.close()

    return templates.TemplateResponse(
        "collections.html",
        {
            "request": request,
            "models": models,
            "token": token,
            "token_query": token_query,
        },
    )
