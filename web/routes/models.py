from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates

from pathlib import Path

from models.database import SessionLocal
from models.model_entity import Model
from models.media_entity import Media
from services.media_cleanup_service import _delete_media_file
from web.auth import require_admin_token, get_request_token
from sqlalchemy import func

router = APIRouter(prefix="/models", dependencies=[Depends(require_admin_token)])
templates = Jinja2Templates(directory="web/templates")

MEDIA_ROOT = Path("media/models")


def normalize_model_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


@router.get("")
def list_models(request: Request):
    session = SessionLocal()
    token = get_request_token(request)
    token_query = f"?token={token}" if token else ""
    try:
        models_data = []

        models = session.query(Model).all()
        for model in models:
            count = (
                session.query(Media)
                .filter(Media.model_id == model.id)
                .count()
            )
            image_count = (
                session.query(Media)
                .filter(Media.model_id == model.id)
                .filter(Media.media_type == "image")
                .count()
            )
            video_count = (
                session.query(Media)
                .filter(Media.model_id == model.id)
                .filter(Media.media_type == "video")
                .count()
            )
            last_upload = (
                session.query(func.max(Media.created_at))
                .filter(Media.model_id == model.id)
                .scalar()
            )

            slug = normalize_model_name(model.name)

            # find preview image/video (safe, filesystem only)
            preview_file = None
            preview_type = None
            model_dir = MEDIA_ROOT / slug
            if model_dir.exists() and model_dir.is_dir():
                images = sorted(
                    f.name
                    for f in model_dir.iterdir()
                    if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
                )
                if images:
                    preview_file = images[0]
                    preview_type = "image"
                else:
                    videos = sorted(
                        f.name
                        for f in model_dir.iterdir()
                        if f.suffix.lower() in (".mp4", ".mov", ".webm")
                    )
                    if videos:
                        preview_file = videos[0]
                        preview_type = "video"

            models_data.append(
                {
                    "name": model.name,
                    "slug": slug,
                    "media_count": count,
                    "image_count": image_count,
                    "video_count": video_count,
                    "last_upload": last_upload,
                    "preview_file": preview_file,
                    "preview_type": preview_type,
                }
            )
    finally:
        session.close()

    return templates.TemplateResponse(
        "models.html",
        {
            "request": request,
            "models": models_data,
            "token": token,
            "token_query": token_query,
        },
    )


@router.delete("/{slug}")
def delete_model(slug: str):
    session = SessionLocal()
    try:
        # match model name from slug
        model_name = slug.replace("_", " ")
        normalized_name = " ".join(model_name.lower().replace("_", " ").split())

        model = (
            session.query(Model)
            .filter(Model.normalized_name == normalized_name)
            .first()
        )

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # delete related media rows and files
        media_items = (
            session.query(Media)
            .filter(Media.model_id == model.id)
            .all()
        )
        for media in media_items:
            _delete_media_file(media.file_path)
            session.delete(media)

        # delete model row
        session.delete(model)
        session.commit()

        return {"status": "deleted"}
    finally:
        session.close()
