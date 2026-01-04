from math import ceil

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from models.database import SessionLocal
from models.model_entity import Model
from models.media_entity import Media

router = APIRouter(prefix="/models")
templates = Jinja2Templates(directory="web/templates")

PAGE_SIZE = 12


def media_path_to_url(file_path: str) -> str:
    file_path = file_path.replace("\\", "/")
    return file_path[file_path.index("/media/") :]


@router.get("/{model_slug}")
def model_gallery(request: Request, model_slug: str, page: int = 1):
    session = SessionLocal()

    try:
        model_name = model_slug.replace("_", " ")

        model = (
            session.query(Model)
            .filter(Model.name.ilike(model_name))
            .first()
        )

        if not model:
            return templates.TemplateResponse(
                "gallery.html",
                {
                    "request": request,
                    "model_name": model_slug,
                    "media": [],
                    "page": page,
                    "total_pages": 1,
                },
            )

        total_items = (
            session.query(Media)
            .filter(Media.model_id == model.id)
            .count()
        )

        total_pages = max(1, ceil(total_items / PAGE_SIZE))
        page = max(1, min(page, total_pages))

        media_items = (
            session.query(Media)
            .filter(Media.model_id == model.id)
            .order_by(Media.created_at.desc())
            .offset((page - 1) * PAGE_SIZE)
            .limit(PAGE_SIZE)
            .all()
        )

        media_data = [
            {
                "url": media_path_to_url(m.file_path),
                "type": m.media_type,
            }
            for m in media_items
        ]

    finally:
        session.close()

    return templates.TemplateResponse(
        "gallery.html",
        {
            "request": request,
            "model_name": model.name,
            "media": media_data,
            "page": page,
            "total_pages": total_pages,
        },
    )
