import config
from views.message_view import send_text, send_media
from services.random_service import get_random_media


async def random_command(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Permission check
    if user_id not in config.AUTHORIZED_USERS:
        await send_text(
            context.bot,
            chat_id,
            "❌ You are not authorized to use this command."
        )
        return

    # Parse optional model name
    args = context.args
    model_name = " ".join(args).strip() if args else None

    media = get_random_media(model_name)

    if not media:
        if model_name:
            await send_text(
                context.bot,
                chat_id,
                f"❌ No media found for model: {model_name}"
            )
        else:
            await send_text(
                context.bot,
                chat_id,
                "❌ No media found in the gallery."
            )
        return

    # Send the actual media
    await send_media(
        context.bot,
        chat_id,
        media.file_path,
        media.media_type
    )
