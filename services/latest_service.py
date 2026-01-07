from sqlalchemy import desc

from models.database import SessionLocal
from models.model_entity import Model
from models.media_entity import Media


def get_latest_media(model_name: str | None = None, limit: int = 1) -> list[dict]:
    session = SessionLocal()
    try:
        query = session.query(Media)

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
            }
            for media in media_items
        ]
    finally:
        session.close()
