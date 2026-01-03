import config
from views.message_view import send_text
from services.storage_service import save_media


async def upload_command(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Permission check
    if user_id not in config.AUTHORIZED_USERS:
        await send_text(
            context.bot,
            chat_id,
            "❌ You are not authorized to upload media."
        )
        return

    message = update.message

    # Check media
    if not message.photo and not message.video:
        await send_text(
            context.bot,
            chat_id,
            "❌ Please send a photo or video with /upload <model name>."
        )
        return

    # Check caption
    if not message.caption:
        await send_text(
            context.bot,
            chat_id,
            "❌ Missing caption. Use: /upload <model name>"
        )
        return

    # Parse model name
    parts = message.caption.split(maxsplit=1)
    if len(parts) < 2:
        await send_text(
            context.bot,
            chat_id,
            "❌ Missing model name. Use: /upload <model name>"
        )
        return

    model_name = parts[1].strip()

    # Save media
    try:
        file_path = await save_media(update, context, model_name)
    except Exception as e:
        await send_text(
            context.bot,
            chat_id,
            f"❌ Failed to save media: {e}"
        )
        return

    # Success
    await send_text(
        context.bot,
        chat_id,
        f"✅ Media saved successfully under {model_name}"
    )
