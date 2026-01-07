from pathlib import Path
from datetime import datetime
import config
from models.database import SessionLocal
from models.model_entity import Model
from models.media_entity import Media
import logging
import time
from services.rating_service import compute_rating_for_path


def normalize_model_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def _normalize_model_key(value: str) -> str:
    return " ".join(value.lower().replace("_", " ").split())


async def save_media(update, context, model_name: str) -> str:
    """
    Save media to disk AND record it in the database.
    Supports bulk (album) uploads safely.
    """

    message = update.message
    model_slug = normalize_model_name(model_name)

    # --- FILESYSTEM ---
    model_dir = Path(config.MEDIA_ROOT) / model_slug
    model_dir.mkdir(parents=True, exist_ok=True)

    if message.photo:
        media_obj = message.photo[-1]
        media_type = "image"
        extension = ".jpg"
        unique_id = media_obj.file_unique_id

    elif message.video:
        media_obj = message.video
        media_type = "video"
        extension = ".mp4"
        unique_id = media_obj.file_unique_id

    else:
        raise ValueError("Unsupported media type")

    # UNIQUE filename (prevents overwrite in albums)
    filename = f"{unique_id}{extension}"
    file_path = model_dir / filename

    tg_file = await context.bot.get_file(media_obj.file_id)
    await tg_file.download_to_drive(custom_path=str(file_path))

    _save_media_record(model_name, str(file_path), media_type)

    return str(file_path)


async def save_media_file(context, model_name: str, file_id: str, unique_id: str, media_type: str) -> str:
    """
    Save media from Telegram file_id to disk and record it in the database.
    """
    model_slug = normalize_model_name(model_name)
    model_dir = Path(config.MEDIA_ROOT) / model_slug
    model_dir.mkdir(parents=True, exist_ok=True)

    if media_type == "image":
        extension = ".jpg"
    elif media_type == "video":
        extension = ".mp4"
    else:
        raise ValueError("Unsupported media type")

    filename = f"{unique_id}{extension}"
    file_path = model_dir / filename

    tg_file = await context.bot.get_file(file_id)
    await tg_file.download_to_drive(custom_path=str(file_path))

    _save_media_record(model_name, str(file_path), media_type)

    return str(file_path)


def _save_media_record(model_name: str, file_path: str, media_type: str) -> None:
    session = SessionLocal()
    try:
        normalized_name = _normalize_model_key(model_name)
        model = (
            session.query(Model)
            .filter(Model.normalized_name == normalized_name)
            .first()
        )
        if not model:
            for candidate in session.query(Model).all():
                if _normalize_model_key(candidate.name) == normalized_name:
                    model = candidate
                    if candidate.normalized_name != normalized_name:
                        candidate.normalized_name = normalized_name
                        session.flush()
                    break
        if not model:
            cleaned_name = " ".join(model_name.split())
            model = Model(
                name=cleaned_name,
                normalized_name=normalized_name,
            )
            session.add(model)
            session.flush()

        existing_media = (
            session.query(Media)
            .filter(Media.file_path == str(file_path))
            .first()
        )
        if existing_media:
            logging.getLogger(__name__).info(
                "Media already exists for %s; skipping duplicate row.",
                file_path,
            )
            return

        rating = None
        if media_type == "image":
            for _ in range(3):
                rating = compute_rating_for_path(str(file_path))
                if rating is not None:
                    break
                time.sleep(0.2)

            if rating is None:
                logging.getLogger(__name__).warning(
                    "Rating missing for %s",
                    file_path,
                )

        media = Media(
            model_id=model.id,
            file_path=str(file_path),
            media_type=media_type,
            rating=rating,
        )
        session.add(media)
        session.commit()

        if media_type == "image" and rating is None:
            for _ in range(5):
                rating = compute_rating_for_path(str(file_path))
                if rating is not None:
                    media.rating = rating
                    media.rated_at = datetime.utcnow()
                    session.commit()
                    break
                time.sleep(0.4)

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
