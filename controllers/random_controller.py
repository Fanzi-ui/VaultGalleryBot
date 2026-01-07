import config
from views.message_view import send_text, send_media
from services.random_service import get_random_media
from services.model_service import resolve_model_name, find_model_matches


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

    raw_input = " ".join(context.args) if context.args else None
    model_name = resolve_model_name(raw_input)

    if raw_input and not model_name:
        matches = find_model_matches(raw_input)
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
            f"❌ Model not found: {raw_input}"
        )
        return

    media = get_random_media(model_name)

    if not media:
        await send_text(
            context.bot,
            chat_id,
            "❌ No media found."
        )
        return

    await send_media(
        context.bot,
        chat_id,
        media["file_path"],
        media["media_type"]
    )
