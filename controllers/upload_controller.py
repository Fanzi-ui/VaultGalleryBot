import config
from views.message_view import send_text
from services.storage_service import save_media


async def upload_command(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message = update.message

    # Permission check
    if user_id not in config.AUTHORIZED_USERS:
        await send_text(
            context.bot,
            chat_id,
            "❌ You are not authorized to upload media."
        )
        return

    # Must be photo or video
    if not message.photo and not message.video:
        return

    media_group_id = message.media_group_id

    # Initialize album counter store
    if "album_counts" not in context.chat_data:
        context.chat_data["album_counts"] = {}

    # --- Resolve model name ---
    model_name = None

    # If caption exists, extract model name and remember it
    if message.caption:
        parts = message.caption.split(maxsplit=1)
        if len(parts) < 2:
            await send_text(
                context.bot,
                chat_id,
                "❌ Missing model name. Use: /upload <model name>"
            )
            return

        model_name = parts[1].strip()

        # Store model name for album uploads
        if media_group_id:
            context.chat_data[media_group_id] = model_name

    # No caption → album continuation
    elif media_group_id and media_group_id in context.chat_data:
        model_name = context.chat_data[media_group_id]

    else:
        await send_text(
            context.bot,
            chat_id,
            "❌ Missing caption. Use: /upload <model name>"
        )
        return

    # --- Save media ---
    try:
        await save_media(update, context, model_name)
    except Exception as e:
        await send_text(
            context.bot,
            chat_id,
            f"❌ Failed to save media: {e}"
        )
        return

    # --- Confirmation messages ---
    if media_group_id:
        # Count album items
        context.chat_data["album_counts"].setdefault(media_group_id, 0)
        context.chat_data["album_counts"][media_group_id] += 1

        # Send confirmation ONLY once (on captioned message)
        if message.caption:
            await send_text(
                context.bot,
                chat_id,
                f"✅ Bulk upload started for {model_name}"
            )
    else:
        # Single upload confirmation
        await send_text(
            context.bot,
            chat_id,
            f"✅ Media saved successfully under {model_name}"
        )
