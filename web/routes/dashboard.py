from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
import random

from models.database import SessionLocal
from models.model_entity import Model
from models.media_entity import Media
from web.auth import require_admin_token, get_request_token

router = APIRouter(dependencies=[Depends(require_admin_token)])
templates = Jinja2Templates(directory="web/templates")


def media_path_to_url(file_path: str) -> str:
    file_path = file_path.replace("\\", "/")
    return file_path[file_path.index("/media/") :]


@router.get("/")
def dashboard(request: Request):
    session = SessionLocal()
    token = get_request_token(request)
    token_query = f"?token={token}" if token else ""

    try:
        model_count = session.query(Model).count()
        media_count = session.query(Media).count()

        # JOIN media -> model
        rows = (
            session.query(Media, Model)
            .join(Model, Media.model_id == Model.id)
            .filter(Media.media_type == "image")
            .all()
        )

        by_model = {}

        for media, model in rows:
            if not media.file_path:
                continue

            by_model.setdefault(model.name, []).append(
                media_path_to_url(media.file_path)
            )

        # ---- FAIR SELECTION ----
        slideshow_images = []

        # 1️⃣ One image per model (guaranteed)
        for model_name, images in by_model.items():
            slideshow_images.append(random.choice(images))

        # 2️⃣ Remaining images
        for images in by_model.values():
            for img in images:
                if img not in slideshow_images:
                    slideshow_images.append(img)

        # 3️⃣ Shuffle remaining only
        first_pass = slideshow_images[:len(by_model)]
        rest = slideshow_images[len(by_model):]
        random.shuffle(rest)

        slideshow_images = first_pass + rest

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
