from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from models.database import SessionLocal
from models.model_entity import Model
from models.media_entity import Media

router = APIRouter(prefix="/models")
templates = Jinja2Templates(directory="web/templates")


def normalize_model_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


@router.get("")
def list_models(request: Request):
    session = SessionLocal()
    try:
        models_data = []

        models = session.query(Model).all()
        for model in models:
            count = (
                session.query(Media)
                .filter(Media.model_id == model.id)
                .count()
            )

            models_data.append(
                {
                    "name": model.name,                     # display name
                    "slug": normalize_model_name(model.name),  # URL-safe name
                    "media_count": count,
                }
            )
    finally:
        session.close()

    return templates.TemplateResponse(
        "models.html",
        {
            "request": request,
            "models": models_data,
        },
    )
