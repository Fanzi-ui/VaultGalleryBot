from sqlalchemy.sql import func

from models.database import SessionLocal
from models.model_entity import Model
from models.media_entity import Media


def get_random_media(model_name: str | None = None):
    """
    Returns a random Media record.
    If model_name is provided, limits selection to that model.
    Returns None if no media is found.
    """

    session = SessionLocal()
    try:
        query = session.query(Media)

        if model_name:
            model = session.query(Model).filter_by(name=model_name).first()
            if not model:
                return None

            query = query.filter(Media.model_id == model.id)

        media = query.order_by(func.random()).first()
        return media

    finally:
        session.close()
