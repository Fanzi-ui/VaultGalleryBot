from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from models.database import SessionLocal
from models.media_entity import Media
from models.model_entity import Model
from web.auth import require_admin_token, get_request_token

router = APIRouter(prefix="/models", dependencies=[Depends(require_admin_token)])
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
            "token": token,
            "token_query": token_query,
            "page_token_query": page_token_query,
        },
    )
