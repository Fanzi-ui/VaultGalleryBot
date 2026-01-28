from pathlib import Path
import config
from models.media_entity import Media
import logging
import shutil
import aiofiles
from sqlalchemy.orm import Session
from services import model_service # Import model_service to use its create_media_record

logger = logging.getLogger(__name__)

def normalize_model_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")

async def save_uploaded_media(db: Session, model_id: int, file: bytes, filename: str, media_type: str) -> Media:
    model = model_service.get_model_by_id_with_session(db, model_id)
    if not model:
        raise ValueError(f"Model with ID {model_id} not found.")
    
    model_slug = normalize_model_name(model.name)
    model_dir = Path(config.MEDIA_ROOT) / model_slug
    model_dir.mkdir(parents=True, exist_ok=True)

    file_path = model_dir / filename

    async with aiofiles.open(file_path, 'wb') as out_file:
        await out_file.write(file)
    
    # Create media record in the database
    media_record = model_service.create_media_record(db, model_id, str(file_path), media_type)
    return media_record

def delete_media_files(media_records: list[Media]) -> None:
    for media in media_records:
        file_path = Path(media.file_path)
        if file_path.exists():
            try:
                file_path.unlink()  # Delete the file
                logger.info(f"Deleted media file: {file_path}")
            except OSError as e:
                logger.error(f"Error deleting file {file_path}: {e}")
        else:
            logger.warning(f"Media file not found, skipping: {file_path}")


def delete_model_directory(model_name: str) -> None:
    model_slug = normalize_model_name(model_name)
    model_dir = Path(config.MEDIA_ROOT) / model_slug
    if model_dir.exists() and model_dir.is_dir():
        try:
            shutil.rmtree(model_dir)  # Delete the directory and all its contents
            logger.info(f"Deleted model directory: {model_dir}")
        except OSError as e:
            logger.error(f"Error deleting directory {model_dir}: {e}")
    else:
        logger.warning(f"Model directory not found, skipping: {model_dir}")
