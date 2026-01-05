from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates

from pathlib import Path

from models.database import SessionLocal
from models.model_entity import Model
from models.media_entity import Media
from web.auth import require_admin_token, get_request_token

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

            slug = normalize_model_name(model.name)

            # find preview image (safe, filesystem only)
            preview_file = None
            model_dir = MEDIA_ROOT / slug
            if model_dir.exists() and model_dir.is_dir():
                images = sorted(
                    f.name
                    for f in model_dir.iterdir()
                    if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
                )
                if images:
                    preview_file = images[0]

            models_data.append(
                {
                    "name": model.name,
                    "slug": slug,
                    "media_count": count,
                    "preview_file": preview_file,
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

        model = (
            session.query(Model)
            .filter(Model.name.ilike(model_name))
            .first()
        )

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # delete related media rows
        session.query(Media).filter(Media.model_id == model.id).delete()

        # delete model row
        session.delete(model)
        session.commit()

        return {"status": "deleted"}
    finally:
        session.close()
