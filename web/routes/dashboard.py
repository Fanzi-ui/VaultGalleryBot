from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from models.database import SessionLocal
from models.model_entity import Model
from models.media_entity import Media

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")


@router.get("/")
def dashboard(request: Request):
    session = SessionLocal()
    try:
        model_count = session.query(Model).count()
        media_count = session.query(Media).count()
    finally:
        session.close()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "model_count": model_count,
            "media_count": media_count,
        },
    )
