from pathlib import Path


async def send_text(bot, chat_id, text):
    await bot.send_message(chat_id=chat_id, text=text)


async def send_media(bot, chat_id, file_path: str, media_type: str):
    path = Path(file_path)

    if not path.exists():
        await bot.send_message(
            chat_id=chat_id,
            text="❌ Media file not found on server."
        )
        return

    if media_type == "image":
        with open(path, "rb") as f:
            await bot.send_photo(chat_id=chat_id, photo=f)

    elif media_type == "video":
        with open(path, "rb") as f:
            await bot.send_video(chat_id=chat_id, video=f)

    else:
        await bot.send_message(
            chat_id=chat_id,
            text="❌ Unsupported media type."
        )
