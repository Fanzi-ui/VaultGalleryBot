from datetime import datetime
from sqlalchemy import asc
from sqlalchemy.sql import func

from models.database import SessionLocal
from models.model_entity import Model
from models.media_entity import Media


def get_random_media(model_name: str | None = None):
    """
    Returns a dict with media data using DB-centered fairness.
    """

    session = SessionLocal()
    try:
        query = session.query(Media)

        if model_name:
            model = session.query(Model).filter_by(name=model_name).first()
            if not model:
                return None
            query = query.filter(Media.model_id == model.id)

        media = (
            query
            .order_by(
                Media.last_sent_at.is_(None).desc(),
                asc(Media.last_sent_at),
                func.random()
            )
            .first()
        )

        if not media:
            return None

        # Capture required data BEFORE session closes
        result = {
            "file_path": media.file_path,
            "media_type": media.media_type,
        }

        media.last_sent_at = datetime.utcnow()
        session.commit()

        return result

    finally:
        session.close()
