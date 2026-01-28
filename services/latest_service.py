from sqlalchemy import desc

from models.database import SessionLocal
from models.model_entity import Model
from models.media_entity import Media


def get_latest_media(
    model_name: str | None = None,
    limit: int = 1,
    count: int | None = None,
) -> list[dict]:
    session = SessionLocal()
    try:
        if count is not None:
            limit = count

        query = session.query(Media, Model).join(Model, Media.model_id == Model.id)

        if model_name:
            model = session.query(Model).filter_by(name=model_name).first()
            if not model:
                return []
            query = query.filter(Media.model_id == model.id)

        media_items = (
            query
            .order_by(desc(Media.created_at))
            .limit(limit)
            .all()
        )

        return [
            {
                "file_path": media.file_path,
                "media_type": media.media_type,
                "model_name": model.name,
            }
            for media, model in media_items
        ]
    finally:
        session.close()
