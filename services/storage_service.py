import os
from pathlib import Path
from datetime import datetime

import config


def normalize_model_name(name: str) -> str:
    """
    Convert 'Bella Hadid' -> 'bella_hadid'
    """
    return name.strip().lower().replace(" ", "_")


async def save_media(update, context, model_name: str) -> str:
    """
    Downloads a photo or video from Telegram and saves it to disk.
    Returns the saved file path.
    """

    message = update.message

    # Normalize model name
    model_slug = normalize_model_name(model_name)

    # Create model directory
    model_dir = Path(config.MEDIA_ROOT) / model_slug
    model_dir.mkdir(parents=True, exist_ok=True)

    # Determine media type and file object
    if message.photo:
        media = message.photo[-1]  # highest resolution
        extension = ".jpg"
    elif message.video:
        media = message.video
        extension = ".mp4"
    else:
        raise ValueError("Unsupported media type")

    # Generate filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}{extension}"
    file_path = model_dir / filename

    # Download file from Telegram
    tg_file = await context.bot.get_file(media.file_id)
    await tg_file.download_to_drive(custom_path=str(file_path))

    return str(file_path)
