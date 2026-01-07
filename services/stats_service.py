from sqlalchemy import func

from models.database import SessionLocal
from models.model_entity import Model
from models.media_entity import Media


def get_overall_stats() -> dict:
    session = SessionLocal()
    try:
        total_models = session.query(func.count(Model.id)).scalar() or 0
        total_media = session.query(func.count(Media.id)).scalar() or 0
        total_images = (
            session.query(func.count(Media.id))
            .filter(Media.media_type == "image")
            .scalar()
            or 0
        )
        total_videos = (
            session.query(func.count(Media.id))
            .filter(Media.media_type == "video")
            .scalar()
            or 0
        )
        rated_images = (
            session.query(func.count(Media.id))
            .filter(Media.media_type == "image")
            .filter(Media.rating.is_not(None))
            .scalar()
            or 0
        )
        avg_rating = (
            session.query(func.avg(Media.rating))
            .filter(Media.rating.is_not(None))
            .scalar()
        )

        return {
            "total_models": total_models,
            "total_media": total_media,
            "total_images": total_images,
            "total_videos": total_videos,
            "rated_images": rated_images,
            "avg_rating": avg_rating,
        }
    finally:
        session.close()


def get_model_stats(model_name: str) -> dict | None:
    session = SessionLocal()
    try:
        model = session.query(Model).filter_by(name=model_name).first()
        if not model:
            return None

        total_media = (
            session.query(func.count(Media.id))
            .filter(Media.model_id == model.id)
            .scalar()
            or 0
        )
        total_images = (
            session.query(func.count(Media.id))
            .filter(Media.model_id == model.id)
            .filter(Media.media_type == "image")
            .scalar()
            or 0
        )
        total_videos = (
            session.query(func.count(Media.id))
            .filter(Media.model_id == model.id)
            .filter(Media.media_type == "video")
            .scalar()
            or 0
        )
        rated_images = (
            session.query(func.count(Media.id))
            .filter(Media.model_id == model.id)
            .filter(Media.media_type == "image")
            .filter(Media.rating.is_not(None))
            .scalar()
            or 0
        )
        avg_rating = (
            session.query(func.avg(Media.rating))
            .filter(Media.model_id == model.id)
            .filter(Media.rating.is_not(None))
            .scalar()
        )
        last_upload = (
            session.query(func.max(Media.created_at))
            .filter(Media.model_id == model.id)
            .scalar()
        )

        return {
            "model_name": model.name,
            "total_media": total_media,
            "total_images": total_images,
            "total_videos": total_videos,
            "rated_images": rated_images,
            "avg_rating": avg_rating,
            "last_upload": last_upload,
        }
    finally:
        session.close()
