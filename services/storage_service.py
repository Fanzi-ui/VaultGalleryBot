from pathlib import Path
from datetime import datetime

import config
from models.database import SessionLocal
from models.model_entity import Model
from models.media_entity import Media


def normalize_model_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


async def save_media(update, context, model_name: str) -> str:
    """
    Save media to disk AND record it in the database.
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
    elif message.video:
        media_obj = message.video
        media_type = "video"
        extension = ".mp4"
    else:
        raise ValueError("Unsupported media type")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}{extension}"
    file_path = model_dir / filename

    tg_file = await context.bot.get_file(media_obj.file_id)
    await tg_file.download_to_drive(custom_path=str(file_path))

    # --- DATABASE ---
    session = SessionLocal()
    try:
        # Get or create model
        model = session.query(Model).filter_by(name=model_name).first()
        if not model:
            model = Model(name=model_name)
            session.add(model)
            session.flush()  # get model.id

        # Create media record
        media = Media(
            model_id=model.id,
            file_path=str(file_path),
            media_type=media_type,
        )
        session.add(media)
        session.commit()

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return str(file_path)
