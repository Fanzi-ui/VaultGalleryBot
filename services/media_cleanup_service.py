from pathlib import Path
from sqlalchemy.sql import func

from models.database import SessionLocal
from models.model_entity import Model
from models.media_entity import Media


def delete_random_media_for_model(model_name: str, count: int = 1) -> int:
    """
    Deletes `count` random media items for a given model.
    Returns the number of deleted media items.
    Model record is preserved.
    """

    session = SessionLocal()
    deleted = 0

    try:
        model = session.query(Model).filter_by(name=model_name).first()
        if not model:
            return 0

        media_items = (
            session.query(Media)
            .filter(Media.model_id == model.id)
            .order_by(func.random())
            .limit(count)
            .all()
        )

        for media in media_items:
            _delete_media_file(media.file_path)
            session.delete(media)
            deleted += 1

        session.commit()
        return deleted

    finally:
        session.close()


def delete_all_media() -> int:
    """
    Deletes ALL media records and files.
    Preserves all models.
    Returns number of deleted media items.
    """

    session = SessionLocal()
    deleted = 0

    try:
        media_items = session.query(Media).all()

        for media in media_items:
            _delete_media_file(media.file_path)
            session.delete(media)
            deleted += 1

        session.commit()
        return deleted

    finally:
        session.close()


def _delete_media_file(file_path: str):
    """
    Safely deletes a media file from disk.
    Does not raise if file is missing.
    """

    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
    except Exception:
        # Fail silently to avoid breaking DB cleanup
        pass
