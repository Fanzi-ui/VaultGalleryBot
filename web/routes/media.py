from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from models.database import SessionLocal
from models.media_entity import Media
from models.model_entity import Model

router = APIRouter(prefix="/models")
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
    try:
        # find model by name
        model = (
            session.query(Model)
            .filter(Model.name.ilike(model_name))
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
        },
    )
