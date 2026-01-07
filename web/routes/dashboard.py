from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import random

from models.database import SessionLocal
from models.model_entity import Model
from models.media_entity import Media
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


def _collect_slideshow_media(session, media_types: list[str]) -> list[dict]:
    rows = (
        session.query(Media, Model)
        .join(Model, Media.model_id == Model.id)
        .filter(Media.media_type.in_(media_types))
        .all()
    )

    by_model: dict[str, list[dict]] = {}

    for media, model in rows:
        if not media.file_path:
            continue

        url = media_path_to_url(media.file_path)
        if not url:
            continue

        by_model.setdefault(model.name, []).append(
            {
                "id": media.id,
                "url": url,
                "model_name": model.name,
                "rating": media.rating,
                "rating_caption": media.rating_caption,
                "media_type": media.media_type,
            }
        )

    selection: list[dict] = []

    for model_name, items in by_model.items():
        selection.append(random.choice(items))

    for items in by_model.values():
        for item in items:
            if item not in selection:
                selection.append(item)

    random.shuffle(selection)
    return selection


@router.get("/")
def dashboard(request: Request):
    if not is_admin_request(request):
        return RedirectResponse(url="/login", status_code=303)

    session = SessionLocal()
    token = get_request_token(request)
    token_query = f"?token={token}" if token else ""

    try:
        model_count = session.query(Model).count()
        media_count = session.query(Media).count()

        # JOIN media -> model
        slideshow_images = _collect_slideshow_media(session, ["image"])

    finally:
        session.close()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "model_count": model_count,
            "media_count": media_count,
            "slideshow_images": slideshow_images,
            "token": token,
            "token_query": token_query,
        },
    )


@router.get("/slideshow")
def slideshow(request: Request):
    if not is_admin_request(request):
        return RedirectResponse(url="/login", status_code=303)

    session = SessionLocal()
    token = get_request_token(request)
    token_query = f"?token={token}" if token else ""

    try:
        models = [model.name for model in session.query(Model).order_by(Model.name).all()]
        slideshow_media = _collect_slideshow_media(session, ["image", "video"])
    finally:
        session.close()

    return templates.TemplateResponse(
        "slideshow.html",
        {
            "request": request,
            "models": models,
            "slideshow_media": slideshow_media,
            "token": token,
            "token_query": token_query,
            "hide_nav": True,
        },
    )
