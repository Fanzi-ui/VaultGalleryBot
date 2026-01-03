from models.database import SessionLocal
from models.model_entity import Model
from models.media_entity import Media
from sqlalchemy import func


def get_models_with_counts():
    """
    Returns a list of (model_name, media_count)
    """
    session = SessionLocal()
    try:
        results = (
            session.query(
                Model.name,
                func.count(Media.id)
            )
            .join(Media, Media.model_id == Model.id)
            .group_by(Model.id)
            .order_by(Model.name.asc())
            .all()
        )
        return results
    finally:
        session.close()
