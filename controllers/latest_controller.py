import config
from views.message_view import send_text, send_media
from services.latest_service import get_latest_media
from services.model_service import resolve_model_name, find_model_matches


async def latest_command(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if user_id not in config.AUTHORIZED_USERS:
        await send_text(
            context.bot,
            chat_id,
            "❌ You are not authorized to use this command."
        )
        return

    raw_args = context.args or []
    count = 1
    model_input = None

    if raw_args:
        if raw_args[-1].isdigit():
            count = max(1, int(raw_args[-1]))
            model_input = " ".join(raw_args[:-1]).strip() or None
        else:
            model_input = " ".join(raw_args).strip()

    if count > 5:
        await send_text(
            context.bot,
            chat_id,
            "⚠️ Max count is 5."
        )
        count = 5

    model_name = resolve_model_name(model_input)
    if model_input and not model_name:
        matches = find_model_matches(model_input)
        if len(matches) > 1:
            await send_text(
                context.bot,
                chat_id,
                "❌ Multiple matches: " + ", ".join(matches[:8])
            )
            return

        await send_text(
            context.bot,
            chat_id,
            f"❌ Model not found: {model_input}"
        )
        return

    media_items = get_latest_media(model_name, count)
    if not media_items:
        await send_text(
            context.bot,
            chat_id,
            "❌ No media found."
        )
        return

    for media in media_items:
        await send_media(
            context.bot,
            chat_id,
            media["file_path"],
            media["media_type"]
        )
