from datetime import datetime
import logging
from pathlib import Path

try:
    from PIL import Image
except Exception:
    Image = None

from sqlalchemy import inspect

from models.database import SessionLocal, engine
from models import model_entity  # ensure model metadata is loaded
from models.media_entity import Media


def compute_rating_from_size(width: int, height: int) -> int:
    max_side = max(width, height)
    min_side = min(width, height)

    if max_side >= 3840 and min_side >= 2160:
        return 99  # 4K
    if max_side >= 2560 and min_side >= 1440:
        return 93  # QHD
    if max_side >= 1920 and min_side >= 1080:
        return 88  # HD
    if max_side >= 1280 and min_side >= 720:
        return 78  # 720p

    mp = (width * height) / 1000000
    scaled = min(mp, 2) / 2
    return min(76, max(60, round(60 + scaled * 16)))


def compute_rating_for_path(file_path: str) -> int | None:
    if Image is None:
        return None

    path = Path(file_path)
    if not path.exists():
        return None

    try:
        with Image.open(path) as img:
            width, height = img.size
            return compute_rating_from_size(width, height)
    except Exception as exc:
        logging.getLogger(__name__).warning(
            "Failed to read image for rating: %s (%s)",
            file_path,
            exc,
        )
        return None


def backfill_missing_ratings() -> None:
    try:
        inspector = inspect(engine)
        if "media" not in inspector.get_table_names():
            return
    except Exception:
        return

    session = SessionLocal()
    try:
        media_items = (
            session.query(Media)
            .filter(Media.media_type == "image")
            .filter(Media.rating.is_(None))
            .all()
        )

        for media in media_items:
            rating = compute_rating_for_path(media.file_path)
            if rating is None:
                continue
            media.rating = rating
            if not media.rated_at:
                media.rated_at = datetime.utcnow()

        session.commit()
    finally:
        session.close()
