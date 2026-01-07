from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from models.database import SessionLocal
from models.media_entity import Media
from models.model_entity import Model
from services.media_cleanup_service import _delete_media_file
from services.rating_service import compute_rating_for_path
from web.auth import require_admin_token, get_request_token
from datetime import datetime

router = APIRouter(prefix="/models", dependencies=[Depends(require_admin_token)])
delete_router = APIRouter(prefix="/api/media", dependencies=[Depends(require_admin_token)])
templates = Jinja2Templates(directory="web/templates")

PAGE_SIZE = 12


def media_path_to_url(file_path: str) -> str:
    if not file_path:
        return ""

    path = file_path.replace("\\", "/")

    if "/media/" in path:
        return path[path.index("/media/") :]

    if path.startswith("media/"):
        return "/" + path

    return ""


@router.get("/{model_name}")
def model_gallery(request: Request, model_name: str, page: int = 1):
    session: Session = SessionLocal()
    token = get_request_token(request)
    token_query = f"?token={token}" if token else ""
    page_token_query = f"&token={token}" if token else ""
    try:
        # find model by name
        model_name = model_name.replace("_", " ")
        normalized_name = " ".join(model_name.lower().replace("_", " ").split())
        model = (
            session.query(Model)
            .filter(Model.normalized_name == normalized_name)
            .first()
        )

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        offset = (page - 1) * PAGE_SIZE

        media_items = (
            session.query(Media)
            .filter(Media.model_id == model.id)
            .order_by(Media.created_at.desc())
            .offset(offset)
            .limit(PAGE_SIZE)
            .all()
        )

        media = []
        for m in media_items:
            url = media_path_to_url(m.file_path)
            if not url:
                continue

            media.append(
                {
                    "id": m.id,
                    "url": url,
                    "rating": m.rating,
                    "rating_caption": m.rating_caption,
                    "media_type": m.media_type,
                }
            )

        total = (
            session.query(Media)
            .filter(Media.model_id == model.id)
            .count()
        )

    finally:
        session.close()

    return templates.TemplateResponse(
        "gallery.html",
        {
            "request": request,
            "media": media,
            "model_name": model.name,
            "page": page,
            "has_next": page * PAGE_SIZE < total,
            "has_prev": page > 1,
            "token": token,
            "token_query": token_query,
            "page_token_query": page_token_query,
        },
    )


@delete_router.delete("/{media_id}")
def delete_media(media_id: int):
    session: Session = SessionLocal()
    try:
        media = session.query(Media).filter(Media.id == media_id).first()
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")

        _delete_media_file(media.file_path)
        session.delete(media)
        session.commit()
        return {"status": "deleted"}
    finally:
        session.close()


@delete_router.post("/{media_id}/rating")
async def rate_media(media_id: int, request: Request):
    session: Session = SessionLocal()
    try:
        payload = await request.json()
    except Exception:
        session.close()
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    rating = payload.get("rating")
    caption = payload.get("caption") or ""

    try:
        media = session.query(Media).filter(Media.id == media_id).first()
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")

        if media.rating_caption:
            raise HTTPException(status_code=409, detail="Caption already set")

        if media.rating is None:
            if rating is None:
                rating = compute_rating_for_path(media.file_path)
            if not isinstance(rating, int) or rating < 1 or rating > 100:
                raise HTTPException(status_code=400, detail="Rating must be 1-100")
            media.rating = rating

        media.rating_caption = caption.strip()[:280]
        media.rated_at = datetime.utcnow()
        session.commit()
        return {"status": "rated"}
    finally:
        session.close()
